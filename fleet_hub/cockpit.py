"""Localhost-only Web Cockpit HTTP server (approvals, live telemetry, calibration settings)."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .approval_md import render_approval_center
from .bridges import GITHUB_REPO_URL, check_github_starred, create_t3_pair_link, run_wakeup_trigger, star_github_repo
from .cockpit_ui import render_cockpit_page
from .config import load_secrets, save_settings_patch
from .db import FleetDB
from .mausbot_bridge import apply_ultra_team, create_mausbot_pair_link, rebalance_openmausbot_models
from .notifier import send_test_message
from .telemetry import collect_cockpit_snapshot, invalidate_telemetry_cache, sync_gcp_credits_live
from .worktree import approve_task, request_revision, resolve_repo_map

NUMERIC_SETTINGS = (
    "PAID_API_MONTHLY_USD",
    "PAID_API_EXTERNAL_USED_USD",
    "FLOW_MONTHLY_CREDITS",
    "COLAB_MONTHLY_CU",
)
TEXT_SETTINGS = (
    "GEMINI_TRIAGE_MODEL",
    "T3CODE_URL",
    "OPENMAUSBOT_URL",
    "VPS_SSH_ALIAS",
    "FLEET_PROXY",
    "FLEET_NOTIFY_URLS",
)
SECRET_SETTINGS = (
    "GEMINI_PAID_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
)


class CockpitServer:
    """Thread-safe wrapper around ThreadingHTTPServer bound strictly to 127.0.0.1."""

    def __init__(self, db: FleetDB, ai_hub: Path, port: int = 7788) -> None:
        self.db = db
        self.ai_hub = ai_hub
        self.port = port
        self.csrf_token = self.db.get_or_create_csrf_token()
        self._serving = False
        self.server = ThreadingHTTPServer(("127.0.0.1", port), self._make_handler())

    def serve_forever(self) -> None:
        self._serving = True
        try:
            self.server.serve_forever()
        finally:
            self._serving = False

    def shutdown(self) -> None:
        if self._serving:
            self.server.shutdown()
        self.server.server_close()

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        cockpit = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def _send_json(self, code: int, data: dict[str, Any]) -> None:
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, code: int, content: str) -> None:
                body = content.encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _redirect(self, location: str, code: int = 303) -> None:
                self.send_response(code)
                self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def _is_same_origin(self) -> bool:
                origin = self.headers.get("Origin", "")
                if origin and not (
                    origin.startswith(f"http://127.0.0.1:{cockpit.port}")
                    or origin.startswith(f"http://localhost:{cockpit.port}")
                ):
                    return False
                return True

            def _read_body(self) -> str:
                if "chunked" in (self.headers.get("Transfer-Encoding", "")).lower():
                    chunks: list[bytes] = []
                    while True:
                        line = self.rfile.readline().strip()
                        if not line:
                            continue
                        size = int(line.split(b";", 1)[0], 16)
                        if size == 0:
                            self.rfile.readline()
                            break
                        chunks.append(self.rfile.read(size))
                        self.rfile.readline()
                    return b"".join(chunks).decode("utf-8", errors="replace")
                length = int(self.headers.get("Content-Length", "0") or 0)
                return self.rfile.read(min(length, 65536)).decode("utf-8", errors="replace")

            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                qs = urllib.parse.parse_qs(parsed.query)
                privacy_q = qs.get("privacy", [""])[0]
                privacy = True if privacy_q == "1" else (False if privacy_q == "0" else None)
                lang_q = qs.get("lang", [""])[0].lower()
                lang = lang_q if lang_q in ("zh", "en") else None

                if parsed.path in (
                    "/api/approve",
                    "/api/revise",
                    "/api/refresh-telemetry",
                    "/api/settings",
                    "/api/notify-test",
                    "/api/sync-gcp-credits",
                    "/api/sync-maus-team",
                    "/api/maus-pair",
                    "/api/wakeup",
                    "/api/rebalance",
                    "/api/github-star-dismiss",
                ):
                    self._redirect("/", code=302)
                    return

                if parsed.path == "/api/health":
                    runtime = load_secrets()
                    self._send_json(
                        200,
                        {
                            "ok": True,
                            "port": cockpit.port,
                            "paid_api_enabled": runtime.paid_api_enabled,
                            "telegram_enabled": runtime.telegram_enabled,
                            "notify_enabled": runtime.notify_enabled,
                            "awaiting_count": len(cockpit.db.list_tasks(status="AWAITING_APPROVAL")),
                        },
                    )
                    return

                if parsed.path == "/api/state":
                    snap = collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, privacy=privacy)
                    self._send_json(
                        200,
                        {
                            "tasks": cockpit.db.list_tasks(limit=50),
                            "pools": snap["pools"],
                            "advisor": snap["advisor"],
                            "routing": snap.get("routing"),
                            "bridges": snap["bridges"],
                            "lens": snap["lens"],
                            "capabilities": snap.get("capabilities"),
                            "repos": list(resolve_repo_map(cockpit.ai_hub).values()),
                            "events": cockpit.db.recent_events(20),
                        },
                    )
                    return

                if parsed.path == "/api/github-star":
                    info = check_github_starred(load_secrets())
                    maturity = cockpit.db.get_usage_maturity()
                    if info.get("starred") is None and maturity["starred_recorded"]:
                        info["starred"] = True
                    info["maturity"] = maturity
                    self._send_json(200, info)
                    return

                if parsed.path == "/":
                    msg = qs.get("msg", [""])[0]
                    ok_flag = qs.get("ok", [""])[0]
                    self._send_html(200, cockpit.render_html(msg=msg, ok_flag=ok_flag, privacy=privacy, lang=lang))
                    return

                self._send_json(404, {"error": "not_found"})

            def do_POST(self) -> None:
                ctype = self.headers.get("Content-Type", "")
                is_json = "application/json" in ctype

                if not self._is_same_origin():
                    if is_json:
                        self._send_json(403, {"ok": False, "error": "forbidden_origin"})
                    else:
                        self._redirect("/?ok=0&msg=" + urllib.parse.quote("非法请求来源"))
                    return

                raw_body = self._read_body()
                if is_json:
                    try:
                        form = json.loads(raw_body)
                    except json.JSONDecodeError:
                        self._send_json(400, {"ok": False, "error": "invalid_json"})
                        return
                else:
                    parsed_qs = urllib.parse.parse_qs(raw_body, keep_blank_values=True)
                    form = {k: v[0] for k, v in parsed_qs.items()}

                def _home_redirect_url(ok_val: str, msg_val: str) -> str:
                    params: list[tuple[str, str]] = [("ok", ok_val), ("msg", msg_val)]
                    lang_val = str(form.get("lang") or "").strip().lower()
                    priv_val = str(form.get("privacy") or "").strip()
                    if not lang_val or not priv_val:
                        ref = self.headers.get("Referer", "")
                        if ref:
                            ref_qs = urllib.parse.parse_qs(urllib.parse.urlparse(ref).query)
                            if not lang_val and ref_qs.get("lang", [""])[0].lower() in ("zh", "en"):
                                lang_val = ref_qs["lang"][0].lower()
                            if not priv_val and ref_qs.get("privacy", [""])[0] in ("0", "1"):
                                priv_val = ref_qs["privacy"][0]
                    if lang_val in ("zh", "en"):
                        params.append(("lang", lang_val))
                    if priv_val in ("0", "1"):
                        params.append(("privacy", priv_val))
                    return "/?" + urllib.parse.urlencode(params)

                expected_csrf = cockpit.db.get_or_create_csrf_token()
                if form.get("csrf") != expected_csrf:
                    if is_json:
                        self._send_json(403, {"ok": False, "error": "invalid_csrf"})
                    else:
                        self._redirect(_home_redirect_url("0", "页面会话已刷新，请重试"))
                    return

                parsed = urllib.parse.urlparse(self.path)
                if parsed.path in (
                    "/api/refresh-telemetry",
                    "/api/wakeup",
                    "/api/sync-gcp-credits",
                    "/api/settings",
                    "/api/approve",
                    "/api/revise",
                    "/api/t3-pair",
                    "/api/maus-pair",
                    "/api/sync-maus-team",
                    "/api/rebalance",
                ):
                    cockpit.db.increment_meta_int("cockpit_user_ops")

                if parsed.path == "/api/refresh-telemetry":
                    invalidate_telemetry_cache()
                    collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    if is_json:
                        self._send_json(200, {"ok": True, "message": "实时探针已刷新"})
                    else:
                        self._redirect(_home_redirect_url("1", "实时探针已刷新（已同步全部算力池与开源轮子状态）"))
                    return

                if parsed.path == "/api/notify-test":
                    ok, msg = send_test_message(load_secrets())
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/sync-gcp-credits":
                    ok, msg, parsed_gcp = sync_gcp_credits_live(cockpit.db)
                    if ok:
                        collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg, "data": parsed_gcp})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/sync-maus-team":
                    ok, msg = apply_ultra_team(load_secrets())
                    invalidate_telemetry_cache()
                    collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/maus-pair":
                    ok, msg, pair_url = create_mausbot_pair_link(load_secrets())
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg, "pair_url": pair_url})
                    elif ok and pair_url:
                        self._redirect(pair_url, code=303)
                    else:
                        self._redirect(_home_redirect_url("0", msg))
                    return

                if parsed.path == "/api/t3-pair":
                    ok, msg, pair_url = create_t3_pair_link(load_secrets())
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg, "pair_url": pair_url})
                    elif ok and pair_url:
                        self._redirect(pair_url, code=303)
                    else:
                        self._redirect(_home_redirect_url("0", msg))
                    return

                if parsed.path == "/api/wakeup":
                    ok, msg = run_wakeup_trigger()
                    invalidate_telemetry_cache()
                    collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/rebalance":
                    snap = collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    ok, msg, changes = rebalance_openmausbot_models(load_secrets(), snap.get("routing") or {})
                    invalidate_telemetry_cache()
                    collect_cockpit_snapshot(cockpit.db, cockpit.ai_hub, force=True)
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg, "changes": changes})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/settings":
                    ok, msg = cockpit.apply_settings_form(form)
                    if is_json:
                        self._send_json(200 if ok else 400, {"ok": ok, "message": msg})
                    else:
                        self._redirect(_home_redirect_url("1" if ok else "0", msg))
                    return

                if parsed.path == "/api/github-star":
                    ok, msg, star_data = star_github_repo(load_secrets())
                    if ok:
                        cockpit.db.set_meta("github_repo_starred", "1")
                        cockpit.db.set_meta("github_star_dismissed", "1")
                        cockpit.db.add_event("cockpit", "GITHUB_STARRED", msg)
                    if is_json:
                        self._send_json(200, {"ok": ok, "message": msg, **star_data})
                    elif ok:
                        self._redirect(_home_redirect_url("1", msg))
                    else:
                        self._redirect(str(star_data.get("fallback_url") or GITHUB_REPO_URL), code=303)
                    return

                if parsed.path == "/api/github-star-dismiss":
                    cockpit.db.set_meta("github_star_dismissed", "1")
                    if is_json:
                        self._send_json(200, {"ok": True})
                    else:
                        self._redirect("/")
                    return

                task_id = str(form.get("task_id", "")).strip()
                if parsed.path == "/api/approve":
                    ok, msg = approve_task(cockpit.db, cockpit.ai_hub, task_id)
                elif parsed.path == "/api/revise":
                    ok, msg = request_revision(cockpit.db, task_id, str(form.get("note", "")))
                else:
                    self._send_json(404, {"ok": False, "error": "not_found"})
                    return

                render_approval_center(cockpit.db, cockpit.ai_hub, load_secrets())
                if is_json:
                    self._send_json(200 if ok else 400, {"ok": ok, "message": msg})
                else:
                    self._redirect(_home_redirect_url("1" if ok else "0", msg))

        return Handler

    def apply_settings_form(self, form: dict[str, Any]) -> tuple[bool, str]:
        """Validate and persist calibration/config edits safely into secrets.env."""
        patch: dict[str, str] = {}
        for key in NUMERIC_SETTINGS:
            if key not in form:
                continue
            raw_val = str(form.get(key) or "").strip()
            if not raw_val:
                patch[key] = ""
                continue
            try:
                num = float(raw_val)
                if num < 0:
                    return False, f"{key} 不能为负数"
                patch[key] = f"{num:g}"
            except ValueError:
                return False, f"{key} 必须是合法数字"

        for key in TEXT_SETTINGS:
            if key in form:
                patch[key] = str(form.get(key) or "").strip()

        for key in SECRET_SETTINGS:
            raw_secret = str(form.get(key) or "").strip()
            if raw_secret:
                patch[key] = raw_secret

        save_settings_patch(patch)
        updated = load_secrets()
        self.db.sync_pool_budget("paid_gemini_api", updated.paid_api_monthly_usd)
        self.db.sync_pool_budget("colab_cu", updated.colab_monthly_cu)
        self.db.sync_pool_budget("flow_credits", updated.flow_monthly_credits)
        invalidate_telemetry_cache()
        collect_cockpit_snapshot(self.db, self.ai_hub, force=True)
        return True, f"配置已保存并热生效（本月 API 赠金总额: ${updated.paid_api_monthly_usd:g}，外部已用校准: ${updated.paid_api_external_used_usd:g}）"

    def render_html(
        self,
        msg: str = "",
        ok_flag: str = "",
        privacy: bool | None = None,
        lang: str | None = None,
    ) -> str:
        runtime = load_secrets()
        use_privacy = runtime.fleet_privacy_mode if privacy is None else privacy
        use_lang = runtime.ui_lang if lang is None else lang
        csrf_token = self.db.get_or_create_csrf_token()
        awaiting = self.db.list_tasks(status="AWAITING_APPROVAL", limit=20)
        others = [t for t in self.db.list_tasks(limit=30) if t["status"] != "AWAITING_APPROVAL"]
        snap = collect_cockpit_snapshot(self.db, self.ai_hub, privacy=use_privacy)
        repos = list(resolve_repo_map(self.ai_hub).values())
        return render_cockpit_page(
            runtime=runtime,
            csrf_token=csrf_token,
            awaiting=awaiting,
            others=others,
            pools=snap["pools"],
            advisor=snap["advisor"],
            routing=snap.get("routing"),
            lens=snap.get("lens"),
            bridges=snap["bridges"],
            capabilities=snap.get("capabilities"),
            repos=repos,
            msg=msg,
            ok_flag=ok_flag,
            privacy=use_privacy,
            lang=use_lang,
        )
