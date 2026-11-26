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
SUMMARY_RPC_PATH = "/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"
_LS_RPC_BODY = b'{"metadata":{"ideName":"antigravity","extensionName":"antigravity","locale":"en"}}'


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


def _ls_rpc_post(base_url: str, rpc_path: str, csrf_token: str, timeout: float = 3.5) -> dict[str, Any] | None:
    """POST to a local Language Server Connect-RPC method over loopback without external proxy."""
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{rpc_path}",
        data=_LS_RPC_BODY,
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
        return payload if isinstance(payload, dict) else None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def fetch_user_status_from_ls(base_url: str, csrf_token: str, timeout: float = 3.5) -> dict[str, Any] | None:
    """Query GetUserStatus over loopback without touching external proxy."""
    payload = _ls_rpc_post(base_url, RPC_PATH, csrf_token, timeout=timeout)
    if not isinstance(payload, dict):
        return None
    us = payload.get("userStatus")
    return us if isinstance(us, dict) else None


def fetch_quota_summary_from_ls(base_url: str, csrf_token: str, timeout: float = 3.5) -> dict[str, Any] | None:
    """Query RetrieveUserQuotaSummary over loopback for both 5h and weekly buckets."""
    return _ls_rpc_post(base_url, SUMMARY_RPC_PATH, csrf_token, timeout=timeout)


