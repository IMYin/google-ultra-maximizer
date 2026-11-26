"""OpenMausBot (milind-soni/OpenMausBot) runtime bridge, service manager, and BotMRR team deployer."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .config import (
    HUB_ROOT,
    PROJECTS_ROOT,
    STATE_DIR,
    WORKSPACE_ROOT,
    RuntimeSecrets,
    load_secrets,
    resolve_tool_bin,
    wrap_cmd,
)

NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
MAUSBOT_LAUNCHD_LABEL = "io.ultra-maximizer.openmausbot"
MAUSBOT_SYSTEMD_UNIT = "ultra-openmausbot.service"


def _maus_app_exists() -> bool:
    return (
        Path("/Applications/OpenMausBot.app").exists()
        or (WORKSPACE_ROOT / "tools" / "apps" / "OpenMausBot.app").exists()
    )


def _no_proxy_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("NO_PROXY", "")
    parts = [p.strip() for p in existing.split(",") if p.strip()]
    for host in ("127.0.0.1", "localhost"):
        if host not in parts:
            parts.append(host)
    env["NO_PROXY"] = ",".join(parts)
    env["no_proxy"] = env["NO_PROXY"]
    return env


def probe_openmausbot(secrets: RuntimeSecrets) -> dict[str, Any]:
    """Check OpenMausBot CLI / server health, loaded bots, and BYO VPS configuration."""
    cli = resolve_tool_bin("openmausbot")
    has_app = _maus_app_exists()
    url = secrets.openmausbot_url.rstrip("/")
    listening = False

    for suffix in ("/api/health/engines", "/"):
        try:
            req = urllib.request.Request(f"{url}{suffix}", method="GET")
            with NO_PROXY_OPENER.open(req, timeout=1.5) as resp:
                if resp.status < 500:
                    listening = True
                    break
        except urllib.error.HTTPError as err:
            if err.code < 500:
                listening = True
                break
        except (urllib.error.URLError, TimeoutError, OSError):
            continue

    if not cli and not has_app and not listening:
        return {
            "id": "openmausbot",
            "name": "OpenMausBot (可选扩展 · 后台巡检/VPS)",
            "name_en": "OpenMausBot (Optional Add-on)",
            "repo": "milind-soni/OpenMausBot",
            "tone": "muted",
            "status": "⚪ 可选扩展 · 未安装",
            "status_en": "⚪ Optional · Not Installed",
            "detail": "日常使用 T3 Code + Fleet-Hub 即已完备；如需无人值守巡检或 BYO VPS，运行 `./scripts/bootstrap.sh --with-mausbot` 按需开启",
            "detail_en": "Optional add-on: T3 Code + Fleet-Hub cover daily work; run `./scripts/bootstrap.sh --with-mausbot` to enable",
            "action_url": "",
            "installed": False,
            "cli_installed": False,
            "bot_count": 0,
            "bots": [],
        }

    bot_count: int | None = None
    ultra_ready = False
    bot_roster: list[dict[str, Any]] = []
    if cli and listening:
        try:
            proc = subprocess.run(
                wrap_cmd([str(cli), "bots", "--json", "--url", url]),
                capture_output=True,
                text=True,
                timeout=3,
                env=_no_proxy_env(),
            )
            if proc.returncode == 0 and proc.stdout.strip():
                raw = json.loads(proc.stdout)
                bots = raw.get("bots", raw) if isinstance(raw, dict) else raw
                if isinstance(bots, list):
                    bot_count = len(bots)
                    names = {str(b.get("name") or "") for b in bots if isinstance(b, dict)}
                    ultra_ready = "Ultra Chief" in names
                    for b in bots:
                        if not isinstance(b, dict):
                            continue
                        ms = b.get("modelSelection") or {}
                        bot_roster.append(
                            {
                                "id": str(b.get("id") or ""),
                                "name": str(b.get("name") or ""),
                                "title": str(b.get("title") or ""),
                                "team": str(b.get("section") or ""),
                                "chief": bool(b.get("chiefOfStaff")),
                                "instance": str(ms.get("instanceId") or ""),
                                "model": str(ms.get("model") or ""),
                                "busy": bool(b.get("busy")),
                                "activity": str(b.get("activity") or "idle"),
                            }
                        )
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            pass

    vps_note = f" · 已绑定 BYO VPS `{secrets.vps_ssh_alias}`" if secrets.vps_ssh_alias else ""
    vps_note_en = f" · BYO VPS `{secrets.vps_ssh_alias}`" if secrets.vps_ssh_alias else ""
    if listening:
        if bot_count is not None:
            team_note = "（已含 Ultra Solo Studio 部门）" if ultra_ready else "（可点下方按钮一键注入 Ultra 部门包）"
            team_note_en = " (Ultra Solo Studio active)" if ultra_ready else " (Click Sync Ultra Bots to apply team)"
            status_txt = f"🟢 运行中 · {bot_count} Bots ({url})"
            status_en = f"🟢 Running · {bot_count} Bots ({url})"
            detail_txt = f"Antigravity 官方 ACP + 多角色派单/卡片审批{team_note}{vps_note}"
            detail_en = f"Antigravity ACP + multi-role dispatch & inline cards{team_note_en}{vps_note_en}"
        elif cli is None:
            status_txt = f"🟢 运行中 ({url})"
            status_en = f"🟢 Running ({url})"
            detail_txt = f"桌面端运行中（未检测到 openmausbot CLI，命令行切池/配对已隐藏，可直接打开控制台）{vps_note}"
            detail_en = f"Desktop app running (openmausbot CLI not found; CLI actions hidden—use Open UI){vps_note_en}"
        else:
            status_txt = f"🟢 运行中 ({url})"
            status_en = f"🟢 Running ({url})"
            detail_txt = f"可选增强已启动；可点击同步精简部门包（仅 Ultra Chief + VPS Scout）{vps_note}"
            detail_en = f"Optional Harness ready; click Sync Ultra Bots for 2-bot team{vps_note_en}"
        return {
            "id": "openmausbot",
            "name": "OpenMausBot (可选扩展 · 后台巡检/VPS)",
            "name_en": "OpenMausBot (Optional Routines / VPS)",
            "repo": "milind-soni/OpenMausBot",
            "tone": "live",
            "status": status_txt,
            "status_en": status_en,
            "detail": detail_txt,
            "detail_en": detail_en,
            "action_url": url,
            "installed": True,
            "cli_installed": bool(cli),
            "bot_count": bot_count,
            "ultra_ready": ultra_ready,
            "bots": bot_roster,
        }

    return {
        "id": "openmausbot",
        "name": "OpenMausBot (可选扩展 · 后台巡检/VPS)",
        "name_en": "OpenMausBot (Optional Routines / VPS)",
        "repo": "milind-soni/OpenMausBot",
        "tone": "muted",
        "status": "⚪ 可选扩展 · 未启用",
        "status_en": "⚪ Optional Add-on · Off",
        "detail": f"日常用 T3 Code + Fleet-Hub 即已完备；仅需无人值守巡检或 BYO VPS 时再运行 `ultra maus install`{vps_note}",
        "detail_en": f"Optional: T3 Code + Fleet-Hub already cover daily work; run `ultra maus install` only for unattended routines/VPS{vps_note_en}",
        "action_url": "",
        "installed": True,
        "cli_installed": bool(cli),
        "bot_count": 0,
        "ultra_ready": False,
        "bots": [],
    }


def _fetch_available_antigravity_models(cli: Path, url: str) -> set[str]:
    try:
        proc = subprocess.run(
            wrap_cmd([str(cli), "models", "--json", "--url", url]),
            capture_output=True,
            text=True,
            timeout=5,
            env=_no_proxy_env(),
        )
        if proc.returncode == 0 and proc.stdout.strip():
            payload = json.loads(proc.stdout)
            for inst in payload.get("instances") or []:
                if isinstance(inst, dict) and inst.get("instanceId") == "antigravity":
                    opts = (inst.get("models") or {}).get("options") or []
                    return {str(o.get("id")) for o in opts if isinstance(o, dict) and o.get("id")}
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        pass
    return set()


def _pick_model(desired: str, available_agy: set[str]) -> str:
    if not available_agy or not desired.startswith("antigravity/"):
        return desired
    model_id = desired.split("/", 1)[1]
    if model_id in available_agy:
        return desired
    for fallback in ("claude-opus-5-5", "claude-sonnet-5-5", "gemini-4-neon", "gemini-3.8-flash"):
        if fallback in available_agy:
            return f"antigravity/{fallback}"
    return desired


def rebalance_openmausbot_models(
    secrets: RuntimeSecrets,
    routing: dict[str, Any],
    *,
    dry_run: bool = False,
    include_other_engines: bool = False,
) -> tuple[bool, str, list[dict[str, str]]]:
    """Rebalance idle OpenMausBot bots across Antigravity pools based on live quota routing."""
    cli = resolve_tool_bin("openmausbot")
    if cli is None:
        return (
            False,
            "未安装可选扩展 OpenMausBot CLI（日常单用 T3 Code 无需切池，直接在会话中选择推荐模型即可；如需后台哨兵 Bot 可运行 ./scripts/bootstrap.sh --with-mausbot）",
            [],
        )

    url = secrets.openmausbot_url.rstrip("/")
    try:
        proc = subprocess.run(
            wrap_cmd([str(cli), "bots", "--json", "--url", url]),
            capture_output=True,
            text=True,
            timeout=5,
            env=_no_proxy_env(),
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"读取 OpenMausBot 列表失败: {exc}", []

    if proc.returncode != 0 or not proc.stdout.strip():
        return False, f"OpenMausBot 未就绪 ({proc.stderr.strip() or url})", []

    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return False, f"解析 OpenMausBot 响应失败: {exc}", []

    bots = raw.get("bots", raw) if isinstance(raw, dict) else raw
    if not isinstance(bots, list) or not bots:
        return False, "OpenMausBot 当前没有可调度的 Bot", []

    available_agy = _fetch_available_antigravity_models(cli, url)
    coding_target = _pick_model(str(routing.get("recommended_coding_model") or "antigravity/claude-opus-5-5"), available_agy)
    triage_target = _pick_model(str(routing.get("recommended_triage_model") or "antigravity/claude-sonnet-5-5"), available_agy)

    changes: list[dict[str, str]] = []
    skipped_busy: list[str] = []
    for b in bots:
        if not isinstance(b, dict):
            continue
        name = str(b.get("name") or "").strip()
        if not name:
            continue
        if b.get("busy") or str(b.get("activity") or "idle") != "idle":
            skipped_busy.append(name)
            continue
        ms = b.get("modelSelection") or {}
        inst = str(ms.get("instanceId") or "")
        model = str(ms.get("model") or "")
        current = f"{inst}/{model}" if inst and model else model

        if inst and inst != "antigravity" and not include_other_engines:
            continue

        title_low = f"{name} {b.get('title') or ''}".lower()
        is_coding_role = name in ("Ultra Architect", "Mini-Game Factory") or any(
            kw in title_low for kw in ("architect", "coder", "engineer", "builder", "game")
        )
        desired = coding_target if is_coding_role else triage_target

        if current == desired:
            continue

        if not dry_run:
            cmd = wrap_cmd([str(cli), "set-model", name, "--model", desired, "--url", url])
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, env=_no_proxy_env())
            if res.returncode != 0:
                err_txt = (res.stderr or res.stdout or "").strip()
                return False, f"切换 {name} 至 {desired} 失败: {err_txt}", changes

        changes.append({"bot": name, "from": current or "(unset)", "to": desired})

    if not changes:
        busy_note = f"（跳过正在执行任务的 Bot: {', '.join(skipped_busy)}）" if skipped_busy else ""
        return True, f"所有闲置 Antigravity Bot 已处于最优池位 ({coding_target} / {triage_target}){busy_note}", []

    prefix = "[Dry-Run] 计划调整" if dry_run else "已按实时余量重平衡"
    summary = ", ".join(f"{c['bot']}: {c['from']} → {c['to']}" for c in changes)
    return True, f"{prefix} {len(changes)} 个 Bot：{summary}", changes


def render_team_yaml() -> Path:
    """Render portable team.template.yaml with resolved local paths into state/."""
    template_path = HUB_ROOT / "teams" / "ultra-solo-studio" / "team.template.yaml"
    skill_path = HUB_ROOT / "teams" / "ultra-solo-studio" / "skills" / "ultra-quota-advisor" / "SKILL.md"
    web_skill_path = HUB_ROOT / "teams" / "ultra-solo-studio" / "skills" / "gemini-web-research" / "SKILL.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Missing team template: {template_path}")

    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    raw = template_path.read_text(encoding="utf-8")
    rendered = (
        raw.replace("{{WORKSPACE_ROOT}}", str(WORKSPACE_ROOT))
        .replace("{{PROJECTS_ROOT}}", str(PROJECTS_ROOT))
        .replace("{{SKILL_PATH}}", str(skill_path))
        .replace("{{WEB_SKILL_PATH}}", str(web_skill_path))
    )
    out_path = STATE_DIR / "ultra-solo-studio.rendered.yaml"
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


def apply_ultra_team(secrets: RuntimeSecrets) -> tuple[bool, str]:
    """Apply the Ultra Solo Studio team pack to the running OpenMausBot workspace."""
    cli = resolve_tool_bin("openmausbot")
    if cli is None:
        return False, "未找到 `openmausbot` CLI，请先运行 `./scripts/bootstrap.sh --with-wheels` 或 `npm install -g openmausbot`"

    url = secrets.openmausbot_url.rstrip("/")
    rendered_path = render_team_yaml()
    try:
        proc = subprocess.run(
            wrap_cmd([str(cli), "team", "apply", str(rendered_path), "--prune", "--url", url]),
            capture_output=True,
            text=True,
            timeout=30,
            env=_no_proxy_env(),
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"注入 Ultra 部门包失败: {exc}"

    output = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return False, f"OpenMausBot team apply 返回退出码 {proc.returncode}: {output or '请确认 `ultra maus install` 服务已启动'}"

    vps_hint = (
        f"；可在 OpenMausBot → Settings → Other services → Self-hosted VPS 填入 SSH 别名 `{secrets.vps_ssh_alias}` 让 VPS Cloud Scout 挂载云端桌面"
        if secrets.vps_ssh_alias
        else ""
    )
    summary = output.splitlines()[-1] if output else "Ultra Solo Studio (2-Bot Sentinel Pack) 已同步"
    return True, f"已同步 Ultra Solo Studio 部门包至 {url}（{summary}）{vps_hint}"


def create_mausbot_pair_link(secrets: RuntimeSecrets) -> tuple[bool, str, str]:
    """Generate a one-time pairing code / URL for browser or phone companion."""
    cli = resolve_tool_bin("openmausbot")
    if cli is None:
        return False, "未找到 `openmausbot` CLI", ""
    url = secrets.openmausbot_url.rstrip("/")
    port = _resolve_port(url, 8799)
    data_dir = WORKSPACE_ROOT / "tools" / "openmausbot-home"
    env = _no_proxy_env()
    env["OMB_DATA_DIR"] = str(data_dir)
    env["OMB_PORT"] = str(port)
    try:
        proc = subprocess.run(
            wrap_cmd([str(cli), "pair", "--ttl", "24h"]),
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        out = (proc.stdout or proc.stderr or "").strip()
        url_match = re.search(r"https?://[^\s]+/pair#code=[A-Z0-9-]+", out)
        code_match = re.search(r"\b([A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4})\b", out)
        pair_url = url_match.group(0) if url_match else (f"{url}/pair#code={code_match.group(1)}" if code_match else "")
        return proc.returncode == 0, out or f"exit={proc.returncode}", pair_url
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"生成配对码失败: {exc}", ""


def _resolve_port(url: str, default: int = 8799) -> int:
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.port or default
    except ValueError:
        return default


def _build_node_path_env() -> str:
    entries: list[str] = []
    node_bin = shutil.which("node")
    if node_bin:
        entries.append(str(Path(node_bin).resolve().parent))
    for candidate in (
        str(Path.home() / ".local" / "bin"),
        str(WORKSPACE_ROOT / "tools" / "npm-global" / "bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ):
        if candidate not in entries:
            entries.append(candidate)
    return ":".join(entries)


def manage_mausbot_service(action: str) -> tuple[bool, str]:
    """Install, check, restart, or uninstall the headless OpenMausBot serve daemon."""
    sys_name = platform.system()
    if sys_name == "Darwin":
        return _macos_mausbot_action(action)
    if sys_name == "Linux":
        return _linux_mausbot_action(action)
    return False, f"Unsupported OS for OpenMausBot service installer: {sys_name}"


def _macos_mausbot_action(action: str) -> tuple[bool, str]:
    uid = os.getuid()
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{MAUSBOT_LAUNCHD_LABEL}.plist"
    log_dir = Path.home() / ".config" / "openmausbot"
    log_dir.mkdir(parents=True, exist_ok=True)
    desktop_app = Path("/Applications/OpenMausBot.app")

    if action == "status":
        if desktop_app.exists():
            pg = subprocess.run(["pgrep", "-fl", "OpenMausBot.app"], capture_output=True, text=True)
            if pg.returncode == 0:
                return True, f"OpenMausBot.app is running ({desktop_app}) — This-PC CUA & iPhone QR active"
        proc = subprocess.run(["launchctl", "print", f"gui/{uid}/{MAUSBOT_LAUNCHD_LABEL}"], capture_output=True, text=True)
        if proc.returncode == 0:
            lines = [ln for ln in proc.stdout.splitlines() if any(k in ln for k in ("state =", "pid =", "last exit"))]
            return True, f"{MAUSBOT_LAUNCHD_LABEL} ({plist_path}):\n" + "\n".join(lines[:6])
        return False, f"OpenMausBot is not running ({desktop_app if desktop_app.exists() else plist_path})"

    if action == "restart":
        if desktop_app.exists():
            subprocess.run(["osascript", "-e", 'tell application "OpenMausBot" to quit'], capture_output=True, text=True)
            op = subprocess.run(["open", "-a", str(desktop_app)], capture_output=True, text=True)
            return op.returncode == 0, op.stderr.strip() or f"Restarted {desktop_app}"
        proc = subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{MAUSBOT_LAUNCHD_LABEL}"], capture_output=True, text=True)
        return (proc.returncode == 0), proc.stdout.strip() or proc.stderr.strip() or f"Restarted {MAUSBOT_LAUNCHD_LABEL}"

    if action == "uninstall":
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{MAUSBOT_LAUNCHD_LABEL}"], capture_output=True, text=True)
        plist_path.unlink(missing_ok=True)
        return True, f"Uninstalled {MAUSBOT_LAUNCHD_LABEL}"

    if desktop_app.exists():
        # Ensure no conflicting headless LaunchAgent fights the desktop app for port 8799 / data dir lease
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{MAUSBOT_LAUNCHD_LABEL}"], capture_output=True, text=True)
        plist_path.unlink(missing_ok=True)
        op = subprocess.run(["open", "-a", str(desktop_app)], capture_output=True, text=True)
        return op.returncode == 0, op.stderr.strip() or f"Launched {desktop_app} (unlocks This-PC CUA & iPhone QR pairing)"

    cli = resolve_tool_bin("openmausbot")
    if cli is None:
        return False, "openmausbot CLI not found; install it first (`npm install -g openmausbot`)."

    data_dir = WORKSPACE_ROOT / "tools" / "openmausbot-home"
    profiles_dir = WORKSPACE_ROOT / "tools" / "openmausbot-profiles"
    data_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    secrets = load_secrets()
    port = _resolve_port(secrets.openmausbot_url, 8799)
    wrapper = resolve_tool_bin("dev-external")
    cmd = [str(cli), "serve", "--port", str(port), "--data-dir", str(data_dir), "--lan", "--no-open", "--no-pair"]
    prog_args = ["/bin/bash", str(wrapper), *cmd] if wrapper else cmd
    args_xml = "\n".join(f"    <string>{arg}</string>" for arg in prog_args)

    proxy_xml = ""
    if secrets.fleet_proxy:
        proxy_xml = (
            f"    <key>HTTP_PROXY</key><string>{secrets.fleet_proxy}</string>\n"
            f"    <key>HTTPS_PROXY</key><string>{secrets.fleet_proxy}</string>\n"
            f"    <key>NO_PROXY</key><string>127.0.0.1,localhost</string>\n"
        )

    plist_text = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{MAUSBOT_LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
{args_xml}
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>{_build_node_path_env()}</string>
    <key>HOME</key><string>{Path.home()}</string>
    <key>OMB_DATA_DIR</key><string>{data_dir}</string>
    <key>OMB_ANTIGRAVITY_NATIVE_CLI</key><string>1</string>
    <key>OMB_DISABLE_ANNOUNCEMENTS</key><string>1</string>
{proxy_xml}  </dict>
  <key>RunAtLoad</key><true/>
  <key>SoftResourceLimits</key><dict><key>NumberOfFiles</key><integer>4096</integer></dict>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>StandardOutPath</key><string>{log_dir / 'boot-service.out.log'}</string>
  <key>StandardErrorPath</key><string>{log_dir / 'boot-service.err.log'}</string>
  <key>WorkingDirectory</key><string>{Path.home()}</string>
</dict>
</plist>
"""
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{MAUSBOT_LAUNCHD_LABEL}"], capture_output=True, text=True)
    plist_path.write_text(plist_text, encoding="utf-8")
    boot = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)], capture_output=True, text=True)
    if boot.returncode != 0:
        return False, f"Failed to load {plist_path}: {boot.stderr.strip()}"
    return True, f"Installed and started {MAUSBOT_LAUNCHD_LABEL} on 127.0.0.1:{port} (data: {data_dir})"


