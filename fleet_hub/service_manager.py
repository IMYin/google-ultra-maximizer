"""Cross-platform background service setup and project bootstrap."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

from .config import (
    ARTIFACTS_ROOT,
    HUB_ROOT,
    PROJECTS_ROOT,
    SECRETS_ENV_PATH,
    WORKTREES_ROOT,
    detect_ai_hub,
    load_secrets,
    resolve_tool_bin,
)

NEW_LAUNCHD_LABEL = "io.ultra-maximizer.daemon"
LEGACY_LAUNCHD_LABEL = f"com.{os.environ.get('USER') or Path.home().name}.fleet-hub"
SYSTEMD_UNIT_NAME = "ultra-maximizer.service"


def init_workspace() -> list[str]:
    """Initialize config secrets.env, workspace directories, and starter AI-Projects registry."""
    notes: list[str] = []
    for d in (PROJECTS_ROOT, WORKTREES_ROOT, ARTIFACTS_ROOT):
        d.mkdir(parents=True, exist_ok=True)
    notes.append(f"Workspace directories ensured under {PROJECTS_ROOT.parent}")

    SECRETS_ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SECRETS_ENV_PATH.exists():
        example = HUB_ROOT / ".env.example"
        content = example.read_text(encoding="utf-8") if example.exists() else "FLEET_PORT=7788\n"
        SECRETS_ENV_PATH.write_text(content, encoding="utf-8")
        os.chmod(SECRETS_ENV_PATH, 0o600)
        notes.append(f"Created config file: {SECRETS_ENV_PATH} (chmod 600)")
    else:
        os.chmod(SECRETS_ENV_PATH, 0o600)
        notes.append(f"Existing config kept: {SECRETS_ENV_PATH}")

    ai_hub = detect_ai_hub()
    ai_hub.mkdir(parents=True, exist_ok=True)
    registry = ai_hub / "_REGISTRY.md"
    if not registry.exists():
        registry.write_text(
            "# AI-Projects Registry\n\n"
            "| 项目名称 | 本地仓库路径 | 云端协同目录 | 状态摘要 | 更新时间 |\n"
            "|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        notes.append(f"Created registry template: {registry}")
    else:
        notes.append(f"AI-Projects hub ready: {ai_hub}")

    return notes


def _detect_macos_plist() -> tuple[str, Path]:
    agents_dir = Path.home() / "Library" / "LaunchAgents"
    legacy_plist = agents_dir / f"{LEGACY_LAUNCHD_LABEL}.plist"
    if legacy_plist.exists():
        return LEGACY_LAUNCHD_LABEL, legacy_plist
    return NEW_LAUNCHD_LABEL, agents_dir / f"{NEW_LAUNCHD_LABEL}.plist"


def _macos_service_action(action: str) -> tuple[bool, str]:
    uid = os.getuid()
    label, plist_path = _detect_macos_plist()
    log_dir = Path.home() / ".config" / "ultra-maximizer"
    if label == LEGACY_LAUNCHD_LABEL:
        log_dir = Path.home() / ".config" / "fleet-hub"
    log_dir.mkdir(parents=True, exist_ok=True)

    if action == "status":
        proc = subprocess.run(["launchctl", "print", f"gui/{uid}/{label}"], capture_output=True, text=True)
        if proc.returncode == 0:
            lines = [ln for ln in proc.stdout.splitlines() if any(k in ln for k in ("state =", "pid =", "last exit"))]
            return True, f"{label} ({plist_path}):\n" + "\n".join(lines[:6])
        return False, f"{label} is not loaded ({plist_path})"

    if action == "restart":
        proc = subprocess.run(["launchctl", "kickstart", "-k", f"gui/{uid}/{label}"], capture_output=True, text=True)
        return (proc.returncode == 0), proc.stdout.strip() or proc.stderr.strip() or f"Restarted {label}"

    if action == "uninstall":
        subprocess.run(["launchctl", "bootout", f"gui/{uid}/{label}"], capture_output=True, text=True)
        plist_path.unlink(missing_ok=True)
        return True, f"Uninstalled {label}"

    # install
    secrets = load_secrets()
    fleet_cli = str(HUB_ROOT / "bin" / "fleet")
    wrapper = resolve_tool_bin("dev-external")
    prog_args = (
        ["/bin/bash", str(wrapper), sys.executable, fleet_cli, "daemon"]
        if wrapper
        else [sys.executable, fleet_cli, "daemon"]
    )
    path_env = os.environ.get("PATH", f"{Path.home() / '.local' / 'bin'}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin")
    proxy_lines = ""
    if secrets.fleet_proxy:
        proxy_lines = (
            f"    <key>HTTP_PROXY</key><string>{secrets.fleet_proxy}</string>\n"
            f"    <key>HTTPS_PROXY</key><string>{secrets.fleet_proxy}</string>\n"
            f"    <key>NO_PROXY</key><string>127.0.0.1,localhost</string>\n"
        )
    args_xml = "\n".join(f"    <string>{arg}</string>" for arg in prog_args)
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{label}</string>
  <key>ProgramArguments</key>
  <array>
{args_xml}
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>{path_env}</string>
{proxy_lines}  </dict>
  <key>RunAtLoad</key><true/>
  <key>SoftResourceLimits</key><dict><key>NumberOfFiles</key><integer>4096</integer></dict>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>StandardOutPath</key><string>{log_dir / 'fleetd.out.log'}</string>
  <key>StandardErrorPath</key><string>{log_dir / 'fleetd.err.log'}</string>
  <key>WorkingDirectory</key><string>{Path.home()}</string>
</dict>
</plist>
"""
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["launchctl", "bootout", f"gui/{uid}/{label}"], capture_output=True, text=True)
    plist_path.write_text(plist_content, encoding="utf-8")
    boot = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)], capture_output=True, text=True)
    if boot.returncode != 0:
        return False, f"Failed to load {plist_path}: {boot.stderr.strip()}"
    return True, f"Installed and started {label} -> {plist_path}"


