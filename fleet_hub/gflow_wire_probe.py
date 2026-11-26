#!/usr/bin/env python3
"""Silent pure-HTTPS Google Flow credit balance probe (0 visible browser windows)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from http.cookiejar import CookieJar, DefaultCookiePolicy
from pathlib import Path
from typing import Any

try:
    import httpx
    from gflow_cli import profile_store
    from gflow_cli.api import flow_wire
    from gflow_cli.api.dto import CreditsInfo
    from gflow_cli.api.transports.batchexecute import parse_frames
    from gflow_cli.auth.cookies import sent_to_flow_host
    from gflow_cli.auth.renew import renew_profile
    from gflow_cli.browser_manager import (
        browser_proxy_kwargs,
        channel_for_profile,
        disable_features_args,
    )
    from gflow_cli.config import BrowserEngine, get_settings
    from gflow_cli.errors import ProfileLockedError
    from gflow_cli.profile_lease import ProfileLease

    _GFLOW_IMPORT_ERROR: Exception | None = None
except ImportError as exc:
    _GFLOW_IMPORT_ERROR = exc
    httpx = None  # type: ignore[assignment]
    profile_store = None  # type: ignore[assignment]
    flow_wire = None  # type: ignore[assignment]
    CreditsInfo = Any  # type: ignore[assignment,misc]

    class ProfileLockedError(Exception):
        pass

COOKIE_CACHE_PATH = Path.home() / ".config" / "fleet-hub" / "gflow_cookies.json"
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def _read_cookie_store() -> dict[str, Any]:
    if not COOKIE_CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(COOKIE_CACHE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_cookie_store(profiles: dict[str, Any]) -> None:
    if not profiles:
        COOKIE_CACHE_PATH.unlink(missing_ok=True)
        return
    COOKIE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = COOKIE_CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"profiles": profiles}, ensure_ascii=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(COOKIE_CACHE_PATH)
    os.chmod(COOKIE_CACHE_PATH, 0o600)


def _save_cookies(profile_name: str, pairs: list[list[str]]) -> None:
    raw = _read_cookie_store()
    profiles = dict(raw.get("profiles")) if isinstance(raw.get("profiles"), dict) else {}
    profiles[profile_name] = {"pairs": pairs, "saved_at": time.time()}
    _write_cookie_store(profiles)


def _load_cookies(profile_name: str) -> list[list[str]]:
    raw = _read_cookie_store()
    profiles = raw.get("profiles")
    pairs: Any = None
    if isinstance(profiles, dict):
        entry = profiles.get(profile_name)
        if isinstance(entry, dict):
            pairs = entry.get("pairs")
    elif profile_name == "default":
        pairs = raw.get("pairs")
    if not isinstance(pairs, list):
        return []
    return [p for p in pairs if isinstance(p, list) and len(p) == 2]


def _clear_cookies(profile_name: str) -> None:
    raw = _read_cookie_store()
    profiles = dict(raw.get("profiles")) if isinstance(raw.get("profiles"), dict) else {}
    if profile_name in profiles:
        profiles.pop(profile_name, None)
        _write_cookie_store(profiles)
    elif "pairs" in raw and profile_name == "default":
        COOKIE_CACHE_PATH.unlink(missing_ok=True)


async def _extract_cookies_headless(profile_dir: Path, profile_name: str = "default") -> list[list[str]]:
    """Extract flow.google.com cookies via strictly headless Chrome (--password-store=basic)."""
    from playwright.async_api import async_playwright

    channel = channel_for_profile(profile_dir)
    now_epoch = time.time()
    async with ProfileLease(profile_dir), async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel=channel,
            headless=True,
            args=["--password-store=basic", *disable_features_args(BrowserEngine.PLAYWRIGHT)],
            **browser_proxy_kwargs(get_settings().browser_proxy),
        )
        try:
            all_cookies = await ctx.cookies()
        finally:
            await ctx.close()

    pairs: list[list[str]] = []
    for c in all_cookies:
        domain = str(c.get("domain", ""))
        path = str(c.get("path", "/"))
        expires = float(c.get("expires", -1) or -1)
        if not sent_to_flow_host(domain):
            continue
        if path != "/":
            continue
        if expires > 0 and expires < now_epoch:
            continue
        name = str(c.get("name", ""))
        val = str(c.get("value", ""))
        if name:
            pairs.append([name, val])
    if pairs:
        _save_cookies(profile_name, pairs)
    return pairs


async def _query_nzlxg(profile_dir: Path, pairs: list[list[str]]) -> CreditsInfo:
    """Query flow.google.com nzlxg RPC over pure HTTPS using cached cookies & system proxy."""
    ua = flow_wire.user_agent(profile_dir) or DEFAULT_UA
    headers = {
        "user-agent": ua,
        "accept-language": "en-US,en;q=0.9",
        "cookie": "; ".join(f"{k}={v}" for k, v in pairs),
    }
    # Clear any prior _signed_out latch so cookie refresh/renew attempts actually hit the wire.
    flow_wire.reset_state()
    if hasattr(flow_wire, "session_recovered"):
        flow_wire.session_recovered(profile_dir)
    async with (
        asyncio.timeout(12.0),
        httpx.AsyncClient(
            follow_redirects=False,
            trust_env=True,  # Honor http_proxy / https_proxy / all_proxy
            timeout=httpx.Timeout(10.0, connect=4.0),
            cookies=CookieJar(policy=DefaultCookiePolicy(allowed_domains=[])),
        ) as client,
    ):
        tokens = await flow_wire.shell_tokens(client, profile_dir, headers)
        resp = await client.send(flow_wire.build_rpc_request("nzlxg", tokens, headers))
        if resp.status_code in (401, 403):
            raise flow_wire.WireReadUnavailable(flow_wire.WireFallbackReason.HTTP_401)
        frames = [payload for rpcid, payload in parse_frames(resp.text) if rpcid == "nzlxg"]
        if not frames:
            raise flow_wire.WireReadUnavailable(flow_wire.WireFallbackReason.UNPARSEABLE)
        return CreditsInfo.from_nzlxg(frames[0])


def select_candidate_profiles(explicit_profile: str | None = None, store: Any = None) -> list[Any]:
    """Order existing gflow profiles safely without crashing when default_profile is unset."""
    ps = store or profile_store
    if ps is None:
        return []
    all_profiles = [p for p in ps.list_profiles() if p.profile_dir.exists()]
    preferred = explicit_profile or os.environ.get("GFLOW_CLI_PROFILE") or ps.get_default_profile()

    if not all_profiles:
        try:
            pname = ps.resolve_profile(explicit_profile)
        except (ps.NoDefaultProfileError, ps.NoProfilesError):
            return []
        all_profiles = [p for p in ps.list_profiles() if p.name == pname and p.profile_dir.exists()]
        if not all_profiles:
            return []

    def _sort_key(p: Any) -> tuple[int, int, int, int, float, str]:
        last_used = getattr(p, "last_used_at", None)
        ts = last_used.timestamp() if last_used else 0.0
        return (
            0 if (preferred and p.name == preferred) else 1,
            0 if getattr(p, "is_default", False) else 1,
            0 if p.name == "default" else 1,
            0 if getattr(p, "cookies_present", False) else 1,
            -ts,
            str(p.name),
        )

    all_profiles.sort(key=_sort_key)
    return all_profiles


async def _probe_profile(meta: Any) -> dict[str, Any]:
    """Probe one gflow profile with cached wire -> headless cookie refresh -> headless renew."""
    email = getattr(meta, "google_account", None) or profile_store.read_account_file(meta.profile_dir) or ""

    # 1. Pure-HTTPS read using cached cookies (zero browser launch, zero profile lock)
    pairs = _load_cookies(meta.name)
    if pairs:
        try:
            info = await _query_nzlxg(meta.profile_dir, pairs)
            return {
                "status": "ok",
                "authenticated": True,
                "profile": meta.name,
                "email": email,
                "credits": info.credits,
                "source": "httpx_wire_cached",
            }
        except Exception:
            pass

    # 2. Headless cookie extraction + pure-HTTPS wire read
    try:
        pairs = await _extract_cookies_headless(meta.profile_dir, profile_name=meta.name)
    except ProfileLockedError:
        return {"status": "busy", "profile": meta.name, "reason": "profile_locked"}
    except Exception:
        pairs = []

    if pairs:
        try:
            info = await _query_nzlxg(meta.profile_dir, pairs)
            return {
                "status": "ok",
                "authenticated": True,
                "profile": meta.name,
                "email": email,
                "credits": info.credits,
                "source": "httpx_wire_refreshed",
            }
        except Exception:
            pass

    # 3. Headless session renewal (also accept migrated flow.google.com accounts where labs returns 410)
    res = None
    try:
        res = await renew_profile(meta.profile_dir, source="fleet_probe")
    except ProfileLockedError:
        return {"status": "busy", "profile": meta.name, "reason": "profile_locked"}
    except Exception:
        res = None

    if res is not None and (getattr(res, "renewed", False) or getattr(res, "result", "") == "labs_unverified"):
        try:
            pairs = await _extract_cookies_headless(meta.profile_dir, profile_name=meta.name)
        except ProfileLockedError:
            return {"status": "busy", "profile": meta.name, "reason": "profile_locked"}
        except Exception:
            pairs = []
        if pairs:
            try:
                info = await _query_nzlxg(meta.profile_dir, pairs)
                return {
                    "status": "ok",
                    "authenticated": True,
                    "profile": meta.name,
                    "email": email,
                    "credits": info.credits,
                    "source": "httpx_wire_renewed",
                }
            except Exception:
                pass

    _clear_cookies(meta.name)
    return {"status": "needs_login", "profile": meta.name, "reason": "session_expired"}


async def main() -> int:
    if _GFLOW_IMPORT_ERROR is not None:
        print(json.dumps({"status": "error", "reason": f"gflow_cli_unavailable: {_GFLOW_IMPORT_ERROR}"}))
        return 0

    candidates = select_candidate_profiles()
    if not candidates:
        print(json.dumps({"status": "needs_login", "reason": "profile_missing"}))
        return 0

    saw_busy = False
    for meta in candidates:
        res = await _probe_profile(meta)
        if res.get("status") == "ok":
            print(json.dumps(res, ensure_ascii=False))
            return 0
        if res.get("status") == "busy":
            saw_busy = True

    if saw_busy:
        print(json.dumps({"status": "busy", "reason": "profile_locked"}))
        return 0

    print(json.dumps({"status": "needs_login", "reason": "session_expired"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