def _linux_mausbot_action(action: str) -> tuple[bool, str]:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_path = unit_dir / MAUSBOT_SYSTEMD_UNIT

    if action == "status":
        proc = subprocess.run(["systemctl", "--user", "status", MAUSBOT_SYSTEMD_UNIT, "--no-pager"], capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout or proc.stderr).strip()

    if action == "restart":
        proc = subprocess.run(["systemctl", "--user", "restart", MAUSBOT_SYSTEMD_UNIT], capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout or proc.stderr).strip() or f"Restarted {MAUSBOT_SYSTEMD_UNIT}"

    if action == "uninstall":
        subprocess.run(["systemctl", "--user", "disable", "--now", MAUSBOT_SYSTEMD_UNIT], capture_output=True, text=True)
        unit_path.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
        return True, f"Uninstalled {MAUSBOT_SYSTEMD_UNIT}"

    cli = resolve_tool_bin("openmausbot")
    if cli is None:
        return False, "openmausbot CLI not found; install it first (`npm install -g openmausbot`)."

    data_dir = WORKSPACE_ROOT / "tools" / "openmausbot-home"
    data_dir.mkdir(parents=True, exist_ok=True)
    secrets = load_secrets()
    port = _resolve_port(secrets.openmausbot_url, 8799)

    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_body = f"""[Unit]
Description=OpenMausBot Harness (Google AI Ultra Maximizer)
After=network-online.target

[Service]
Type=simple
Environment=OMB_DATA_DIR={data_dir}
Environment=OMB_ANTIGRAVITY_NATIVE_CLI=1
Environment=OMB_DISABLE_ANNOUNCEMENTS=1
ExecStart={cli} serve --port {port} --data-dir {data_dir} --lan --no-open --no-pair
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""
    unit_path.write_text(unit_body, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
    en = subprocess.run(["systemctl", "--user", "enable", "--now", MAUSBOT_SYSTEMD_UNIT], capture_output=True, text=True)
    if en.returncode != 0:
        return False, (en.stderr or en.stdout).strip()
    return True, f"Installed and started {MAUSBOT_SYSTEMD_UNIT} on 127.0.0.1:{port}"
