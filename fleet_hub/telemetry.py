"""Genuine live telemetry probes for all Google AI Ultra compute/resource pools (zero fake mocks)."""

from __future__ import annotations

import calendar
import concurrent.futures
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .agy_quota_probe import probe_antigravity_quotas
from .bridges import collect_bridge_statuses, invalidate_bridge_cache
from .burn_advisor import build_burn_recommendations, compute_routing_verdict
from .config import (
    HUB_ROOT,
    PLAYWRIGHT_BROWSERS_DIR,
    WORKSPACE_ROOT,
    load_secrets,
    mask_email,
    redact_path,
    resolve_tool_bin,
    wrap_cmd,
)
from .db import FleetDB, now_iso

_CACHE_LOCK = threading.Lock()
_CACHE_BY_PRIVACY: dict[bool, dict[str, Any]] = {}
TTL_SEC = 180.0

GFLOW_WIRE_PROBE = HUB_ROOT / "fleet_hub" / "gflow_wire_probe.py"
GCP_CREDITS_PROBE = HUB_ROOT / "fleet_hub" / "gcp_credits_probe.py"
GFLOW_PYTHON_CANDIDATE = Path.home() / ".local" / "share" / "uv" / "tools" / "gflow-cli" / "bin" / "python"

COLAB_BAL_RE = re.compile(r"Current balance:\s*([0-9]+(?:\.[0-9]+)?)\s*compute units", re.IGNORECASE)
COLAB_RATE_RE = re.compile(r"Usage rate:\s*([0-9]+(?:\.[0-9]+)?)\s*/hr", re.IGNORECASE)
COLAB_ACTIVE_RE = re.compile(r"Active assignments:\s*(\d+)", re.IGNORECASE)

GDRIVE_USED_RE = re.compile(r"Used:\s*([^\r\n]+)")
GDRIVE_LIMIT_RE = re.compile(r"Limit:\s*([^\r\n]+)")
GDRIVE_TRASH_RE = re.compile(r"Trash:\s*([^\r\n]+)")


def _with_proxy_env(base_env: dict[str, str]) -> dict[str, str]:
    """Ensure proxy vars are forwarded for cloud probes when configured or auto-detected."""
    env = dict(base_env)
    secrets = load_secrets()
    proxy = secrets.fleet_proxy
    if not proxy and secrets.fleet_auto_proxy_port > 0 and not env.get("https_proxy") and not env.get("HTTPS_PROXY"):
        try:
            with socket.create_connection(("127.0.0.1", secrets.fleet_auto_proxy_port), timeout=0.4):
                proxy = f"http://127.0.0.1:{secrets.fleet_auto_proxy_port}"
        except OSError:
            proxy = ""
    if proxy:
        env.setdefault("HTTP_PROXY", proxy)
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("http_proxy", proxy)
        env.setdefault("https_proxy", proxy)
        if proxy.startswith("http://127.0.0.1:"):
            port_part = proxy.rsplit(":", 1)[-1].rstrip("/")
            if port_part.isdigit():
                env.setdefault("ALL_PROXY", f"socks5://127.0.0.1:{port_part}")
                env.setdefault("all_proxy", f"socks5://127.0.0.1:{port_part}")
    env.setdefault("NO_PROXY", "127.0.0.1,localhost")
    env.setdefault("no_proxy", "127.0.0.1,localhost")
    return env


