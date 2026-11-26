"""Open-source wheel health probes (t3code, openmausbot, agent-desktop, agy-lens, apprise) and 5h wakeup helper."""

from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import RuntimeSecrets, WORKSPACE_ROOT, resolve_tool_bin, wrap_cmd
from .mausbot_bridge import probe_openmausbot

NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_BRIDGE_LOCK = threading.Lock()
_BRIDGE_TS = 0.0
_BRIDGE_DATA: list[dict[str, Any]] | None = None
BRIDGE_TTL_SEC = 120.0


def probe_t3code(secrets: RuntimeSecrets) -> dict[str, Any]:
    """Check t3code CLI & local server availability."""
    t3_bin = resolve_tool_bin("t3")
    url = secrets.t3code_url.rstrip("/")
    listening = False
    try:
        req = urllib.request.Request(url, method="HEAD")
        with NO_PROXY_OPENER.open(req, timeout=1.5):
            listening = True
    except urllib.error.HTTPError:
        listening = True
    except (urllib.error.URLError, TimeoutError, OSError):
        listening = False

    if not t3_bin and not listening:
        return {
            "id": "t3code",
            "name": "T3 Code (多Agent移动端/Web控制台)",
            "name_en": "T3 Code (Mobile/Web Worktree IDE)",
            "repo": "pingdotgg/t3code",
            "tone": "muted",
            "status": "未安装",
            "status_en": "Not Installed",
            "detail": "替代自研 Telegram 交互，原生管理 Antigravity/Claude/Codex + Worktree + 手机端审批",
            "detail_en": "Mobile/Web coding & live Git worktree diffs for Antigravity, Claude Code, and Codex",
            "action_url": "",
        }

    connect_note = "本地 127.0.0.1:3773 就绪（运行 `t3 up` 开启手机远程 / T3 Connect）"
    connect_note_en = "Local 127.0.0.1:3773 ready (run `t3 up` for T3 Connect remote relay)"
    if t3_bin and listening:
        try:
            proc = subprocess.run(
                wrap_cmd([str(t3_bin), "status", "--json"]),
                capture_output=True,
                text=True,
                timeout=4,
            )
            if proc.returncode == 0 and "{" in proc.stdout:
                st = json.loads(proc.stdout)
                if (st.get("connect") or {}).get("enabled"):
                    connect_note = "T3 Connect 远程中继已开启 · 手机与桌面实时同步"
                    connect_note_en = "T3 Connect QUIC relay active · Mobile & Desktop synced"
                elif (st.get("lan") or {}).get("enabled"):
                    connect_note = "LAN / Tailscale 局域网直连已开启"
                    connect_note_en = "LAN / Tailscale direct access active"
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

    return {
        "id": "t3code",
        "name": "T3 Code (pingdotgg/t3code)",
        "name_en": "T3 Code (pingdotgg/t3code)",
        "repo": "pingdotgg/t3code",
        "tone": "live" if listening else "warn",
        "status": f"🟢 运行中 ({url})" if listening else "🟡 已安装 · 服务未启动",
        "status_en": f"🟢 Running ({url})" if listening else "🟡 Installed · Stopped",
        "detail": connect_note,
        "detail_en": connect_note_en,
        "action_url": url if listening else "",
    }