def _format_countdown_bilingual(
    reset_iso: str,
    window_kind: str = "",
    pct: float | None = None,
) -> tuple[str, str, float | None, bool]:
    if not reset_iso:
        if window_kind == "5h" and pct is not None and pct >= 99.9:
            return "待唤醒（首请求启动 5h 计时）", "Idle · 5h timer starts on use", None, True
        if window_kind == "weekly" and pct is not None and pct >= 99.9:
            return "7天滚动周期（满额）", "Full · 7d rolling window", None, True
        return "未知重置时间", "Unknown reset", None, False
    try:
        target = datetime.fromisoformat(reset_iso.replace("Z", "+00:00"))
        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours = (target - now).total_seconds() / 3600.0
        if hours <= 0:
            return "即将刷新", "Refreshing soon", 0.0, False
        if hours >= 24:
            days = int(hours // 24)
            rem_h = int(hours % 24)
            return f"{days}天 {rem_h}小时后重置", f"Resets in {days}d {rem_h}h", round(hours, 2), False
        h = int(hours)
        m = int((hours - h) * 60)
        return f"{h}h {m}m 后重置", f"Resets in {h}h {m}m", round(hours, 2), False
    except ValueError:
        return reset_iso, reset_iso, None, False


def _format_countdown(reset_iso: str) -> tuple[str, float | None]:
    zh_txt, _, hours, _ = _format_countdown_bilingual(reset_iso)
    return zh_txt, hours


def _is_claude_or_oss_bucket(label: str, hours_to_reset: float | None) -> bool:
    low = label.lower()
    if any(k in low for k in ("claude", "gpt", "oss")):
        return True
    if hours_to_reset is not None and hours_to_reset <= 8.0 and "gemini" not in low and "orchestrator" not in low:
        return True
    return False


def _extract_group_families(group_desc: str) -> list[str]:
    low = group_desc.lower()
    marker = "models within this group:"
    if marker not in low:
        return []
    raw_list = group_desc[low.index(marker) + len(marker) :]
    families: list[str] = []
    for part in raw_list.split(","):
        base = part.split("(", 1)[0].strip()
        if base and base not in families:
            families.append(base)
    return families[:5]


def parse_quota_summary_payload(summary_resp: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Parse RetrieveUserQuotaSummary into per-category 5h & weekly rolling windows."""
    if not isinstance(summary_resp, dict):
        return {}
    root = summary_resp.get("response") if isinstance(summary_resp.get("response"), dict) else summary_resp
    container = root.get("quotaSummary") or root.get("quota_summary") or root
    if not isinstance(container, dict):
        return {}

    bucket_entries: list[tuple[Any, str, str, str]] = []
    groups = container.get("groups") or container.get("quotaGroups") or container.get("quota_groups") or []
    if isinstance(groups, list):
        for g in groups:
            if not isinstance(g, dict):
                continue
            g_name = str(g.get("displayName") or g.get("display_name") or g.get("name") or "")
            g_id = str(g.get("groupId") or g.get("group_id") or g.get("id") or "")
            g_desc = str(g.get("description") or "")
            bs = g.get("buckets") or g.get("quotaBuckets") or g.get("quota_buckets") or []
            if isinstance(bs, list):
                for b in bs:
                    bucket_entries.append((b, g_name, g_id, g_desc))
    top_buckets = container.get("buckets") or container.get("quotaBuckets") or container.get("quota_buckets") or []
    if isinstance(top_buckets, list):
        for b in top_buckets:
            bucket_entries.append((b, "", "", ""))

    out: dict[str, dict[str, Any]] = {}
    for b, g_name, g_id, g_desc in bucket_entries:
        if not isinstance(b, dict):
            continue
        bucket_id = str(b.get("bucketId") or b.get("bucket_id") or b.get("id") or "")
        display_name = str(b.get("displayName") or b.get("display_name") or b.get("label") or b.get("name") or "")
        window_val = str(b.get("window") or b.get("windowType") or b.get("window_type") or "")
        q = b.get("quotaInfo") or b.get("quota_info") or b.get("quota") or b
        if not isinstance(q, dict):
            continue
        reset_time = str(q.get("resetTime") or q.get("reset_time") or q.get("resetAt") or "")
        rem = q.get("remainingFraction")
        if rem is None:
            rem = q.get("remaining_fraction")
        if rem is None:
            rem = q.get("fractionRemaining")
        if rem is None and reset_time:
            rem = 0.0
        if rem is None and not reset_time:
            continue
        try:
            pct = round(max(0.0, min(100.0, float(rem) * 100.0)), 1)
        except (TypeError, ValueError):
            continue

        cat_text = f"{bucket_id} {g_name} {g_id} {g_desc}".lower()
        if "gemini" in cat_text or "google" in cat_text:
            category = "gemini"
        elif any(tok in cat_text for tok in ("3p", "claude", "gpt", "oss", "third", "anthropic", "openai", "opus", "sonnet")):
            category = "claude"
        else:
            continue

        win_text = f"{window_val} {bucket_id} {display_name}".lower()
        if any(tok in win_text for tok in ("weekly", "7d", "7-day", "7_day")):
            kind = "weekly"
        elif any(tok in win_text for tok in ("5h", "5-hour", "5_hour", "five")):
            kind = "5h"
        else:
            _, hours_guess = _format_countdown(reset_time)
            if hours_guess is not None and hours_guess <= 8.5:
                kind = "5h"
            elif hours_guess is not None and hours_guess > 24.0:
                kind = "weekly"
            else:
                continue

        zh_txt, en_txt, hours_left, idle_unstarted = _format_countdown_bilingual(reset_time, window_kind=kind, pct=pct)
        win_rec = {
            "kind": kind,
            "label": "5h 滚动额度" if kind == "5h" else "1周滚动额度",
            "label_en": "5h Rolling" if kind == "5h" else "7d Weekly",
            "remaining_pct": pct,
            "reset_time": reset_time,
            "reset_text": zh_txt,
            "reset_text_en": en_txt,
            "hours_left": hours_left,
            "idle_unstarted": idle_unstarted,
        }

        cat_bucket = out.setdefault(category, {"windows": {}, "families": []})
        prev_win = cat_bucket["windows"].get(kind)
        if prev_win is None or (
            win_rec["remaining_pct"],
            win_rec["hours_left"] if win_rec["hours_left"] is not None else 9999.0,
        ) < (
            prev_win["remaining_pct"],
            prev_win["hours_left"] if prev_win["hours_left"] is not None else 9999.0,
        ):
            cat_bucket["windows"][kind] = win_rec
        if not cat_bucket["families"] and g_desc:
            cat_bucket["families"] = _extract_group_families(g_desc)

    return out


def _window_from_pool_summary(us_sum: dict[str, Any], kind: str) -> dict[str, Any]:
    pct = round(float(us_sum["remaining_pct"]), 1)
    reset_time = str(us_sum.get("reset_time") or "")
    zh_txt, en_txt, hours_left, idle_unstarted = _format_countdown_bilingual(reset_time, window_kind=kind, pct=pct)
    return {
        "kind": kind,
        "label": "5h 滚动额度" if kind == "5h" else "1周滚动额度",
        "label_en": "5h Rolling" if kind == "5h" else "7d Weekly",
        "remaining_pct": pct,
        "reset_time": reset_time,
        "reset_text": str(us_sum.get("reset_text") or zh_txt),
        "reset_text_en": en_txt,
        "hours_left": us_sum.get("hours_left") if us_sum.get("hours_left") is not None else hours_left,
        "idle_unstarted": idle_unstarted,
    }


def _merge_pool_summary(
    us_sum: dict[str, Any] | None,
    sum_cat: dict[str, Any] | None,
    default_us_kind: str,
) -> dict[str, Any] | None:
    sum_windows = (sum_cat or {}).get("windows") or {}
    w5 = sum_windows.get("5h")
    wwk = sum_windows.get("weekly")

    if sum_windows:
        if us_sum:
            if w5 is None and (us_sum.get("is_rolling_5h") or default_us_kind == "5h"):
                w5 = _window_from_pool_summary(us_sum, "5h")
            if wwk is None and not us_sum.get("is_rolling_5h") and default_us_kind == "weekly":
                wwk = _window_from_pool_summary(us_sum, "weekly")
        families = list((us_sum or {}).get("families") or (sum_cat or {}).get("families") or [])[:5]
        model_count = int((us_sum or {}).get("model_count") or len(families))
        if w5 and wwk:
            eff_pct = round(min(float(w5["remaining_pct"]), float(wwk["remaining_pct"])), 1)
            rep = w5 if float(w5["remaining_pct"]) <= float(wwk["remaining_pct"]) else wwk
            return {
                "remaining_pct": eff_pct,
                "reset_time": rep["reset_time"],
                "reset_text": rep["reset_text"],
                "hours_left": rep["hours_left"],
                "is_rolling_5h": True,
                "has_weekly": True,
                "window_5h": w5,
                "window_weekly": wwk,
                "families": families,
                "model_count": model_count,
            }
        only = w5 or wwk
        assert only is not None
        out: dict[str, Any] = {
            "remaining_pct": only["remaining_pct"],
            "reset_time": only["reset_time"],
            "reset_text": only["reset_text"],
            "hours_left": only["hours_left"],
            "is_rolling_5h": only["kind"] == "5h",
            "has_weekly": only["kind"] == "weekly",
            "families": families,
            "model_count": model_count,
        }
        if w5:
            out["window_5h"] = w5
        if wwk:
            out["window_weekly"] = wwk
        return out

    if us_sum is None:
        return None
    out = dict(us_sum)
    us_is_5h = bool(out.get("is_rolling_5h"))
    win_kind = "5h" if (us_is_5h or default_us_kind == "5h") else "weekly"
    out["has_weekly"] = win_kind == "weekly"
    out["window_5h" if win_kind == "5h" else "window_weekly"] = _window_from_pool_summary(out, win_kind)
    return out


def parse_user_status_snapshot(
    user_status: dict[str, Any],
    ls_version: str = "",
    quota_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize raw GetUserStatus + RetrieveUserQuotaSummary payloads into Gemini & Claude buckets."""
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
        reset_time = str(qi.get("resetTime") or "")
        rem = qi.get("remainingFraction")
        if rem is None and reset_time:
            rem = 0.0
        if rem is None:
            continue
        pct = max(0.0, min(100.0, float(rem) * 100.0))
        leaving = str(item.get("tagTitle") or "").strip().lower() == "leaving soon"
        reset_text, _, hours_left, _ = _format_countdown_bilingual(reset_time, pct=round(pct, 1))
        rec = {
            "label": label,
            "remaining_pct": round(pct, 2),
            "reset_time": reset_time,
            "reset_text": reset_text,
            "hours_left": hours_left,
            "leaving": leaving,
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
        # Unique short model family prefixes for compact display, keeping active models first
        ordered_models = [m for m in models if not m.get("leaving")] + [m for m in models if m.get("leaving")]
        families: list[str] = []
        for m in ordered_models:
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

    summary_parsed = parse_quota_summary_payload(quota_summary)
    gemini_merged = _merge_pool_summary(_summarize(gemini_models), summary_parsed.get("gemini"), "weekly")
    claude_merged = _merge_pool_summary(_summarize(rolling_models), summary_parsed.get("claude"), "5h")

    return {
        "email": email,
        "tier": tier_name,
        "plan_name": plan_name,
        "ls_version": ls_version,
        "fetched_at": now_iso(),
        "gemini_weekly": gemini_merged,
        "claude_rolling_5h": claude_merged,
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


def _build_card_windows(pool_snap: dict[str, Any]) -> list[dict[str, Any]]:
    w5 = pool_snap.get("window_5h")
    wwk = pool_snap.get("window_weekly")
    if not (isinstance(w5, dict) and isinstance(wwk, dict)):
        return []
    out: list[dict[str, Any]] = []
    for kind, w in (("5h", w5), ("weekly", wwk)):
        pct = round(float(w.get("remaining_pct") or 0.0), 1)
        reset_zh = str(w.get("reset_text") or "")
        reset_en = str(w.get("reset_text_en") or reset_zh)
        out.append(
            {
                "kind": kind,
                "label": str(w.get("label") or ("5h 滚动额度" if kind == "5h" else "1周滚动额度")),
                "label_en": str(w.get("label_en") or ("5h Rolling" if kind == "5h" else "7d Weekly")),
                "pct": pct,
                "reset": reset_zh,
                "reset_en": reset_en,
                "hours_left": w.get("hours_left"),
                "idle_unstarted": bool(w.get("idle_unstarted")),
            }
        )
    return out


def probe_antigravity_quotas(db: FleetDB, privacy: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return both Antigravity quota pool cards plus raw normalized telemetry."""
    snap: dict[str, Any] | None = None
    live_ok = False

    for base_url, csrf, ver in discover_daemon_endpoints():
        raw_us = fetch_user_status_from_ls(base_url, csrf)
        raw_sum = fetch_quota_summary_from_ls(base_url, csrf)
        if raw_us or raw_sum:
            snap = parse_user_status_snapshot(raw_us or {}, ls_version=ver, quota_summary=raw_sum)
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
                    "title": "Antigravity · Gemini 4 双周期池（5h + 1周）",
                    "title_en": "Antigravity · Gemini 4 (5h + 7d Weekly)",
                    "badge": "⚪ 未检测到本地 Antigravity Daemon",
                    "badge_en": "⚪ Antigravity Daemon Not Detected",
                    "badge_tone": "muted",
                    "primary": "待启动 Antigravity",
                    "primary_en": "Waiting for Antigravity",
                    "detail": "打开 Antigravity 2.0 或 `agy` 后自动直连 LanguageServer 获取 5h + 1周滚动双限额",
                    "detail_en": "Open Antigravity 2.0 or `agy` to stream live 5h + 7d weekly quotas",
                    "pct": None,
                },
                {
                    "pool": "agy_claude_5h",
                    "title": "Antigravity · Claude 5.5 / GPT-OSS 双周期池（5h + 1周）",
                    "title_en": "Antigravity · Claude 5.5 / OSS (5h + 7d Weekly)",
                    "badge": "⚪ 未检测到本地 Antigravity Daemon",
                    "badge_en": "⚪ Antigravity Daemon Not Detected",
                    "badge_tone": "muted",
                    "primary": "待启动 Antigravity",
                    "primary_en": "Waiting for Antigravity",
                    "detail": "5h + 1周滚动配额独立计算，不消耗 Gemini 配额",
                    "detail_en": "Independent 5h + 7d rolling quotas without burning Gemini",
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
        gw_windows = _build_card_windows(gw)
        fams_txt = ", ".join(gw.get("families", [])[:3])
        if gw_windows:
            w5 = gw["window_5h"]
            wwk = gw["window_weekly"]
            rem5 = float(w5["remaining_pct"])
            remw = float(wwk["remaining_pct"])
            eff_rem = min(rem5, remw)
            gem_is_5h = True
            kicker_base_zh = f"{fams_txt}{lens_tail}" if fams_txt else lens_tail.lstrip(" ·")
            kicker_base_en = f"{fams_txt}{lens_tail_en}" if fams_txt else lens_tail_en.lstrip(" ·")
            kicker_zh = " · ".join(p for p in (kicker_base_zh, email_disp) if p)
            kicker_en = " · ".join(p for p in (kicker_base_en, email_disp) if p)
            detail_zh = f"5h: {w5['reset_text']} · 周: {wwk['reset_text']}" + (f" · {kicker_zh}" if kicker_zh else "")
            detail_en = f"5h: {w5['reset_text_en']} · Wk: {wwk['reset_text_en']}" + (f" · {kicker_en}" if kicker_en else "")
            cards.append(
                {
                    "pool": "agy_gemini_weekly",
                    "title": f"Antigravity · Gemini 4 双周期池 ({tier})",
                    "title_en": f"Antigravity · Gemini 4 5h + Weekly ({tier})",
                    "badge": source_badge,
                    "badge_en": source_badge_en,
                    "badge_tone": "warn" if eff_rem < 20.0 else ("live" if live_ok else "stale"),
                    "primary": f"5h {rem5:.1f}% · 周 {remw:.1f}%",
                    "primary_en": f"5h {rem5:.1f}% · Wk {remw:.1f}%",
                    "detail": detail_zh,
                    "detail_en": detail_en,
                    "kicker": kicker_zh,
                    "kicker_en": kicker_en,
                    "pct": eff_rem,
                    "pct_5h": rem5,
                    "pct_weekly": remw,
                    "windows": gw_windows,
                    "meta": gw,
                }
            )
        else:
            rem = float(gw["remaining_pct"])
            gem_is_5h = bool(
                gw.get("is_rolling_5h")
                or (isinstance(gw.get("hours_left"), (int, float)) and float(gw["hours_left"]) <= 8.5)
            )
            tone = "warn" if rem < 20.0 else ("live" if live_ok else "stale")
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
                    "detail": f"{gw['reset_text']} · {fams_txt}{lens_tail}"
                    + (f" · {email_disp}" if email_disp else ""),
                    "detail_en": f"{reset_en} · {fams_txt}{lens_tail_en}"
                    + (f" · {email_disp}" if email_disp else ""),
                    "pct": rem,
                    "meta": gw,
                }
            )

    c5 = snap.get("claude_rolling_5h")
    if isinstance(c5, dict):
        c5_windows = _build_card_windows(c5)
        fams5_txt = ", ".join(c5.get("families", [])[:3])
        if c5_windows:
            w5 = c5["window_5h"]
            wwk = c5["window_weekly"]
            rem5 = float(w5["remaining_pct"])
            remw = float(wwk["remaining_pct"])
            eff_rem = min(rem5, remw)
            kicker_zh = " · ".join(p for p in (fams5_txt, "独立 5h + 1周滚动双池，与 Gemini 互不占用") if p)
            kicker_en = " · ".join(p for p in (fams5_txt, "Independent 5h + 7d rolling pools") if p)
            detail_prefix = f"5h: {w5['reset_text']} · 周: {wwk['reset_text']}"
            detail_prefix_en = f"5h: {w5['reset_text_en']} · Wk: {wwk['reset_text_en']}"
            cards.append(
                {
                    "pool": "agy_claude_5h",
                    "title": "Antigravity · Claude 5.5 / OSS 双周期池",
                    "title_en": "Antigravity · Claude 5.5 / OSS 5h + Weekly",
                    "badge": source_badge,
                    "badge_en": source_badge_en,
                    "badge_tone": "warn" if eff_rem < 25.0 else ("live" if live_ok else "stale"),
                    "primary": f"5h {rem5:.1f}% · 周 {remw:.1f}%",
                    "primary_en": f"5h {rem5:.1f}% · Wk {remw:.1f}%",
                    "detail": f"{detail_prefix} · {fams5_txt}（独立 5h + 1周双池，与 Gemini 互不占用）"
                    if fams5_txt
                    else f"{detail_prefix}（独立 5h + 1周双池，与 Gemini 互不占用）",
                    "detail_en": f"{detail_prefix_en} · {fams5_txt} (independent 5h + 7d pools)"
                    if fams5_txt
                    else f"{detail_prefix_en} (independent 5h + 7d pools)",
                    "kicker": kicker_zh,
                    "kicker_en": kicker_en,
                    "pct": eff_rem,
                    "pct_5h": rem5,
                    "pct_weekly": remw,
                    "windows": c5_windows,
                    "meta": c5,
                }
            )
        else:
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
                    "badge_tone": "warn" if rem5 < 25.0 else ("live" if live_ok else "stale"),
                    "primary": f"剩余 {rem5:.1f}%",
                    "primary_en": f"{rem5:.1f}% left",
                    "detail": f"{c5['reset_text']} · {fams5_txt}{c5_note_zh}",
                    "detail_en": f"{reset5_en} · {fams5_txt} {c5_note_en}",
                    "pct": rem5,
                    "meta": c5,
                }
            )

    return cards, {"live": live_ok, "snapshot": snap, "lens": lens_stats}