def _probe_colab(db: FleetDB) -> dict[str, Any]:
    """Probe live Colab balance via google-colab-cli (`colab usage`)."""
    secrets = load_secrets()
    snap: dict[str, Any] | None = None
    live_ok = False

    colab_bin = resolve_tool_bin("colab")
    if colab_bin is not None:
        try:
            proc = subprocess.run(
                wrap_cmd([str(colab_bin), "usage"]),
                capture_output=True,
                text=True,
                timeout=12,
                env=_with_proxy_env(os.environ),
            )
            if proc.returncode == 0:
                m_bal = COLAB_BAL_RE.search(proc.stdout)
                m_rate = COLAB_RATE_RE.search(proc.stdout)
                m_act = COLAB_ACTIVE_RE.search(proc.stdout)
                if m_bal:
                    balance = float(m_bal.group(1))
                    rate = float(m_rate.group(1)) if m_rate else 0.0
                    active = int(m_act.group(1)) if m_act else 0
                    snap = {
                        "balance": balance,
                        "rate": rate,
                        "active": active,
                        "fetched_at": now_iso(),
                    }
                    db.set_meta("telemetry_colab_json", json.dumps(snap, ensure_ascii=False))
                    live_ok = True
        except (subprocess.SubprocessError, OSError, ValueError):
            pass

    if snap is None:
        cached = db.get_meta("telemetry_colab_json", "")
        if cached:
            try:
                snap = json.loads(cached)
            except json.JSONDecodeError:
                snap = None

    if snap is None:
        return {
            "pool": "colab_cu",
            "title": "Google Colab L4 GPU 池",
            "title_en": "Google Colab L4 GPU",
            "badge": "⚪ 暂未连上 colab usage",
            "badge_en": "⚪ colab usage offline",
            "badge_tone": "muted",
            "primary": "未获取",
            "primary_en": "Unavailable",
            "detail": "请检查网络或 colab CLI 登录状态（google-colab-cli）",
            "detail_en": "Check network or `colab auth login` (google-colab-cli)",
            "pct": None,
        }

    bal = float(snap["balance"])
    rate = float(snap["rate"])
    active = int(snap["active"])
    l4_hours = bal / 1.94
    running_alert = active > 0 or rate > 0.0
    badge = "🟠 实例计费中！" if running_alert else ("🟢 官方实时 API (colab usage)" if live_ok else f"🟡 官方快照 ({snap['fetched_at']})")
    badge_en = "🟠 Billing Active!" if running_alert else ("🟢 Live API (colab usage)" if live_ok else f"🟡 Snapshot ({snap['fetched_at']})")
    pct = min(100.0, (bal / max(secrets.colab_monthly_cu, 1.0)) * 100.0)
    return {
        "pool": "colab_cu",
        "title": "Google Colab L4 GPU 池",
        "title_en": "Google Colab L4 GPU",
        "badge": badge,
        "badge_en": badge_en,
        "badge_tone": "warn" if running_alert else "live",
        "primary": f"{bal:.2f} CU 可用",
        "primary_en": f"{bal:.2f} CU left",
        "detail": f"约 {l4_hours:.0f} 小时 L4 显卡 · 速率 {rate:.2f}/hr · 活跃实例 {active} 个",
        "detail_en": f"~{l4_hours:.0f}h L4 GPU · burn {rate:.2f}/hr · {active} active",
        "pct": pct,
        "meta": snap,
    }