def probe_agent_desktop() -> dict[str, Any]:
    """Check vercel-labs/agent-desktop availability and macOS Accessibility permission."""
    ad_bin = resolve_tool_bin("agent-desktop")
    if not ad_bin:
        return {
            "id": "agent_desktop",
            "name": "Agent Desktop (macOS 辅助功能树操控)",
            "name_en": "Agent Desktop (macOS AX Tree)",
            "repo": "vercel-labs/agent-desktop",
            "tone": "muted",
            "status": "未安装",
            "status_en": "Not Installed",
            "detail": "免截图直接读取系统 AX 树 JSON 操控原生 App 窗口",
            "detail_en": "Structured OS Accessibility tree JSON (@ref) without pixel guessing",
            "action_url": "",
        }

    try:
        proc = subprocess.run(
            wrap_cmd([str(ad_bin), "status"]),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and "{" in proc.stdout:
            payload = json.loads(proc.stdout[proc.stdout.index("{") :])
            perms = ((payload.get("data") or {}).get("permissions") or {})
            ax_state = str((perms.get("accessibility") or {}).get("state") or "unknown")
            sr_state = str((perms.get("screen_recording") or {}).get("state") or "unknown")
            ver = str((payload.get("data") or {}).get("version") or "")
            if ax_state == "granted":
                return {
                    "id": "agent_desktop",
                    "name": f"Agent Desktop v{ver} (vercel-labs)",
                    "name_en": f"Agent Desktop v{ver} (vercel-labs)",
                    "repo": "vercel-labs/agent-desktop",
                    "tone": "live",
                    "status": "🟢 AX 辅助功能已授权",
                    "status_en": "🟢 AX Accessibility Granted",
                    "detail": f"Screen Recording: {sr_state} · 远端可无感读树点击任意桌面 App",
                    "detail_en": f"Screen Recording: {sr_state} · Native AX tree click/type ready",
                    "action_url": "",
                }
            if os.environ.get("XPC_SERVICE_NAME"):
                return {
                    "id": "agent_desktop",
                    "name": f"Agent Desktop v{ver} (vercel-labs)",
                    "name_en": f"Agent Desktop v{ver} (vercel-labs)",
                    "repo": "vercel-labs/agent-desktop",
                    "tone": "local",
                    "status": "🟢 CLI 就绪（宿主 IDE/终端独立授权）",
                    "status_en": "🟢 CLI Ready (Host TCC Scoped)",
                    "detail": "macOS TCC 按启动宿主授权；后台守护进程无法代查 Antigravity/终端状态，请以终端 `agent-desktop status` 为准",
                    "detail_en": "macOS TCC is scoped per host app; verify in terminal with `agent-desktop status`",
                    "action_url": "",
                }
            return {
                "id": "agent_desktop",
                "name": f"Agent Desktop v{ver} (vercel-labs)",
                "name_en": f"Agent Desktop v{ver} (vercel-labs)",
                "repo": "vercel-labs/agent-desktop",
                "tone": "local",
                "status": f"🟡 CLI 就绪 · AX={ax_state}",
                "status_en": f"🟡 CLI Ready · AX={ax_state}",
                "detail": "运行 `agent-desktop permissions --guide` 在系统设置开启一次辅助功能即可远程控窗",
                "detail_en": "Run `agent-desktop permissions --guide` to enable Accessibility in System Settings",
                "action_url": "",
            }
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        pass

    return {
        "id": "agent_desktop",
        "name": "Agent Desktop (vercel-labs)",
        "name_en": "Agent Desktop (vercel-labs)",
        "repo": "vercel-labs/agent-desktop",
        "tone": "local",
        "status": "🟡 已安装（状态探针超时）",
        "status_en": "🟡 Installed (Probe Timeout)",
        "detail": str(ad_bin),
        "detail_en": str(ad_bin),
        "action_url": "",
    }


def probe_agy_lens() -> dict[str, Any]:
    """Check Aoike123/agy-lens Antigravity 2.0 plugin + CLI status."""
    cli = resolve_tool_bin("agy-lens")
    plugin_json = Path.home() / ".gemini" / "config" / "plugins" / "agy-lens" / "plugin.json"
    if not cli and not plugin_json.exists():
        return {
            "id": "agy_lens",
            "name": "Agy Lens (Antigravity 2.0 侧边栏)",
            "name_en": "Agy Lens (Antigravity Sidebar)",
            "repo": "Aoike123/agy-lens",
            "tone": "muted",
            "status": "未安装",
            "status_en": "Not Installed",
            "detail": "零依赖本地分析上下文类别、tok/s 与等价 API 账单",
            "detail_en": "Local context composition, tok/s & API-equivalent savings telemetry",
            "action_url": "",
        }
    return {
        "id": "agy_lens",
        "name": "Agy Lens (Aoike123/agy-lens)",
        "name_en": "Agy Lens (Aoike123/agy-lens)",
        "repo": "Aoike123/agy-lens",
        "tone": "live",
        "status": "🟢 插件与 CLI 已挂载",
        "status_en": "🟢 Plugin & CLI Mounted",
        "detail": "Antigravity 右侧边栏可见实时 Context / Quota / History / 等价节省金额",
        "detail_en": "Live Context, Quota, History & API-equivalent ROI inside Antigravity",
        "action_url": "",
    }


def probe_notifier_wheel(secrets: RuntimeSecrets) -> dict[str, Any]:
    """Check Apprise multi-channel notifier & configured channels."""
    app_bin = resolve_tool_bin("apprise")
    urls = secrets.all_notify_urls()
    if urls and app_bin:
        return {
            "id": "apprise",
            "name": "Apprise (多渠道异步通知轮子)",
            "name_en": "Apprise (Multi-Channel Push Bus)",
            "repo": "caronc/apprise",
            "tone": "live",
            "status": f"🟢 已接入 {len(urls)} 条通道",
            "status_en": f"🟢 {len(urls)} Channel(s) Active",
            "detail": "支持 Telegram / Bark / Slack / Discord / 飞书，无需维护私造轮询脚本",
            "detail_en": "Telegram, Bark, Slack, Discord & Lark alerts without custom bot polling",
            "action_url": "",
        }
    return {
        "id": "apprise",
        "name": "Apprise (多渠道异步通知轮子)",
        "name_en": "Apprise (Multi-Channel Push Bus)",
        "repo": "caronc/apprise",
        "tone": "local" if app_bin else "muted",
        "status": "🟡 引擎已装 · 待填通道 URL" if app_bin else "⚪ 未配置",
        "status_en": "🟡 Installed · Add Notify URL" if app_bin else "⚪ Unconfigured",
        "detail": "secrets.env 填入 FLEET_NOTIFY_URLS（或 TELEGRAM_*）立即开启推送",
        "detail_en": "Set FLEET_NOTIFY_URLS (or TELEGRAM_*) in Calibrate to enable push alerts",
        "action_url": "",
    }


def invalidate_bridge_cache() -> None:
    """Clear cached open-source wheel bridge probes."""
    global _BRIDGE_TS, _BRIDGE_DATA
    with _BRIDGE_LOCK:
        _BRIDGE_TS = 0.0
        _BRIDGE_DATA = None


def collect_bridge_statuses(secrets: RuntimeSecrets, force: bool = False) -> list[dict[str, Any]]:
    """Collect cached status badges for all integrated open-source wheels concurrently."""
    global _BRIDGE_TS, _BRIDGE_DATA
    with _BRIDGE_LOCK:
        if not force and _BRIDGE_DATA is not None and (time.time() - _BRIDGE_TS) < BRIDGE_TTL_SEC:
            return _BRIDGE_DATA

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        f_t3 = pool.submit(probe_t3code, secrets)
        f_maus = pool.submit(probe_openmausbot, secrets)
        f_lens = pool.submit(probe_agy_lens)
        f_ad = pool.submit(probe_agent_desktop)
        f_not = pool.submit(probe_notifier_wheel, secrets)
        items = [
            f_t3.result(),
            f_maus.result(),
            f_lens.result(),
            f_ad.result(),
            f_not.result(),
        ]
    with _BRIDGE_LOCK:
        _BRIDGE_DATA = items
        _BRIDGE_TS = time.time()
    return items


def run_wakeup_trigger() -> tuple[bool, str]:
    """Trigger model warmup / 5-hour rolling window check via antigravity-usage if signed in."""
    au_bin = resolve_tool_bin("antigravity-usage")
    if au_bin is None:
        return False, "未安装 antigravity-usage，请使用 T3 Code 或 Antigravity 发一条轻提示词开启 5h 窗口"
    try:
        proc = subprocess.run(
            wrap_cmd([str(au_bin), "wakeup"]),
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (proc.stdout + "\n" + proc.stderr).strip()
        if proc.returncode == 0:
            return True, out or "antigravity-usage wakeup 执行完成"
        return False, out or f"wakeup 退出码 {proc.returncode}"
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"wakeup 执行异常: {exc}"


def _resolve_t3_binary() -> Path | None:
    t3_bin = resolve_tool_bin("t3")
    if t3_bin is not None:
        return t3_bin
    versions_dir = WORKSPACE_ROOT / "tools" / "t3code-home" / "runtime" / "versions"
    if versions_dir.exists():
        candidates = sorted((p / "t3" for p in versions_dir.iterdir() if p.is_dir() and (p / "t3").is_file()), reverse=True)
        if candidates:
            return candidates[0]
    return None


def create_t3_pair_link(secrets: RuntimeSecrets) -> tuple[bool, str, str]:
    """Mint a single-use T3 Code pairing URL on the running local server."""
    t3_bin = _resolve_t3_binary()
    if t3_bin is None:
        return False, "未找到 `t3` CLI", ""

    url = secrets.t3code_url.rstrip("/")
    env = os.environ.copy()
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"

    cmd = [str(t3_bin), "pair", "--ttl", "1h", "--label", "Fleet-Hub Browser"]
    t3_home_env = os.environ.get("T3CODE_HOME")
    t3_home = Path(t3_home_env) if t3_home_env else (WORKSPACE_ROOT / "tools" / "t3code-home")
    if t3_home.exists():
        env["T3CODE_HOME"] = str(t3_home)
        cmd.extend(["--base-dir", str(t3_home)])

    try:
        proc = subprocess.run(wrap_cmd(cmd), capture_output=True, text=True, timeout=15, env=env)
        out = (proc.stdout or proc.stderr or "").strip()
        tok_match = re.search(r"#token=([A-Za-z0-9_-]+)", out) or re.search(r"(?im)^\s*Token:\s*([A-Za-z0-9_-]+)", out)
        if tok_match:
            token = tok_match.group(1)
            return proc.returncode == 0, out or f"Token: {token}", f"{url}/pair#token={token}"
        url_match = re.search(r"https?://[^\s]+/pair#token=[A-Za-z0-9_-]+", out)
        return proc.returncode == 0, out or f"exit={proc.returncode}", (url_match.group(0) if url_match else "")
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"生成 T3 配对码失败: {exc}", ""
