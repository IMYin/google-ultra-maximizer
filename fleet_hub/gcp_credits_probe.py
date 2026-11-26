#!/usr/bin/env python3
"""Headless Google Cloud Billing Credits table probe (zero hardcoded account IDs)."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import platform
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MONEY_RE = re.compile(r"-?[\d,]+(?:\.\d+)?")
CN_DATE_RE = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})")


def _parse_money(text: str) -> float | None:
    cleaned = text.replace("\u00a0", " ").strip()
    m = MONEY_RE.search(cleaned)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _parse_date_iso(text: str) -> str:
    raw = text.strip()
    if not raw or raw in ("—", "-", "--"):
        return ""
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%Y/%m/%d", "%d %b %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m = CN_DATE_RE.search(raw)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return raw


def parse_gcp_credits_table(
    headers: list[str],
    rows: list[list[str]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Parse extracted GCP Console Credits table headers & rows into normalized grant balances."""
    norm_headers = [h.strip().lower() for h in headers]

    def _col(candidates: tuple[str, ...], default_idx: int) -> int:
        for i, h in enumerate(norm_headers):
            if any(c in h for c in candidates):
                return i
        return default_idx

    idx_name = _col(("credit name", "名称"), 0)
    idx_status = _col(("status", "状态"), 1)
    idx_rem = _col(("remaining value", "剩余价值", "剩余金额"), 3)
    idx_orig = _col(("original value", "原始价值", "原始金额"), 4)
    idx_start = _col(("start date", "开始日期"), 8)
    idx_end = _col(("end date", "结束日期", "到期"), 9)

    cur_date = (now or datetime.now(timezone.utc)).date()
    grants: list[dict[str, Any]] = []
    remaining_total = 0.0
    original_total = 0.0

    for row in rows:
        if len(row) <= max(idx_status, idx_rem, idx_orig):
            continue
        status = row[idx_status].strip()
        if status.lower() not in ("available", "active", "可用", "有效"):
            continue
        rem = _parse_money(row[idx_rem])
        orig = _parse_money(row[idx_orig])
        if rem is None or orig is None:
            continue

        name = row[idx_name].strip() if idx_name < len(row) else "Cloud Credit"
        start_iso = _parse_date_iso(row[idx_start]) if idx_start < len(row) else ""
        end_iso = _parse_date_iso(row[idx_end]) if idx_end < len(row) else ""
        days_left: int | None = None
        if re.match(r"^\d{4}-\d{2}-\d{2}$", end_iso):
            try:
                end_dt = datetime.strptime(end_iso, "%Y-%m-%d").date()
                days_left = (end_dt - cur_date).days
            except ValueError:
                days_left = None

        used = max(0.0, round(orig - rem, 4))
        remaining_total += rem
        original_total += orig
        grants.append(
            {
                "name": name,
                "status": status,
                "remaining": round(rem, 2),
                "original": round(orig, 2),
                "used": round(used, 2),
                "start_date": start_iso,
                "end_date": end_iso,
                "days_left": days_left,
            }
        )

    remaining_total = round(remaining_total, 2)
    original_total = round(original_total, 2)
    used_total = max(0.0, round(original_total - remaining_total, 2))

    # Find earliest-expiring grant that still has balance
    expiring = [g for g in grants if g["remaining"] > 0 and isinstance(g["days_left"], int)]
    earliest_grant = min(expiring, key=lambda g: g["days_left"]) if expiring else None

    return {
        "status": "ok",
        "currency_symbol": "$",
        "remaining_total": remaining_total,
        "original_total": original_total,
        "used_total": used_total,
        "active_grants_count": len(grants),
        "earliest_grant": earliest_grant,
        "grants": sorted(grants, key=lambda g: (g["end_date"] or "9999-12-31", g["remaining"])),
        "fetched_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }


def _resolve_profile_dir() -> tuple[Path, str]:
    """Locate usable Chrome/Playwright Google session profile across macOS/Linux."""
    dedicated = Path.home() / ".config" / "ultra-maximizer" / "gcp-profile"
    if (dedicated / "Default").exists() or (dedicated / "Cookies").exists():
        return dedicated, "chromium"

    try:
        from gflow_cli import profile_store
        from gflow_cli.browser_manager import channel_for_profile
        from gflow_cli.config import get_settings

        settings = get_settings()
        pname = profile_store.resolve_profile(None)
        pdir = settings.profile_subdir(pname)
        if pdir.exists():
            return pdir, channel_for_profile(pdir)
    except Exception:
        pass

    sys_name = platform.system()
    candidates = (
        [Path.home() / "Library" / "Application Support" / "gflow-cli" / "profile_default"]
        if sys_name == "Darwin"
        else [
            Path.home() / ".config" / "gflow-cli" / "profile_default",
            Path.home() / ".local" / "share" / "gflow-cli" / "profile_default",
        ]
    )
    for cand in candidates:
        if cand.exists():
            return cand, ("chrome" if sys_name == "Darwin" else "chromium")

    return dedicated, ("chrome" if sys_name == "Darwin" else "chromium")


@contextlib.contextmanager
def _optional_lease(profile_dir: Path):
    try:
        from gflow_cli.profile_lease import ProfileLease

        with ProfileLease(profile_dir):
            yield
    except Exception:
        yield


def _proxy_kwargs() -> dict[str, Any]:
    proxy = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
        or ""
    ).strip()
    if proxy and (proxy.startswith("http://") or proxy.startswith("https://") or proxy.startswith("socks5://")):
        return {"proxy": {"server": proxy}}
    return {}