def _probe_storage(db: FleetDB, privacy: bool = False) -> dict[str, Any]:
    """Probe workspace storage capacity, AI-Projects size, and Google Drive quota."""
    ws_path = WORKSPACE_ROOT if WORKSPACE_ROOT.exists() else Path.home()
    st = os.statvfs(ws_path)
    total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
    avail_gb = (st.f_bavail * st.f_frsize) / (1024**3)
    used_gb = total_gb - avail_gb
    pct = min(100.0, (used_gb / max(total_gb, 1.0)) * 100.0)
    ws_label = redact_path(str(ws_path), privacy=privacy)
    disk_str = f"{ws_label} 可用 {avail_gb:.1f} GB / {total_gb:.0f} GB（已用 {pct:.0f}%）"
    disk_str_en = f"{ws_label}: {avail_gb:.1f} GB free / {total_gb:.0f} GB ({pct:.0f}% used)"

    ai_hub = Path(db.get_meta("last_ai_hub", "")) if db.get_meta("last_ai_hub", "") else None
    ai_size_mb = 0.0
    ai_files = 0
    if ai_hub and ai_hub.exists():
        for p in ai_hub.rglob("*"):
            if "_archive" in p.relative_to(ai_hub).parts:
                continue
            if p.is_file():
                ai_files += 1
                try:
                    ai_size_mb += p.stat().st_size / (1024 * 1024)
                except OSError:
                    pass

    gd_cmd_env = _resolve_gdrive_quota_cmd()
    gd_snap: dict[str, str] | None = None
    live_gd = False
    if gd_cmd_env is not None:
        gd_cmd, gd_env = gd_cmd_env
        try:
            proc = subprocess.run(
                gd_cmd,
                capture_output=True,
                text=True,
                timeout=8,
                env=gd_env,
            )
            if proc.returncode == 0:
                u = GDRIVE_USED_RE.search(proc.stdout)
                lim = GDRIVE_LIMIT_RE.search(proc.stdout)
                tr = GDRIVE_TRASH_RE.search(proc.stdout)
                if u and lim:
                    gd_snap = {
                        "used": u.group(1).strip(),
                        "limit": lim.group(1).strip(),
                        "trash": tr.group(1).strip() if tr else "0",
                        "fetched_at": now_iso(),
                    }
                    db.set_meta("telemetry_gdrive_quota", json.dumps(gd_snap, ensure_ascii=False))
                    live_gd = True
        except (subprocess.SubprocessError, OSError):
            pass

    if gd_snap is None:
        cached = db.get_meta("telemetry_gdrive_quota", "")
        if cached:
            try:
                gd_snap = json.loads(cached)
            except json.JSONDecodeError:
                gd_snap = None

    if gd_snap:
        primary = f"云盘已用 {gd_snap['used']} / {gd_snap['limit']}"
        primary_en = f"Drive {gd_snap['used']} / {gd_snap['limit']}"
        badge = "🟢 实时磁盘 + Drive 官方配额" if live_gd else "🟢 实时磁盘 + Drive 配额快照"
        badge_en = "🟢 Live Disk + Drive Quota" if live_gd else "🟢 Live Disk + Drive Snapshot"
        detail = f"{disk_str} · AI-Projects 实占 {ai_size_mb:.1f} MB（{ai_files} 文件）"
        detail_en = f"{disk_str_en} · AI-Projects {ai_size_mb:.1f} MB ({ai_files} files)"
    else:
        primary = disk_str
        primary_en = disk_str_en
        badge = "🟢 实时磁盘 statvfs"
        badge_en = "🟢 Live statvfs"
        detail = f"AI-Projects 实占 {ai_size_mb:.1f} MB（{ai_files} 文件）"
        detail_en = f"AI-Projects {ai_size_mb:.1f} MB ({ai_files} files)"

    return {
        "pool": "gdrive_bus",
        "title": "Google Drive + 工作区存储总线",
        "title_en": "Google Drive + SSD Storage Bus",
        "badge": badge,
        "badge_en": badge_en,
        "badge_tone": "live",
        "primary": primary,
        "primary_en": primary_en,
        "detail": detail,
        "detail_en": detail_en,
        "pct": pct,
    }


def _resolve_gdrive_quota_cmd() -> tuple[list[str], dict[str, str]] | None:
    """Resolve `gdrive readonly quota` in both interactive IDE shells and background launchd daemons."""
    env = _with_proxy_env(os.environ)
    gdrive_bin = resolve_tool_bin("gdrive")
    if gdrive_bin is not None:
        return wrap_cmd([str(gdrive_bin), "readonly", "quota"]), env

    scripts_dir = Path.home() / ".gemini" / "config" / "plugins" / "gdrive" / "skills" / "gdrive" / "scripts"
    ls_candidates = [
        Path("/Applications/Antigravity.app/Contents/Resources/bin/language_server"),
        resolve_tool_bin("language_server"),
    ]
    ls_bin = next((Path(c) for c in ls_candidates if c and Path(c).exists()), None)
    if ls_bin is not None and scripts_dir.is_dir():
        env["PATH"] = f"{scripts_dir}{os.pathsep}{env.get('PATH', '')}"
        return wrap_cmd([str(ls_bin), "plugin-cli", "gdrive", "readonly", "quota"]), env
    return None


def _playwright_python() -> Path | None:
    if GFLOW_PYTHON_CANDIDATE.exists():
        return GFLOW_PYTHON_CANDIDATE
    gflow = resolve_tool_bin("gflow") or resolve_tool_bin("gflow-cli")
    if gflow is not None:
        cand = gflow.resolve().parent / "python"
        if cand.exists():
            return cand
    try:
        import playwright  # noqa: F401
        import sys

        return Path(sys.executable)
    except ImportError:
        return None


