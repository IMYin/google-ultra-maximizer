"""Native Antigravity & open-source wheel health probes (antigravity, agy-lens, agent-desktop, apprise) and 5h wakeup helper."""

from __future__ import annotations

import concurrent.futures
import json
import os
import socket
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any

from .agy_quota_probe import discover_daemon_endpoints
from .config import RuntimeSecrets, resolve_tool_bin, wrap_cmd

_BRIDGE_LOCK = threading.Lock()
_BRIDGE_TS = 0.0
_BRIDGE_DATA: list[dict[str, Any]] | None = None
BRIDGE_TTL_SEC = 120.0

GITHUB_REPO = "IMYin/google-ultra-maximizer"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"
_STAR_LOCK = threading.Lock()
_STAR_TS = 0.0
_STAR_CACHE: dict[str, Any] | None = None
STAR_TTL_SEC = 300.0


def probe_antigravity_native() -> dict[str, Any]:
    """Check native Antigravity 2.0 daemon RPC, agy CLI, and app bundle status."""
    endpoints = discover_daemon_endpoints()
    agy_cli = resolve_tool_bin("agy")
    has_app = Path("/Applications/Antigravity.app").exists()

    if endpoints:
        ver = str(endpoints[0][2] or "").strip()
        ver_disp = f" v{ver}" if ver else ""
        cli_note_zh = " · agy CLI 就绪" if agy_cli else ""
        cli_note_en = " · agy CLI ready" if agy_cli else ""
        return {
            "id": "antigravity",
            "name": "Antigravity 2.0",
            "name_en": "Antigravity 2.0",
            "repo": "google/antigravity",
            "tone": "live",
            "status": f"官方直连{ver_disp}",
            "status_en": f"Live LS RPC{ver_disp}",
            "detail": f"本机 Language Server 环回直连{cli_note_zh} · 原生 IDE / Swarm / 子代理主执行面",
            "detail_en": f"Local Language Server RPC active{cli_note_en} · native IDE, CLI & Swarm runtime",
            "action_url": "",
            "cli_installed": bool(agy_cli),
            "ls_version": ver,
        }

    if agy_cli or has_app:
        return {
            "id": "antigravity",
            "name": "Antigravity 2.0",
            "name_en": "Antigravity 2.0",
            "repo": "google/antigravity",
            "tone": "local",
            "status": "已安装 · 待启动",
            "status_en": "Installed · Standby",
            "detail": "打开 Antigravity 2.0 或运行 agy 自动直连 5h + 1周双周期配额",
            "detail_en": "Launch Antigravity 2.0 or agy to stream live 5h + 7d quotas",
            "action_url": "",
            "cli_installed": bool(agy_cli),
            "ls_version": "",
        }

    return {
        "id": "antigravity",
        "name": "Antigravity 2.0",
        "name_en": "Antigravity 2.0",
        "repo": "google/antigravity",
        "tone": "muted",
        "status": "未检测到",
        "status_en": "Not Detected",
        "detail": "安装并登录 Antigravity 2.0 (Google AI Ultra) 开启原生遥测",
        "detail_en": "Install & sign in to Antigravity 2.0 for native telemetry",
        "action_url": "",
        "cli_installed": False,
        "ls_version": "",
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


def invalidate_star_cache() -> None:
    """Clear cached GitHub star status."""
    global _STAR_TS, _STAR_CACHE
    with _STAR_LOCK:
        _STAR_TS = 0.0
        _STAR_CACHE = None


def invalidate_bridge_cache() -> None:
    """Clear cached open-source wheel bridge probes."""
    global _BRIDGE_TS, _BRIDGE_DATA
    with _BRIDGE_LOCK:
        _BRIDGE_TS = 0.0
        _BRIDGE_DATA = None
    invalidate_star_cache()


def collect_bridge_statuses(secrets: RuntimeSecrets, force: bool = False) -> list[dict[str, Any]]:
    """Collect cached status badges for native Antigravity and integrated open-source wheels concurrently."""
    global _BRIDGE_TS, _BRIDGE_DATA
    with _BRIDGE_LOCK:
        if not force and _BRIDGE_DATA is not None and (time.time() - _BRIDGE_TS) < BRIDGE_TTL_SEC:
            return _BRIDGE_DATA

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        f_agy = pool.submit(probe_antigravity_native)
        f_lens = pool.submit(probe_agy_lens)
        f_ad = pool.submit(probe_agent_desktop)
        f_not = pool.submit(probe_notifier_wheel, secrets)
        items = [
            f_agy.result(),
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
        return False, "未安装 antigravity-usage，请直接在 Antigravity 发一条轻提示词开启 5h 窗口"
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


def _starred_api_path(repository: str) -> str | None:
    parts = repository.split("/")
    if len(parts) != 2 or not all(p and p not in (".", "..") for p in parts):
        return None
    return f"user/starred/{urllib.parse.quote(parts[0], safe='')}/{urllib.parse.quote(parts[1], safe='')}"


def _gh_env(secrets: RuntimeSecrets) -> dict[str, str]:
    env = dict(os.environ)
    env["GH_PROMPT_DISABLED"] = "1"
    proxy = secrets.fleet_proxy
    if not proxy and secrets.fleet_auto_proxy_port > 0 and not env.get("HTTPS_PROXY") and not env.get("https_proxy"):
        try:
            with socket.create_connection(("127.0.0.1", secrets.fleet_auto_proxy_port), timeout=0.3):
                proxy = f"http://127.0.0.1:{secrets.fleet_auto_proxy_port}"
        except OSError:
            proxy = ""
    if proxy:
        env.setdefault("HTTP_PROXY", proxy)
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("http_proxy", proxy)
        env.setdefault("https_proxy", proxy)
    env.setdefault("NO_PROXY", "127.0.0.1,localhost")
    env.setdefault("no_proxy", "127.0.0.1,localhost")
    return env


def _resolve_gh_binary() -> Path | None:
    return resolve_tool_bin("gh", (Path("/opt/homebrew/bin/gh"), Path("/usr/local/bin/gh")))


def check_github_starred(
    secrets: RuntimeSecrets,
    repository: str = GITHUB_REPO,
    force: bool = False,
) -> dict[str, Any]:
    """Check whether the local signed-in `gh` CLI account already starred this repository."""
    global _STAR_TS, _STAR_CACHE
    path = _starred_api_path(repository)
    if path is None:
        return {"ok": False, "repo": repository, "url": GITHUB_REPO_URL, "gh_available": False, "starred": None}

    repo_url = f"https://github.com/{repository}"
    if repository == GITHUB_REPO and not force:
        with _STAR_LOCK:
            if _STAR_CACHE is not None and (time.time() - _STAR_TS) < STAR_TTL_SEC:
                return dict(_STAR_CACHE)

    gh_bin = _resolve_gh_binary()
    if gh_bin is None:
        res = {"ok": True, "repo": repository, "url": repo_url, "gh_available": False, "starred": None}
        if repository == GITHUB_REPO:
            with _STAR_LOCK:
                _STAR_CACHE = dict(res)
                _STAR_TS = time.time()
        return res

    gh_available = False
    starred: bool | None = None
    try:
        proc = subprocess.run(
            wrap_cmd([str(gh_bin), "api", "-i", "-X", "GET", path]),
            capture_output=True,
            text=True,
            timeout=6,
            env=_gh_env(secrets),
        )
        first_line = ((proc.stdout or "").splitlines() or [""])[0]
        if " 204 " in first_line:
            gh_available = True
            starred = True
        elif " 404 " in first_line:
            gh_available = True
            starred = False
    except (subprocess.SubprocessError, OSError):
        pass

    res = {"ok": True, "repo": repository, "url": repo_url, "gh_available": gh_available, "starred": starred}
    if repository == GITHUB_REPO:
        with _STAR_LOCK:
            _STAR_CACHE = dict(res)
            _STAR_TS = time.time()
    return res


def star_github_repo(
    secrets: RuntimeSecrets,
    repository: str = GITHUB_REPO,
) -> tuple[bool, str, dict[str, Any]]:
    """Star the repository via local `gh` CLI when signed in, or return browser fallback URL."""
    global _STAR_TS, _STAR_CACHE
    path = _starred_api_path(repository)
    if path is None:
        return False, "无效的 GitHub 仓库标识", {"starred": False, "fallback_url": GITHUB_REPO_URL, "via": "invalid"}

    repo_url = f"https://github.com/{repository}"
    gh_bin = _resolve_gh_binary()
    if gh_bin is None:
        return (
            False,
            "未检测到 gh CLI，已为你打开 GitHub 仓库页面点亮 Star",
            {"starred": False, "fallback_url": repo_url, "via": "browser"},
        )

    try:
        proc = subprocess.run(
            wrap_cmd(
                [
                    str(gh_bin),
                    "api",
                    "-i",
                    "-X",
                    "PUT",
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-H",
                    "Content-Length: 0",
                    path,
                ]
            ),
            capture_output=True,
            text=True,
            timeout=10,
            env=_gh_env(secrets),
        )
        first_line = ((proc.stdout or "").splitlines() or [""])[0]
        if proc.returncode == 0 or " 204 " in first_line:
            if repository == GITHUB_REPO:
                with _STAR_LOCK:
                    _STAR_CACHE = {
                        "ok": True,
                        "repo": repository,
                        "url": repo_url,
                        "gh_available": True,
                        "starred": True,
                    }
                    _STAR_TS = time.time()
            return (
                True,
                f"感谢点亮 Star！已为 {repository} 加星 ⭐",
                {"starred": True, "url": repo_url, "via": "gh_cli"},
            )
    except (subprocess.SubprocessError, OSError):
        pass

    return (
        False,
        "本机 gh 未授权直接加星，请在新打开的 GitHub 页面点击 Star",
        {"starred": False, "fallback_url": repo_url, "via": "browser"},
    )
