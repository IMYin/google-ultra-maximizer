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
from gflow_cli.profile_lease import ProfileLease

COOKIE_CACHE_PATH = Path.home() / ".config" / "fleet-hub" / "gflow_cookies.json"
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)


def _save_cookies(pairs: list[list[str]]) -> None:
    COOKIE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = COOKIE_CACHE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"pairs": pairs, "saved_at": time.time()}), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(COOKIE_CACHE_PATH)
    os.chmod(COOKIE_CACHE_PATH, 0o600)


def _load_cookies() -> list[list[str]]:
    if not COOKIE_CACHE_PATH.exists():
        return []
    try:
        data = json.loads(COOKIE_CACHE_PATH.read_text(encoding="utf-8"))
        pairs = data.get("pairs") or []
        return [p for p in pairs if isinstance(p, list) and len(p) == 2]
    except (OSError, json.JSONDecodeError):
        return []


async def _extract_cookies_headless(profile_dir: Path) -> list[list[str]]:
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
        _save_cookies(pairs)
    return pairs


async def _query_nzlxg(profile_dir: Path, pairs: list[list[str]]) -> CreditsInfo:
    """Query flow.google.com nzlxg RPC over pure HTTPS using cached cookies & system proxy."""
    ua = flow_wire.user_agent(profile_dir) or DEFAULT_UA
    headers = {
        "user-agent": ua,
        "accept-language": "en-US,en;q=0.9",
        "cookie": "; ".join(f"{k}={v}" for k, v in pairs),
    }
    flow_wire.forget_tokens(profile_dir)
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


async def main() -> int:
    settings = get_settings()
    pname = profile_store.resolve_profile(None)
    profile_dir = settings.profile_subdir(pname)
    if not profile_dir.exists():
        print(json.dumps({"status": "needs_login", "reason": "profile_missing"}))
        return 0

    email = profile_store.read_account_file(profile_dir) or ""
    pairs = _load_cookies()

    if not pairs:
        pairs = await _extract_cookies_headless(profile_dir)

    if not pairs:
        print(json.dumps({"status": "needs_login", "reason": "empty_cookies"}))
        return 0

    try:
        info = await _query_nzlxg(profile_dir, pairs)
        print(
            json.dumps(
                {
                    "status": "ok",
                    "authenticated": True,
                    "email": email,
                    "credits": info.credits,
                    "source": "httpx_wire_cached",
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception:
        # Refresh cookies headlessly once; if still signed out, run headless renew_profile
        try:
            pairs = await _extract_cookies_headless(profile_dir)
            if pairs:
                info = await _query_nzlxg(profile_dir, pairs)
                print(
                    json.dumps(
                        {
                            "status": "ok",
                            "authenticated": True,
                            "email": email,
                            "credits": info.credits,
                            "source": "httpx_wire_refreshed",
                        },
                        ensure_ascii=False,
                    )
                )
                return 0
        except Exception:
            pass

        try:
            res = await renew_profile(profile_dir, source="fleet_probe")
            if getattr(res, "renewed", False):
                pairs = await _extract_cookies_headless(profile_dir)
                if pairs:
                    info = await _query_nzlxg(profile_dir, pairs)
                    print(
                        json.dumps(
                            {
                                "status": "ok",
                                "authenticated": True,
                                "email": email,
                                "credits": info.credits,
                                "source": "httpx_wire_renewed",
                            },
                            ensure_ascii=False,
                        )
                    )
                    return 0
        except Exception:
            pass

        COOKIE_CACHE_PATH.unlink(missing_ok=True)
        print(json.dumps({"status": "needs_login", "reason": "session_expired"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