def sync_gcp_credits_live(db: FleetDB, login_mode: bool = False) -> tuple[bool, str, dict[str, Any] | None]:
    """Read real remaining GCP Billing Credits via headless Playwright (or --login once)."""
    py_bin = _playwright_python()
    if py_bin is None or not GCP_CREDITS_PROBE.exists():
        return False, "未找到 Playwright 运行时（请先安装 gflow-cli 或 playwright）", None

    env = _with_proxy_env(os.environ)
    env["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_DIR
    cmd = wrap_cmd([str(py_bin), str(GCP_CREDITS_PROBE), *(["--login"] if login_mode else [])])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=200 if login_mode else 40, env=env)
        out = proc.stdout.strip()
        if "{" not in out:
            return False, f"GCP 账单探针未返回 JSON: {(proc.stderr or out)[:200]}", None
        parsed = json.loads(out[out.index("{") :])
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError) as exc:
        return False, f"读取 GCP 账单失败: {exc}", None

    status = parsed.get("status")
    if status == "ok":
        db.set_meta("telemetry_gcp_credits_json", json.dumps(parsed, ensure_ascii=False))
        db.sync_pool_budget("paid_gemini_api", float(parsed.get("original_total") or 0.0))
        invalidate_telemetry_cache()
        rem = float(parsed["remaining_total"])
        orig = float(parsed["original_total"])
        used = float(parsed["used_total"])
        cnt = int(parsed["active_grants_count"])
        return True, f"已自动同步 GCP 赠金账单（{cnt} 笔生效）：剩余 ${rem:.2f} / ${orig:.2f}（已扣 ${used:.2f}）", parsed
    if status == "needs_login":
        return False, "Google Cloud 浏览器会话未登录或已过期，请终端运行一次 `ultra gcp-login` 后重试", parsed
    return False, f"GCP 账单读取未完成: {parsed.get('reason') or status}", parsed