def _linux_service_action(action: str) -> tuple[bool, str]:
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_path = unit_dir / SYSTEMD_UNIT_NAME

    if action == "status":
        proc = subprocess.run(["systemctl", "--user", "status", SYSTEMD_UNIT_NAME, "--no-pager"], capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout or proc.stderr).strip()

    if action == "restart":
        proc = subprocess.run(["systemctl", "--user", "restart", SYSTEMD_UNIT_NAME], capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout or proc.stderr).strip() or f"Restarted {SYSTEMD_UNIT_NAME}"

    if action == "uninstall":
        subprocess.run(["systemctl", "--user", "disable", "--now", SYSTEMD_UNIT_NAME], capture_output=True, text=True)
        unit_path.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
        return True, f"Uninstalled {SYSTEMD_UNIT_NAME}"

    unit_dir.mkdir(parents=True, exist_ok=True)
    fleet_cli = str(HUB_ROOT / "bin" / "fleet")
    unit_body = f"""[Unit]
Description=Google AI Ultra Maximizer (Fleet-Hub Daemon)
After=network-online.target

[Service]
Type=simple
ExecStart={sys.executable} {fleet_cli} daemon
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""
    unit_path.write_text(unit_body, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, text=True)
    en = subprocess.run(["systemctl", "--user", "enable", "--now", SYSTEMD_UNIT_NAME], capture_output=True, text=True)
    if en.returncode != 0:
        return False, (en.stderr or en.stdout).strip()
    return True, f"Installed and started {SYSTEMD_UNIT_NAME} -> {unit_path}"


def manage_service(action: str) -> tuple[bool, str]:
    """Install, check, restart, or uninstall the background daemon on macOS or Linux."""
    sys_name = platform.system()
    if sys_name == "Darwin":
        return _macos_service_action(action)
    if sys_name == "Linux":
        return _linux_service_action(action)
    return False, f"Unsupported OS for background service installer: {sys_name}"
