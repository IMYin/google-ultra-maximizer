"""Real-time Antigravity 2.0 quota probe via local Language Server RPC (daemon-safe)."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import mask_email, resolve_tool_bin, wrap_cmd
from .db import FleetDB, now_iso

NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
RPC_PATH = "/exa.language_server_pb.LanguageServerService/GetUserStatus"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def discover_daemon_endpoints() -> list[tuple[str, str, str]]:
    """Discover live local Antigravity Language Server endpoints (url, csrf, version)."""
    endpoints: list[tuple[str, str, str]] = []
    daemon_dirs = [
        Path.home() / ".gemini" / "antigravity" / "daemon",
        Path.home() / ".gemini" / "antigravity-cli" / "daemon",
    ]
    for ddir in daemon_dirs:
        if not ddir.is_dir():
            continue
        for fp in sorted(ddir.glob("hub_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                meta = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            pid = int(meta.get("pid") or 0)
            http_port = int(meta.get("httpPort") or 0)
            csrf = str(meta.get("csrfToken") or "").strip()
            ver = str(meta.get("lsVersion") or "").strip()
            if http_port > 0 and csrf and _pid_alive(pid):
                endpoints.append((f"http://127.0.0.1:{http_port}", csrf, ver))

    env_addr = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "").strip()
    env_csrf = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "").strip()
    if env_addr and env_csrf:
        url = env_addr if env_addr.startswith("http") else f"http://{env_addr}"
        ver = os.environ.get("ANTIGRAVITY_LS_VERSION", "").strip()
        if all(existing[0] != url for existing in endpoints):
            endpoints.append((url, env_csrf, ver))

    return endpoints


def fetch_user_status_from_ls(base_url: str, csrf_token: str, timeout: float = 3.5) -> dict[str, Any] | None:
    """Query GetUserStatus over loopback without touching external proxy."""
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{RPC_PATH}",
        data=b'{"metadata":{"ideName":"antigravity","extensionName":"antigravity","locale":"en"}}',
        headers={
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
            "x-codeium-csrf-token": csrf_token,
            "x-antigravity-csrf-token": csrf_token,
        },
        method="POST",
    )
    try:
        with NO_PROXY_OPENER.open(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
        us = payload.get("userStatus")
        return us if isinstance(us, dict) else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _format_countdown(reset_iso: str) -> tuple[str, float | None]:
    if not reset_iso:
        return "未知重置时间", None
    try:
        target = datetime.fromisoformat(reset_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        hours = (target - now).total_seconds() / 3600.0
        if hours <= 0:
            return "即将刷新", 0.0
        if hours >= 24:
            days = int(hours // 24)
            rem_h = int(hours % 24)
            return f"{days}天 {rem_h}小时后重置", round(hours, 2)
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m 后重置", round(hours, 2)
    except ValueError:
        return reset_iso, None


def _is_claude_or_oss_bucket(label: str, hours_to_reset: float | None) -> bool:
    low = label.lower()
    if any(k in low for k in ("claude", "gpt", "oss")):
        return True
    if hours_to_reset is not None and hours_to_reset <= 8.0 and "gemini" not in low and "orchestrator" not in low:
        return True
    return False


def parse_user_status_snapshot(user_status: dict[str, Any], ls_version: str = "") -> dict[str, Any]:
    """Normalize raw GetUserStatus payload into two distinct Ultra buckets."""
    email = str(user_status.get("email") or "")
    tier_obj = user_status.get("userTier")
    tier_name = str(tier_obj.get("name") if isinstance(tier_obj, dict) else tier_obj or "")
    plan_info = (user_status.get("planStatus") or {}).get("planInfo") or {}
    plan_name = str(plan_info.get("planName") or "")

    configs = (user_status.get("cascadeModelConfigData") or {}).get("clientModelConfigs") or []
    gemini_models: list[dict[str, Any]] = []
    rolling_models: list[dict[str, Any]] = []

    for item in configs:
        label = str(item.get("label") or "").strip()
        qi = item.get("quotaInfo") or {}
        rem = qi.get("remainingFraction")
        if rem is None:
            continue
        pct = max(0.0, min(100.0, float(rem) * 100.0))
        reset_time = str(qi.get("resetTime") or "")
        reset_text, hours_left = _format_countdown(reset_time)
        rec = {
            "label": label,
            "remaining_pct": round(pct, 2),
            "reset_time": reset_time,
            "reset_text": reset_text,
            "hours_left": hours_left,
        }
        if _is_claude_or_oss_bucket(label, hours_left):
            rolling_models.append(rec)
        else:
            gemini_models.append(rec)

    def _summarize(models: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not models:
            return None
        min_pct = min(m["remaining_pct"] for m in models)
        rep = min(models, key=lambda m: (m["remaining_pct"], m["hours_left"] or 9999.0))
        # Unique short model family prefixes for compact display
        families: list[str] = []
        for m in models:
            base = m["label"].split("(", 1)[0].strip()
            if base and base not in families:
                families.append(base)
        return {
            "remaining_pct": round(min_pct, 1),
            "reset_time": rep["reset_time"],
            "reset_text": rep["reset_text"],
            "hours_left": rep["hours_left"],
            "is_rolling_5h": bool(rep["hours_left"] is not None and rep["hours_left"] <= 8.5),
            "families": families[:5],
            "model_count": len(models),
        }

    return {
        "email": email,
        "tier": tier_name,
        "plan_name": plan_name,
        "ls_version": ls_version,
        "fetched_at": now_iso(),
        "gemini_weekly": _summarize(gemini_models),
        "claude_rolling_5h": _summarize(rolling_models),
    }


def fetch_agy_lens_summary(timeout: float = 3.5) -> dict[str, Any] | None:
    """Optionally read today/7d API-equivalent cost from `agy-lens --json`."""
    cli = resolve_tool_bin("agy-lens")
    if cli is None:
        return None
    try:
        proc = subprocess.run(
            wrap_cmd([str(cli), "--json"]),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0 or "{" not in proc.stdout:
            return None
        data = json.loads(proc.stdout[proc.stdout.index("{") :])
        totals = (data.get("history") or {}).get("totals") or {}
        today = totals.get("today") or {}
        d7 = totals.get("d7") or {}
        return {
            "today_usd": float(today.get("est_cost_usd") or 0.0),
            "today_calls": int(today.get("calls") or 0),
            "d7_usd": float(d7.get("est_cost_usd") or 0.0),
            "d7_calls": int(d7.get("calls") or 0),
        }
    except (subprocess.SubprocessError, OSError, ValueError, json.JSONDecodeError):
        return None


def probe_antigravity_quotas(db: FleetDB, privacy: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return both Antigravity quota pool cards plus raw normalized telemetry."""
    snap: dict[str, Any] | None = None
    live_ok = False

    for base_url, csrf, ver in discover_daemon_endpoints():
        raw_us = fetch_user_status_from_ls(base_url, csrf)
        if raw_us:
            snap = parse_user_status_snapshot(raw_us, ls_version=ver)
            db.set_meta("telemetry_agy_quota_json", json.dumps(snap, ensure_ascii=False))
            live_ok = True
            break

    if snap is None:
        cached = db.get_meta("telemetry_agy_quota_json", "")
        if cached:
            try:
                snap = json.loads(cached)
            except json.JSONDecodeError:
                snap = None

    lens_stats = fetch_agy_lens_summary()
    if lens_stats is not None:
        db.set_meta("telemetry_agy_lens_json", json.dumps(lens_stats, ensure_ascii=False))
    else:
        cached_lens = db.get_meta("telemetry_agy_lens_json", "")
        if cached_lens:
            try:
                lens_stats = json.loads(cached_lens)
            except json.JSONDecodeError:
                lens_stats = None

    if snap is None:
        return (
            [
                {
                    "pool": "agy_gemini_weekly",
                    "title": "Antigravity · Gemini 4 / 3.8 周池",
                    "title_en": "Antigravity · Gemini 4 / 3.8 Weekly",
                    "badge": "⚪ 未检测到本地 Antigravity Daemon",
                    "badge_en": "⚪ Antigravity Daemon Not Detected",
                    "badge_tone": "muted",
                    "primary": "待启动 Antigravity",
                    "primary_en": "Waiting for Antigravity",
                    "detail": "打开 Antigravity 2.0 或 `agy` 后自动直连 LanguageServer 获取实时百分比",
                    "detail_en": "Open Antigravity 2.0 or `agy` to stream live LanguageServer quotas",
                    "pct": None,
                },
                {
                    "pool": "agy_claude_5h",
                    "title": "Antigravity · Claude 5.5 / GPT-OSS 5h 池",
                    "title_en": "Antigravity · Claude 5.5 / OSS 5h Rolling",
                    "badge": "⚪ 未检测到本地 Antigravity Daemon",
                    "badge_en": "⚪ Antigravity Daemon Not Detected",
                    "badge_tone": "muted",
                    "primary": "待启动 Antigravity",
                    "primary_en": "Waiting for Antigravity",
                    "detail": "5 小时滚动配额独立计算，不消耗 Gemini 4 周池额度",
                    "detail_en": "5h rolling quota resets independently without burning Gemini Weekly",
                    "pct": None,
                },
            ],
            {"live": False, "lens": lens_stats},
        )

    tier = snap.get("tier") or snap.get("plan_name") or "Antigravity"
    email_disp = mask_email(str(snap.get("email") or ""), privacy=privacy)
    ver_disp = f" v{snap['ls_version']}" if snap.get("ls_version") else ""
    source_badge = f"🟢 官方直连{ver_disp}" if live_ok else f"🟡 会话快照 ({snap.get('fetched_at', '')})"
    source_badge_en = f"🟢 Live LS RPC{ver_disp}" if live_ok else f"🟡 Snapshot ({snap.get('fetched_at', '')})"
    lens_tail = ""
    lens_tail_en = ""
    if lens_stats and lens_stats.get("d7_usd", 0) > 0:
        lens_tail = f" · 近7天约值 ${lens_stats['d7_usd']:.0f}"
        lens_tail_en = f" · 7d eqv ${lens_stats['d7_usd']:.0f}"

    cards: list[dict[str, Any]] = []
    gw = snap.get("gemini_weekly")
    gem_is_5h = False
    if isinstance(gw, dict):
        rem = float(gw["remaining_pct"])
        gem_is_5h = bool(
            gw.get("is_rolling_5h")
            or (isinstance(gw.get("hours_left"), (int, float)) and float(gw["hours_left"]) <= 8.5)
        )
        tone = "warn" if rem < 20.0 else "live"
        reset_en = f"{gw['hours_left']:.1f}h reset" if isinstance(gw.get("hours_left"), (int, float)) else str(gw.get("reset_text") or "")
        gw_title = f"Antigravity · Gemini 4 5h 滚动主池 ({tier})" if gem_is_5h else f"Antigravity · Gemini 4 周池 ({tier})"
        gw_title_en = f"Antigravity · Gemini 4 5h Rolling ({tier})" if gem_is_5h else f"Antigravity · Gemini 4 Weekly ({tier})"
        cards.append(
            {
                "pool": "agy_gemini_weekly",
                "title": gw_title,
                "title_en": gw_title_en,
                "badge": source_badge,
                "badge_en": source_badge_en,
                "badge_tone": tone,
                "primary": f"剩余 {rem:.1f}%",
                "primary_en": f"{rem:.1f}% left",
                "detail": f"{gw['reset_text']} · {', '.join(gw.get('families', [])[:3])}{lens_tail}"
                + (f" · {email_disp}" if email_disp else ""),
                "detail_en": f"{reset_en} · {', '.join(gw.get('families', [])[:3])}{lens_tail_en}"
                + (f" · {email_disp}" if email_disp else ""),
                "pct": rem,
                "meta": gw,
            }
        )

    c5 = snap.get("claude_rolling_5h")
    if isinstance(c5, dict):
        rem5 = float(c5["remaining_pct"])
        reset5_en = f"{c5['hours_left']:.1f}h reset" if isinstance(c5.get("hours_left"), (int, float)) else str(c5.get("reset_text") or "")
        c5_note_zh = "（独立第二 5h 滚动池，与 Gemini 互不占用）" if gem_is_5h else "（独立滚动，不占 Gemini 周池）"
        c5_note_en = "(independent 2nd 5h rolling pool)" if gem_is_5h else "(independent 5h clock)"
        cards.append(
            {
                "pool": "agy_claude_5h",
                "title": "Antigravity · Claude 5.5 / OSS 5h 滚动池",
                "title_en": "Antigravity · Claude 5.5 / OSS 5h Rolling",
                "badge": source_badge,
                "badge_en": source_badge_en,
                "badge_tone": "live" if rem5 >= 25.0 else "warn",
                "primary": f"剩余 {rem5:.1f}%",
                "primary_en": f"{rem5:.1f}% left",
                "detail": f"{c5['reset_text']} · {', '.join(c5.get('families', [])[:3])}{c5_note_zh}",
                "detail_en": f"{reset5_en} · {', '.join(c5.get('families', [])[:3])} {c5_note_en}",
                "pct": rem5,
                "meta": c5,
            }
        )

    return cards, {"live": live_ok, "snapshot": snap, "lens": lens_stats}