def _probe_paid_api(db: FleetDB) -> dict[str, Any]:
    """Report live synced GCP Billing Credits first, falling back to manual calibration & local usageMetadata."""
    secrets = load_secrets()
    calls = int(db.get_meta("paid_api_calls", "0") or 0)
    prompt_tok = int(db.get_meta("paid_api_prompt_tokens", "0") or 0)
    out_tok = int(db.get_meta("paid_api_output_tokens", "0") or 0)
    ledger = {row["pool"]: row for row in db.get_quota_ledger()}
    local_usd = float(ledger.get("paid_gemini_api", {}).get("used_units", 0.0))

    gcp_raw = db.get_meta("telemetry_gcp_credits_json", "")
    if gcp_raw:
        try:
            gcp = json.loads(gcp_raw)
        except json.JSONDecodeError:
            gcp = None
        if isinstance(gcp, dict) and gcp.get("status") == "ok":
            rem = float(gcp.get("remaining_total") or 0.0)
            orig = float(gcp.get("original_total") or 0.0)
            used = float(gcp.get("used_total") or 0.0)
            cnt = int(gcp.get("active_grants_count") or 0)
            eg = gcp.get("earliest_grant") or {}
            pct = max(0.0, min(100.0, (rem / max(orig, 0.01)) * 100.0))
            tone = "warn" if pct < 15.0 else "live"
            exp_note = (
                f" · 最近到期: ${float(eg['remaining']):.2f} ({eg['end_date']})"
                if isinstance(eg, dict) and eg.get("end_date")
                else ""
            )
            exp_note_en = (
                f" · Next expiry: ${float(eg['remaining']):.2f} ({eg['end_date']})"
                if isinstance(eg, dict) and eg.get("end_date")
                else ""
            )
            local_note = f" · 本机 API 记账 ${local_usd:.4f} ({calls} 次)" if calls > 0 else ""
            local_note_en = f" · Local API ${local_usd:.4f} ({calls} calls)" if calls > 0 else ""
            return {
                "pool": "paid_gemini_api",
                "title": "Google Cloud / Gemini 赠金池",
                "title_en": "Google Cloud / Gemini Credits",
                "badge": f"🟢 GCP 账单快照 ({cnt} 笔生效 · {gcp.get('fetched_at', '')[:16]})",
                "badge_en": f"🟢 GCP Grants ({cnt} active · {gcp.get('fetched_at', '')[:16]})",
                "badge_tone": tone,
                "primary": f"剩余 ${rem:.2f} / ${orig:.2f}",
                "primary_en": f"${rem:.2f} / ${orig:.2f} left",
                "detail": f"总已扣 ${used:.2f}（含 VPS / 云服务 / API）{exp_note}{local_note}",
                "detail_en": f"${used:.2f} spent (VPS / Cloud / API){exp_note_en}{local_note_en}",
                "pct": pct,
                "meta": {
                    "gcp_synced": True,
                    "local_used_usd": local_usd,
                    "used_usd": used,
                    "remaining_usd": rem,
                    "budget_usd": orig,
                    "earliest_grant": eg,
                    "grants": gcp.get("grants") or [],
                },
            }

    budget = float(secrets.paid_api_monthly_usd)
    ext_used = max(0.0, float(secrets.paid_api_external_used_usd))
    db.sync_pool_budget("paid_gemini_api", budget)
    total_used = local_usd + ext_used

    if not secrets.paid_api_enabled and budget <= 0:
        return {
            "pool": "paid_gemini_api",
            "title": "Google Cloud / Gemini 赠金池",
            "title_en": "Google Cloud / Gemini Credits",
            "badge": "⚪ 未配置 / 待同步",
            "badge_en": "⚪ Unconfigured / Sync Needed",
            "badge_tone": "muted",
            "primary": "待同步 GCP 账单",
            "primary_en": "Sync GCP Credits",
            "detail": "点击「自动读取 GCP 赠金」直接抓取真实剩余金额与扣费明细",
            "detail_en": "Click Auto-Sync GCP Credits to fetch live active grant balances",
            "pct": None,
            "meta": {"gcp_synced": False, "local_used_usd": local_usd, "external_used_usd": ext_used, "budget_usd": 0.0},
        }

    if budget <= 0:
        return {
            "pool": "paid_gemini_api",
            "title": "Google Cloud / Gemini 赠金池",
            "title_en": "Google Cloud / Gemini Credits",
            "badge": f"🔵 已接入 ({secrets.gemini_triage_model}) · 待同步额度",
            "badge_en": f"🔵 Active ({secrets.gemini_triage_model}) · Sync Budget",
            "badge_tone": "local",
            "primary": f"本月本地实计 ${local_usd:.4f}",
            "primary_en": f"${local_usd:.4f} local spend",
            "detail": f"{calls} 次调用（入 {prompt_tok:,} / 出 {out_tok:,}）· 点「自动读取 GCP 赠金」自动汇总 VPS 与全部消费",
            "detail_en": f"{calls} calls (in {prompt_tok:,} / out {out_tok:,}) · Click Auto-Sync GCP Credits",
            "pct": None,
            "meta": {"gcp_synced": False, "local_used_usd": local_usd, "external_used_usd": ext_used, "budget_usd": 0.0},
        }

    remaining_usd = max(0.0, budget - total_used)
    rem_pct = max(0.0, min(100.0, (remaining_usd / budget) * 100.0))
    tone = "warn" if rem_pct < 15.0 else "live"
    ext_note = f" + 外部校准 ${ext_used:.2f}" if ext_used > 0 else ""
    ext_note_en = f" + external ${ext_used:.2f}" if ext_used > 0 else ""
    return {
        "pool": "paid_gemini_api",
        "title": "Google Cloud / Gemini 赠金池",
        "title_en": "Google Cloud / Gemini Credits",
        "badge": f"🟡 手动基数 ({secrets.gemini_triage_model})",
        "badge_en": f"🟡 Manual Baseline ({secrets.gemini_triage_model})",
        "badge_tone": tone,
        "primary": f"剩余 ${remaining_usd:.2f} / ${budget:.0f}",
        "primary_en": f"${remaining_usd:.2f} / ${budget:.0f} left",
        "detail": f"本地实计 ${local_usd:.4f}（{calls} 次）{ext_note} · 点「自动读取 GCP 赠金」获取精确扣费",
        "detail_en": f"Local ${local_usd:.4f} ({calls} calls){ext_note_en} · Click Auto-Sync GCP Credits",
        "pct": rem_pct,
        "meta": {
            "gcp_synced": False,
            "local_used_usd": local_usd,
            "external_used_usd": ext_used,
            "total_used_usd": total_used,
            "remaining_usd": remaining_usd,
            "budget_usd": budget,
        },
    }