async def _run_probe(login_mode: bool = False) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    profile_dir, channel = _resolve_profile_dir()
    if login_mode:
        profile_dir = Path.home() / ".config" / "ultra-maximizer" / "gcp-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    account_id = os.environ.get("GCP_BILLING_ACCOUNT_ID", "").strip()
    target_url = (
        f"https://console.cloud.google.com/billing/{account_id}/credits?hl=en"
        if account_id
        else "https://console.cloud.google.com/billing/credits?hl=en"
    )

    launch_kwargs: dict[str, Any] = {
        "user_data_dir": str(profile_dir),
        "headless": not login_mode,
        "args": ["--password-store=basic", "--disable-blink-features=AutomationControlled"],
        **_proxy_kwargs(),
    }
    if channel and channel != "chromium":
        launch_kwargs["channel"] = channel

    with _optional_lease(profile_dir):
        async with async_playwright() as pw:
            try:
                ctx = await pw.chromium.launch_persistent_context(**launch_kwargs)
            except Exception:
                launch_kwargs.pop("channel", None)
                ctx = await pw.chromium.launch_persistent_context(**launch_kwargs)

            try:
                page = await ctx.new_page()
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

                deadline = time.monotonic() + (180.0 if login_mode else 14.0)
                headers: list[str] = []
                rows: list[list[str]] = []

                while time.monotonic() < deadline:
                    cur_url = page.url.lower()
                    if not login_mode and ("accounts.google.com" in cur_url or "signin" in cur_url):
                        return {
                            "status": "needs_login",
                            "reason": "Google Cloud Console sign-in required; run `ultra gcp-login` once.",
                        }

                    table_data = await page.evaluate(
                        """() => {
                            const headers = Array.from(document.querySelectorAll('th, [role="columnheader"]'))
                              .map(el => (el.innerText || '').trim());
                            const rows = Array.from(document.querySelectorAll('tbody tr, [role="row"]'))
                              .map(r => Array.from(r.querySelectorAll('td, [role="cell"], [role="gridcell"]'))
                                .map(c => (c.innerText || '').trim()))
                              .filter(r => r.length >= 4);
                            return { headers, rows };
                        }"""
                    )
                    headers = table_data.get("headers") or []
                    rows = table_data.get("rows") or []
                    if headers and any("$" in cell or "available" in cell.lower() for r in rows for cell in r):
                        break
                    await page.wait_for_timeout(500)

                if not rows:
                    return {
                        "status": "empty",
                        "reason": "No billing credit rows found (check billing permissions or run `ultra gcp-login`).",
                    }
                return parse_gcp_credits_table(headers, rows)
            finally:
                await ctx.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless GCP Billing Credits Probe")
    parser.add_argument("--login", action="store_true", help="Open headed browser once to authenticate GCP profile")
    args = parser.parse_args()
    try:
        res = asyncio.run(_run_probe(login_mode=args.login))
    except Exception as exc:
        res = {"status": "error", "reason": str(exc)[:300]}
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
