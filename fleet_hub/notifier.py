"""Multi-channel passive notifier powered by Apprise (replacing custom polling scripts)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any

from .config import RuntimeSecrets, resolve_tool_bin, wrap_cmd
from .db import FleetDB


def _proxy_env(secrets: RuntimeSecrets) -> dict[str, str]:
    env = dict(os.environ)
    proxy = secrets.fleet_proxy
    if not proxy and secrets.fleet_auto_proxy_port > 0 and not env.get("HTTPS_PROXY"):
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
    return env


def send_notification(secrets: RuntimeSecrets, title: str, body: str) -> tuple[bool, str]:
    """Dispatch notification via `apprise` CLI across all configured channels (Telegram/Bark/Slack/...)."""
    urls = secrets.all_notify_urls()
    if not urls:
        return False, "未配置通知通道（请填写 ~/.config/fleet-hub/secrets.env 中的 FLEET_NOTIFY_URLS 或 TELEGRAM_*）"

    apprise_bin = resolve_tool_bin("apprise")
    if apprise_bin is not None:
        cmd = wrap_cmd([str(apprise_bin), "-t", title, "-b", body, *urls])
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=_proxy_env(secrets))
            if proc.returncode == 0:
                return True, f"Apprise 已推送至 {len(urls)} 个通道"
            err = (proc.stderr or proc.stdout).strip()
            return False, f"Apprise 推送失败: {err[:300]}"
        except (subprocess.SubprocessError, OSError) as exc:
            return False, f"Apprise 执行异常: {exc}"

    # Fallback direct Telegram Bot API only if apprise is absent and Telegram creds are provided.
    if secrets.telegram_enabled:
        url = f"https://api.telegram.org/bot{secrets.telegram_bot_token}/sendMessage"
        data = json.dumps({"chat_id": secrets.telegram_chat_id, "text": f"{title}\n\n{body}"}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok")), "Telegram 推送成功" if res.get("ok") else str(res)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return False, f"Telegram 推送失败: {exc}"

    return False, "未找到 apprise CLI，请安装 `uv tool install apprise`"


def send_test_message(secrets: RuntimeSecrets) -> tuple[bool, str]:
    """Send a connectivity smoke-test notification."""
    return send_notification(
        secrets,
        "Google AI Ultra Maximizer · 测试通知",
        "推送通道连接成功！后续仅在需要审批或配额清零预警时通知；日常交互与手机遥控请直接使用 T3 Code。",
    )


def notify_awaiting_approval(db: FleetDB, secrets: RuntimeSecrets, task: dict[str, Any]) -> bool:
    """Send one passive alert per awaiting task (interactive review lives in T3 Code / Cockpit)."""
    if not secrets.notify_enabled:
        return False
    if int(task.get("tg_message_id") or 0) > 0:
        return False

    summary_diff = (task.get("diff_stat") or "").strip().splitlines()[-1:] or [""]
    body = (
        f"项目: [{task['project']}] {task['title']}\n"
        f"工单: {task['task_id']}\n"
        f"分支: {task['branch_name']} ({task['head_sha'][:8]})\n"
        f"改动: {summary_diff[0][:120]}\n"
        f"驾驶舱: http://127.0.0.1:{secrets.fleet_port} | T3 Code: {secrets.t3code_url}"
    )
    ok, msg = send_notification(secrets, f"🟡 待拍板工单 [{task['project']}]", body)
    if ok:
        db.update_task_fields(task["task_id"], tg_message_id=1)
        db.add_event(task["task_id"], "NOTIFY_SENT", msg)
        return True
    db.add_event(task["task_id"], "NOTIFY_ERR", msg)
    return False