def _probe_ai_studio(ai_hub: Path) -> dict[str, Any]:
    """Real Pacific Time midnight reset countdown + local synced specs count."""
    pt_tz = ZoneInfo("America/Los_Angeles")
    local_tz = datetime.now().astimezone().tzinfo
    now_pt = datetime.now(pt_tz)
    next_reset_pt = (now_pt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    delta = next_reset_pt - now_pt
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    mins = rem // 60
    reset_local = next_reset_pt.astimezone(local_tz).strftime("%H:%M")

    spec_packs = 0
    if ai_hub.exists():
        for sp in ai_hub.glob("*/specs/*"):
            if sp.parent.parent.name.startswith("_"):
                continue
            if sp.is_dir():
                spec_packs += 1

    return {
        "pool": "ai_studio_daily",
        "title": "Google AI Studio 网页池",
        "title_en": "Google AI Studio Daily",
        "badge": "🔵 真实重置时钟（每日清零）",
        "badge_en": "🔵 Pacific Midnight Reset",
        "badge_tone": "local",
        "primary": f"距下次每日重置 {hours}h {mins}m",
        "primary_en": f"Resets in {hours}h {mins}m",
        "detail": f"太平洋午夜重置（本地 {reset_local}）· 云端 specs 载荷包 {spec_packs} 组",
        "detail_en": f"Midnight PT ({reset_local} local) · {spec_packs} synced spec bundles",
        "pct": None,
    }


def _probe_flow_genie(db: FleetDB, privacy: bool = False) -> dict[str, Any]:
    """Probe gflow-cli credits silently via pure-HTTPS nzlxg wire probe (0 browser popups)."""
    secrets = load_secrets()
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    days_left = last_day - now.day
    gflow = resolve_tool_bin("gflow") or resolve_tool_bin("gflow-cli")
    gflow_py = GFLOW_PYTHON_CANDIDATE if GFLOW_PYTHON_CANDIDATE.exists() else None
    if gflow_py is None and gflow is not None:
        # Check same venv as gflow
        cand = gflow.resolve().parent / "python"
        if cand.exists():
            gflow_py = cand

    if gflow is None or gflow_py is None or not GFLOW_WIRE_PROBE.exists():
        return {
            "pool": "flow_credits",
            "title": "Google Flow + Project Genie",
            "title_en": "Google Flow + Project Genie",
            "badge": "⚪ 未安装 gflow-cli",
            "badge_en": "⚪ gflow-cli Not Installed",
            "badge_tone": "muted",
            "primary": f"距月末清零还剩 {days_left} 天",
            "primary_en": f"{days_left}d until month-end reset",
            "detail": "安装 gflow-cli 后可直连读取剩余 Veo / Nano Banana 积分",
            "detail_en": "Install gflow-cli to stream live Veo / Nano Banana credits",
            "pct": None,
        }

    env = _with_proxy_env(os.environ)
    env["PLAYWRIGHT_BROWSERS_PATH"] = PLAYWRIGHT_BROWSERS_DIR
    env.setdefault("GFLOW_CLI_TELEMETRY", "0")

    snap: dict[str, Any] | None = None
    live_ok = False
    needs_login = False

    try:
        cred_proc = subprocess.run(
            wrap_cmd([str(gflow_py), str(GFLOW_WIRE_PROBE)]),
            capture_output=True,
            text=True,
            timeout=25,
            env=env,
        )
        out = cred_proc.stdout.strip()
        if "{" in out:
            parsed = json.loads(out[out.index("{") :])
            if parsed.get("status") == "ok" and parsed.get("authenticated") and parsed.get("credits") is not None:
                snap = {
                    "credits": float(parsed["credits"]),
                    "email": parsed.get("email") or "",
                    "fetched_at": now_iso(),
                }
                db.set_meta("telemetry_gflow_json", json.dumps(snap, ensure_ascii=False))
                live_ok = True
            elif parsed.get("status") == "needs_login":
                needs_login = True
    except (subprocess.SubprocessError, OSError, ValueError, json.JSONDecodeError):
        pass

    if snap is None:
        cached = db.get_meta("telemetry_gflow_json", "")
        if cached:
            try:
                snap = json.loads(cached)
            except json.JSONDecodeError:
                snap = None

    if snap is not None and not needs_login:
        credits = float(snap["credits"])
        email = mask_email(str(snap.get("email") or "已授权账号"), privacy=privacy)
        email_en = mask_email(str(snap.get("email") or "signed-in account"), privacy=privacy)
        badge = "🟢 官方实时 RPC (无感直连)" if live_ok else f"🟡 会话快照 ({snap['fetched_at']})"
        badge_en = "🟢 Live HTTPS RPC" if live_ok else f"🟡 Snapshot ({snap['fetched_at']})"
        denom = secrets.flow_monthly_credits if credits > 10500.0 else min(secrets.flow_monthly_credits, 10000.0)
        return {
            "pool": "flow_credits",
            "title": "Google Flow + Project Genie",
            "title_en": "Google Flow + Project Genie",
            "badge": badge,
            "badge_en": badge_en,
            "badge_tone": "live",
            "primary": f"{credits:,.0f} 积分可用",
            "primary_en": f"{credits:,.0f} credits",
            "detail": f"{email} · 距月末清零还剩 {days_left} 天",
            "detail_en": f"{email_en} · {days_left}d until month-end expiry",
            "pct": min(100.0, (credits / max(denom, 1.0)) * 100.0),
            "meta": snap,
        }

    return {
        "pool": "flow_credits",
        "title": "Google Flow + Project Genie",
        "title_en": "Google Flow + Project Genie",
        "badge": "🟡 CLI 已安装 · 待登录会话",
        "badge_en": "🟡 CLI Installed · Login Needed",
        "badge_tone": "local",
        "primary": f"距月末清零还剩 {days_left} 天",
        "primary_en": f"{days_left}d until month-end reset",
        "detail": "终端执行 `gflow auth login` 完成一次浏览器登录后自动读取真实积分",
        "detail_en": "Run `gflow auth login` once in terminal to read live Flow credits",
        "pct": None,
    }


def collect_live_telemetry(
    db: FleetDB,
    ai_hub: Path,
    force: bool = False,
    privacy: bool | None = None,
) -> list[dict[str, Any]]:
    """Return all live quota pool cards with a 180-second cache keyed by privacy mode."""
    secrets = load_secrets()
    use_privacy = secrets.fleet_privacy_mode if privacy is None else bool(privacy)
    db.set_meta("last_ai_hub", str(ai_hub))

    with _CACHE_LOCK:
        entry = _CACHE_BY_PRIVACY.get(use_privacy)
        if not force and entry is not None and (time.time() - float(entry["ts"])) < TTL_SEC:
            return entry["cards"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        f_agy = pool.submit(probe_antigravity_quotas, db, use_privacy)
        f_colab = pool.submit(_probe_colab, db)
        f_storage = pool.submit(_probe_storage, db, use_privacy)
        f_flow = pool.submit(_probe_flow_genie, db, use_privacy)

        agy_cards, agy_meta = f_agy.result()
        cards = [
            *agy_cards,
            f_colab.result(),
            f_flow.result(),
            f_storage.result(),
            _probe_ai_studio(ai_hub),
            _probe_paid_api(db),
        ]

    meta_out = {"lens": agy_meta.get("lens")}
    with _CACHE_LOCK:
        if force:
            _CACHE_BY_PRIVACY.clear()
        _CACHE_BY_PRIVACY[use_privacy] = {
            "ts": time.time(),
            "cards": cards,
            "meta": meta_out,
        }
    return cards


def invalidate_telemetry_cache() -> None:
    """Clear in-memory telemetry & bridge caches so updated settings/models take effect immediately."""
    with _CACHE_LOCK:
        _CACHE_BY_PRIVACY.clear()
    invalidate_bridge_cache()


def collect_cockpit_snapshot(
    db: FleetDB,
    ai_hub: Path,
    force: bool = False,
    privacy: bool | None = None,
) -> dict[str, Any]:
    """Collect unified pools, burn advisor recommendations, routing verdict, and wheel bridges."""
    secrets = load_secrets()
    use_privacy = secrets.fleet_privacy_mode if privacy is None else bool(privacy)
    cards = collect_live_telemetry(db, ai_hub, force=force, privacy=use_privacy)
    with _CACHE_LOCK:
        lens_stats = ((_CACHE_BY_PRIVACY.get(use_privacy) or {}).get("meta") or {}).get("lens")
    if lens_stats is None:
        cached_lens = db.get_meta("telemetry_agy_lens_json", "")
        if cached_lens:
            try:
                lens_stats = json.loads(cached_lens)
            except json.JSONDecodeError:
                lens_stats = None

    advisor = build_burn_recommendations(cards, lens_stats=lens_stats)
    routing = compute_routing_verdict(cards, lens_stats=lens_stats)
    bridges = collect_bridge_statuses(secrets, force=force)
    return {
        "pools": cards,
        "advisor": advisor,
        "routing": routing,
        "bridges": bridges,
        "lens": lens_stats,
    }
