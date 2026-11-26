"""Unit tests for Google AI Ultra Maximizer (Fleet-Hub v2.0) + open-source hygiene checks."""

from __future__ import annotations

import http.client
import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
import unittest

HUB_ROOT = Path(__file__).resolve().parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from fleet_hub.agy_quota_probe import parse_user_status_snapshot
from fleet_hub.approval_md import process_markdown_decisions, render_approval_center
from fleet_hub.bridges import collect_bridge_statuses
from fleet_hub.burn_advisor import build_burn_recommendations, compute_routing_verdict
from fleet_hub.cockpit import CockpitServer
from fleet_hub.config import RuntimeSecrets, mask_email, save_settings_patch
from fleet_hub.db import FleetDB
from fleet_hub.gcp_credits_probe import parse_gcp_credits_table
from fleet_hub.mausbot_bridge import probe_openmausbot, rebalance_openmausbot_models, render_team_yaml
from fleet_hub.sanitizer import parse_inbox_sections, verify_task_assets
from fleet_hub.telemetry import (
    _probe_ai_studio,
    _probe_paid_api,
    collect_cockpit_snapshot,
    invalidate_telemetry_cache,
)


class TestFleetHub(unittest.TestCase):
    def test_parse_inbox_sha256_and_zip_verification(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-test-") as td:
            root = Path(td)
            ai_dir = root / "demo"
            specs_dir = ai_dir / "specs" / "pack"
            specs_dir.mkdir(parents=True)

            zip_path = specs_dir / "bundle.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("hello.txt", "world")

            inbox = ai_dir / "INBOX.md"
            inbox.write_text(
                "<!-- ignore comment -->\n\n"
                "## [2026-11-26] 测试任务\n"
                "请处理 `.ai/specs/pack/bundle.zip`。\n",
                encoding="utf-8",
            )

            items = parse_inbox_sections("demo", inbox)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].title, "测试任务")
            self.assertTrue(items[0].task_id.startswith("demo-20261126-"))

            ok_early, reason_early = verify_task_assets(ai_dir, items[0].raw_markdown, debounce_sec=60)
            self.assertFalse(ok_early)
            self.assertIn("sync_debounce", reason_early)

            ok_ready, reason_ready = verify_task_assets(ai_dir, items[0].raw_markdown, debounce_sec=0)
            self.assertTrue(ok_ready, reason_ready)

            zip_path.write_bytes(b"not-a-zip")
            ok_bad, reason_bad = verify_task_assets(ai_dir, items[0].raw_markdown, debounce_sec=0)
            self.assertFalse(ok_bad)
            self.assertIn("incomplete_zip", reason_bad)

    def test_approval_markdown_revise_checkbox(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-app-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()

            db.upsert_task(
                {
                    "task_id": "demo-20261126-abcd1234",
                    "project": "demo",
                    "project_repo_path": str(root / "repo"),
                    "title": "Demo task",
                    "source_file": "INBOX.md",
                    "content_sha256": "sha-demo-1",
                    "raw_markdown": "body",
                    "pool": "agy_core",
                    "zone": "YELLOW",
                    "status": "AWAITING_APPROVAL",
                    "worktree_path": str(root / "worktrees" / "demo"),
                    "branch_name": "bot/demo",
                    "head_sha": "deadbeef1234",
                    "diff_stat": "1 file changed",
                    "verify_output": "tests passed",
                    "cost_summary": "0-Token",
                }
            )
            md_path = render_approval_center(db, ai_hub, RuntimeSecrets())
            content = md_path.read_text(encoding="utf-8")
            self.assertIn("- [ ] APPROVE <!-- task_id: demo-20261126-abcd1234 -->", content)

            updated = content.replace(
                "- [ ] REVISE: 在此填写修改意见 <!-- task_id: demo-20261126-abcd1234 -->",
                "- [x] REVISE: 请补一条单测 <!-- task_id: demo-20261126-abcd1234 -->",
            )
            md_path.write_text(updated, encoding="utf-8")
            actions = process_markdown_decisions(db, ai_hub)
            self.assertEqual(len(actions), 1)
            task = db.get_task("demo-20261126-abcd1234")
            assert task is not None
            self.assertEqual(task["status"], "REVISE_REQUESTED")
            self.assertEqual(task["revision_note"], "请补一条单测")

    def test_cockpit_health_and_csrf_protection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-http-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            cockpit = CockpitServer(db, ai_hub, port=0)
            port = cockpit.server.server_address[1]
            t = threading.Thread(target=cockpit.serve_forever, daemon=True)
            t.start()
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(data["ok"])
                    self.assertIn("notify_enabled", data)

                req = urllib.request.Request(
                    f"http://127.0.0.1:{port}/api/approve",
                    data=json.dumps({"task_id": "x", "csrf": "wrong"}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 403)
            finally:
                cockpit.shutdown()
                t.join(timeout=2)

    def test_db_fd_stability_and_zero_churn_markdown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-fd-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()

            before_fds = len(os.listdir("/dev/fd"))
            for _ in range(60):
                db.get_quota_ledger()
                db.list_tasks(limit=10)
                db.get_or_create_csrf_token()
            after_fds = len(os.listdir("/dev/fd"))
            self.assertLessEqual(after_fds - before_fds, 2)

            md1 = render_approval_center(db, ai_hub, RuntimeSecrets())
            mtime1 = md1.stat().st_mtime_ns
            time.sleep(0.02)
            md2 = render_approval_center(db, ai_hub, RuntimeSecrets())
            mtime2 = md2.stat().st_mtime_ns
            self.assertEqual(mtime1, mtime2)

    def test_persistent_csrf_and_browser_redirects(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-csrf-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()

            c1 = CockpitServer(db, ai_hub, port=0)
            c2 = CockpitServer(db, ai_hub, port=0)
            self.assertEqual(c1.csrf_token, c2.csrf_token)
            port = c2.server.server_address[1]
            t = threading.Thread(target=c2.serve_forever, daemon=True)
            t.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                conn.request("GET", "/api/approve")
                r_get = conn.getresponse()
                r_get.read()
                self.assertEqual(r_get.status, 302)
                self.assertEqual(r_get.getheader("Location"), "/")

                body = urllib.parse.urlencode({"task_id": "missing", "csrf": "stale"})
                conn.request(
                    "POST",
                    "/api/approve",
                    body=body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                r_post = conn.getresponse()
                r_post.read()
                self.assertEqual(r_post.status, 303)
                loc = r_post.getheader("Location") or ""
                self.assertTrue(loc.startswith("/?ok=0&msg="), loc)
                conn.close()
            finally:
                c1.shutdown()
                c2.shutdown()
                t.join(timeout=2)

    def test_live_telemetry_honesty(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-tel-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()

            with mock.patch("fleet_hub.telemetry.load_secrets", return_value=RuntimeSecrets()):
                paid = _probe_paid_api(db)
                self.assertEqual(paid["badge_tone"], "muted")
                self.assertIsNone(paid["pct"])

            studio = _probe_ai_studio(ai_hub)
            self.assertEqual(studio["badge_tone"], "local")
            self.assertIn("距下次每日重置", studio["primary"])
            self.assertIsNone(studio["pct"])

            c = CockpitServer(db, ai_hub, port=0)
            port = c.server.server_address[1]
            t = threading.Thread(target=c.serve_forever, daemon=True)
            t.start()
            try:
                fake_snap = {
                    "pools": [{"pool": "flow_credits", "title": "Flow", "badge": "🟢", "badge_tone": "live", "primary": "10,050", "detail": "ok", "pct": 100.0}],
                    "advisor": [],
                    "bridges": [],
                    "lens": None,
                }
                with mock.patch("fleet_hub.cockpit.collect_cockpit_snapshot", return_value=fake_snap):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    body = urllib.parse.urlencode({"csrf": c.csrf_token})
                    conn.request(
                        "POST",
                        "/api/refresh-telemetry",
                        body=body,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    r = conn.getresponse()
                    r.read()
                    self.assertEqual(r.status, 303)
                    loc = r.getheader("Location") or ""
                    self.assertTrue(loc.startswith("/?ok=1&msg="), loc)
                    conn.close()
            finally:
                c.shutdown()
                t.join(timeout=2)

    def test_agy_quota_bucket_split_and_burn_advisor(self) -> None:
        sample_us = {
            "email": "demo@example.com",
            "userTier": {"name": "Google AI Ultra"},
            "planStatus": {"planInfo": {"planName": "Pro"}},
            "cascadeModelConfigData": {
                "clientModelConfigs": [
                    {
                        "label": "Gemini 4 Neon (High)",
                        "quotaInfo": {"remainingFraction": 0.2263, "resetTime": "2099-11-30T23:00:00Z"},
                    },
                    {
                        "label": "Claude Opus 5.5 (High)",
                        "quotaInfo": {"remainingFraction": 1.0, "resetTime": "2099-11-26T06:30:00Z"},
                    },
                ]
            },
        }
        snap = parse_user_status_snapshot(sample_us, ls_version="2.35.1")
        self.assertEqual(snap["gemini_weekly"]["remaining_pct"], 22.6)
        self.assertFalse(snap["gemini_weekly"]["is_rolling_5h"])
        self.assertEqual(snap["claude_rolling_5h"]["remaining_pct"], 100.0)
        self.assertEqual(mask_email("alice@example.com", privacy=True), "a***@example.com")

        # Full AI Ultra plan: Gemini 4 & Orchestrator also reset on a 5h rolling clock
        reset_5h = (datetime.now(timezone.utc) + timedelta(hours=4, minutes=55)).strftime("%Y-%m-%dT%H:%M:%SZ")
        full_ultra_us = {
            "email": "demo@example.com",
            "userTier": {"name": "Google AI Ultra"},
            "cascadeModelConfigData": {
                "clientModelConfigs": [
                    {
                        "label": "Gemini 4 Neon (High)",
                        "quotaInfo": {"remainingFraction": 0.998, "resetTime": reset_5h},
                    },
                    {
                        "label": "Orchestrator (Neon)",
                        "quotaInfo": {"remainingFraction": 0.998, "resetTime": reset_5h},
                    },
                    {
                        "label": "Claude Opus 5.5 (High)",
                        "quotaInfo": {"remainingFraction": 1.0, "resetTime": reset_5h},
                    },
                ]
            },
        }
        snap_ultra = parse_user_status_snapshot(full_ultra_us, ls_version="2.35.2")
        self.assertTrue(snap_ultra["gemini_weekly"]["is_rolling_5h"])
        self.assertEqual(snap_ultra["claude_rolling_5h"]["remaining_pct"], 100.0)
        self.assertNotIn("Orchestrator (Neon)", snap_ultra["claude_rolling_5h"]["families"])

        cards = [
            {"pool": "agy_gemini_weekly", "pct": 22.6, "meta": {"reset_text": "4天后重置"}},
            {"pool": "agy_claude_5h", "pct": 100.0, "meta": {"reset_text": "4h 30m 后重置"}},
            {"pool": "flow_credits", "pct": 40.0, "meta": {"credits": 10023.0}},
            {"pool": "colab_cu", "pct": 49.7, "meta": {"balance": 995.0}},
            {"pool": "paid_gemini_api", "badge_tone": "muted"},
        ]
        advice = build_burn_recommendations(cards, lens_stats={"d7_usd": 393.97, "d7_calls": 5479}, now=datetime(2026, 11, 26))
        self.assertGreaterEqual(len(advice), 4)
        self.assertEqual(advice[0]["severity"], "urgent")
        self.assertIn("Claude Opus / Sonnet 5.5", advice[0]["title"])

    def test_bridges_and_apprise_url_derivation(self) -> None:
        sec = RuntimeSecrets(
            telegram_bot_token="123:ABC",
            telegram_chat_id="999",
            fleet_notify_urls="bark://token@host,tgram://123:ABC/999",
        )
        urls = sec.all_notify_urls()
        self.assertEqual(urls, ["bark://token@host", "tgram://123:ABC/999"])
        bridges = collect_bridge_statuses(sec, force=True)
        self.assertEqual({b["id"] for b in bridges}, {"t3code", "openmausbot", "agy_lens", "agent_desktop", "apprise"})

    def test_openmausbot_team_render_and_sync_endpoint(self) -> None:
        rendered = render_team_yaml()
        self.assertTrue(rendered.exists())
        text = rendered.read_text(encoding="utf-8")
        self.assertNotIn("{{WORKSPACE_ROOT}}", text)
        self.assertNotIn("{{PROJECTS_ROOT}}", text)
        self.assertNotIn("{{SKILL_PATH}}", text)
        self.assertNotIn("{{WEB_SKILL_PATH}}", text)
        self.assertIn("Ultra Chief", text)
        self.assertIn("VPS Cloud Scout", text)
        self.assertIn("prune: true", text)
        self.assertTrue((Path(__file__).resolve().parent.parent / "teams" / "ultra-solo-studio" / "skills" / "gemini-web-research" / "SKILL.md").exists())
        # Lean 2-bot optional pack (each has 2 skills + explicit Antigravity 5h model)
        self.assertEqual(text.count("model: antigravity/"), 2)
        self.assertEqual(text.count("- file: "), 4)

        sec = RuntimeSecrets(openmausbot_url="http://127.0.0.1:65531", vps_ssh_alias="my-gcp-vps")
        with mock.patch("fleet_hub.mausbot_bridge.resolve_tool_bin", return_value=Path("/usr/local/bin/openmausbot")), mock.patch(
            "fleet_hub.mausbot_bridge._maus_app_exists", return_value=False
        ):
            card = probe_openmausbot(sec)
            self.assertEqual(card["id"], "openmausbot")
            self.assertEqual(card["tone"], "muted")
            self.assertIn("my-gcp-vps", card["detail"])

        with tempfile.TemporaryDirectory(prefix="fleet-maus-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            c = CockpitServer(db, ai_hub, port=0)
            port = c.server.server_address[1]
            t = threading.Thread(target=c.serve_forever, daemon=True)
            t.start()
            try:
                fake_snap = {
                    "pools": [],
                    "advisor": [],
                    "bridges": [{"id": "openmausbot", "name": "OpenMausBot", "tone": "live", "status": "ok", "detail": "5 bots", "action_url": "http://127.0.0.1:8799"}],
                    "lens": None,
                }
                with mock.patch("fleet_hub.cockpit.collect_cockpit_snapshot", return_value=fake_snap), mock.patch(
                    "fleet_hub.cockpit.apply_ultra_team", return_value=(True, "synced 5 bots")
                ):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    conn.request("GET", "/api/sync-maus-team")
                    r_get = conn.getresponse()
                    r_get.read()
                    self.assertEqual(r_get.status, 302)

                    conn.request("GET", "/?lang=en&privacy=1")
                    r_ui = conn.getresponse()
                    html_txt = r_ui.read().decode("utf-8")
                    self.assertEqual(r_ui.status, 200)
                    self.assertIn("/api/sync-maus-team", html_txt)
                    self.assertIn("/api/maus-pair", html_txt)

                    body = urllib.parse.urlencode({"csrf": c.csrf_token})
                    conn.request("POST", "/api/sync-maus-team", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    r_post = conn.getresponse()
                    r_post.read()
                    self.assertEqual(r_post.status, 303)

                    with mock.patch("fleet_hub.cockpit.create_mausbot_pair_link", return_value=(True, "ok", "http://127.0.0.1:8799/pair#code=AAAA-BBBB-CCCC")):
                        conn.request("POST", "/api/maus-pair", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        r_pair = conn.getresponse()
                        r_pair.read()
                        self.assertEqual(r_pair.status, 303)
                        self.assertEqual(r_pair.getheader("Location"), "http://127.0.0.1:8799/pair#code=AAAA-BBBB-CCCC")

                    with mock.patch("fleet_hub.cockpit.create_t3_pair_link", return_value=(True, "ok", "http://127.0.0.1:3773/pair#token=FRESH123456")):
                        conn.request("POST", "/api/t3-pair", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
                        r_t3 = conn.getresponse()
                        r_t3.read()
                        self.assertEqual(r_t3.status, 303)
                        self.assertEqual(r_t3.getheader("Location"), "http://127.0.0.1:3773/pair#token=FRESH123456")
                    conn.close()
            finally:
                c.shutdown()
                t.join(timeout=2)

    def test_paid_api_50_budget_and_settings_endpoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fleet-cred-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            sec_file = root / "secrets.env"
            sec_file.write_text("# comment\nGEMINI_PAID_API_KEY=keep-me-secret\n", encoding="utf-8")

            # Uncalibrated budget (0.0) must not guess $100
            sec_uncal = RuntimeSecrets(gemini_paid_api_key="k", paid_api_monthly_usd=0.0)
            with mock.patch("fleet_hub.telemetry.load_secrets", return_value=sec_uncal):
                card_uncal = _probe_paid_api(db)
                self.assertEqual(card_uncal["badge_tone"], "local")
                self.assertIsNone(card_uncal["pct"])

            # Calibrated $50 budget + $11.50 external spend -> $38.50 left, 77.0%
            sec_50 = RuntimeSecrets(gemini_paid_api_key="k", paid_api_monthly_usd=50.0, paid_api_external_used_usd=11.5)
            with mock.patch("fleet_hub.telemetry.load_secrets", return_value=sec_50):
                card_50 = _probe_paid_api(db)
                self.assertEqual(card_50["primary"], "剩余 $38.50 / $50")
                self.assertAlmostEqual(card_50["pct"], 77.0, places=2)

            # save_settings_patch preserves secrets when empty
            save_settings_patch({"PAID_API_MONTHLY_USD": "50", "FLEET_PROXY": "http://127.0.0.1:1082"}, sec_file)
            saved_text = sec_file.read_text(encoding="utf-8")
            self.assertIn("GEMINI_PAID_API_KEY=keep-me-secret", saved_text)
            self.assertIn("PAID_API_MONTHLY_USD=50", saved_text)

            # Cockpit POST /api/settings + bilingual rendering
            c = CockpitServer(db, ai_hub, port=0)
            port = c.server.server_address[1]
            t = threading.Thread(target=c.serve_forever, daemon=True)
            t.start()
            try:
                fake_snap = {"pools": [], "advisor": [], "bridges": [], "lens": None}
                with mock.patch("fleet_hub.cockpit.save_settings_patch") as p_save, mock.patch(
                    "fleet_hub.cockpit.collect_cockpit_snapshot", return_value=fake_snap
                ):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    body = urllib.parse.urlencode(
                        {
                            "csrf": c.csrf_token,
                            "lang": "en",
                            "privacy": "1",
                            "PAID_API_MONTHLY_USD": "50",
                            "PAID_API_EXTERNAL_USED_USD": "0",
                            "GEMINI_PAID_API_KEY": "",
                        }
                    )
                    conn.request(
                        "POST",
                        "/api/settings",
                        body=body,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    r_set = conn.getresponse()
                    r_set.read()
                    self.assertEqual(r_set.status, 303)
                    set_loc = r_set.getheader("Location") or ""
                    self.assertIn("lang=en", set_loc)
                    self.assertIn("privacy=1", set_loc)
                    p_save.assert_called_once()
                    # Blank password input must not overwrite stored key
                    self.assertNotIn("GEMINI_PAID_API_KEY", p_save.call_args[0][0])

                    for lang_q, marker in [("en", "Ultra Burn Advisor"), ("zh", "算力榨干参谋")]:
                        conn.request("GET", f"/?lang={lang_q}&privacy=1")
                        r_lang = conn.getresponse()
                        html_txt = r_lang.read().decode("utf-8")
                        self.assertEqual(r_lang.status, 200)
                        self.assertIn(marker, html_txt)
                    conn.close()
            finally:
                c.shutdown()
                t.join(timeout=2)

    def test_gcp_credits_table_parser_and_sync_endpoint(self) -> None:
        headers = [
            "Credit name",
            "Status",
            "Percent remaining",
            "Remaining value",
            "Original value",
            "Type",
            "Credit ID",
            "Usage scope",
            "Start date",
            "End date",
        ]
        rows = [
            ["Google Developer Program benefit", "Available", "100%", "$40.00", "$40.00", "One-time", "c1", "All", "November 24, 2026", "November 24, 2027"],
            ["Google Developer Program benefit", "Available", "74%", "$7.35", "$10.00", "One-time", "c2", "All", "January 29, 2026", "January 29, 2027"],
            ["Google Developer Program benefit", "Available", "100%", "$10.00", "$10.00", "One-time", "c3", "All", "July 2, 2026", "July 2, 2027"],
            ["Welcome credit", "Expired", "—", "$298.01", "$300.00", "One-time", "c4", "Free trial", "December 1, 2025", "January 9, 2026"],
        ]
        parsed = parse_gcp_credits_table(headers, rows, now=datetime(2026, 11, 26))
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["active_grants_count"], 3)
        self.assertAlmostEqual(parsed["remaining_total"], 57.35, places=2)
        self.assertAlmostEqual(parsed["original_total"], 60.0, places=2)
        self.assertAlmostEqual(parsed["used_total"], 2.65, places=2)
        self.assertEqual(parsed["earliest_grant"]["end_date"], "2027-01-29")

        with tempfile.TemporaryDirectory(prefix="fleet-gcp-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            db.set_meta("telemetry_gcp_credits_json", json.dumps(parsed, ensure_ascii=False))
            card = _probe_paid_api(db)
            self.assertEqual(card["primary"], "剩余 $57.35 / $60.00")
            self.assertIn("总已扣 $2.65", card["detail"])

            c = CockpitServer(db, ai_hub, port=0)
            port = c.server.server_address[1]
            t = threading.Thread(target=c.serve_forever, daemon=True)
            t.start()
            try:
                fake_snap = {"pools": [card], "advisor": [], "bridges": [], "lens": None}
                with mock.patch("fleet_hub.cockpit.collect_cockpit_snapshot", return_value=fake_snap), mock.patch(
                    "fleet_hub.cockpit.sync_gcp_credits_live", return_value=(True, "ok", parsed)
                ):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                    conn.request("GET", "/?lang=zh&privacy=1")
                    r_html = conn.getresponse()
                    html_txt = r_html.read().decode("utf-8")
                    self.assertEqual(r_html.status, 200)
                    self.assertIn("/api/sync-gcp-credits", html_txt)
                    self.assertIn("2027-01-29", html_txt)

                    body = urllib.parse.urlencode({"csrf": c.csrf_token})
                    conn.request("POST", "/api/sync-gcp-credits", body=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    r_post = conn.getresponse()
                    r_post.read()
                    self.assertEqual(r_post.status, 303)
                    conn.close()
            finally:
                c.shutdown()
                t.join(timeout=2)

    def test_open_source_hygiene_no_personal_literals(self) -> None:
        """Fail if any hardcoded user home paths, personal Gmail addresses, LAN IPs, or API keys exist."""
        allowed_exts = (".py", ".md", ".toml", ".example", ".sh", ".yml", ".yaml", "")
        checks = (
            ("hardcoded /Users/<user>", re.compile(r"/Users/(?!<|\{|you|your|alice|demo|runner)[A-Za-z0-9._-]+")),
            ("leaked token/key", re.compile(r"\b(?:AIzaS[y][A-Za-z0-9_-]{10,}|gh[p]_[A-Za-z0-9]{10,}|sk-pro[j]-[A-Za-z0-9_-]{10,})\b")),
            ("private LAN IP", re.compile(r"\b192\.168\.\d+\.\d+\b")),
        )
        gmail_re = re.compile(r"[A-Za-z0-9._%+-]+@gmail\.com", re.IGNORECASE)
        for path in HUB_ROOT.rglob("*"):
            if path.is_dir():
                continue
            if any(part in (".git", "state", "logs", "__pycache__") for part in path.parts):
                continue
            if path.suffix not in allowed_exts:
                continue
            if path.name.startswith("fleet.") or path.suffix == ".sqlite":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, pat in checks:
                self.assertIsNone(pat.search(text), f"{label} found in {path}")
            for email in gmail_re.findall(text):
                low = email.lower()
                self.assertTrue(
                    low == "you@gmail.com" or low.endswith("-you@gmail.com"),
                    f"personal gmail found in {path}: {email}",
                )

    def test_routing_verdict_and_telemetry_cache_by_privacy(self) -> None:
        cards_harvest = [
            {"pool": "agy_gemini_weekly", "pct": 11.7},
            {"pool": "agy_claude_5h", "pct": 100.0},
        ]
        v_harvest = compute_routing_verdict(cards_harvest, lens_stats={"d7_usd": 400.0}, now=datetime(2026, 11, 26))
        self.assertEqual(v_harvest["mode"], "5h_harvest")
        self.assertEqual(v_harvest["recommended_coding_model"], "antigravity/claude-opus-5-5")
        self.assertTrue(v_harvest["wakeup_recommended"])
        self.assertGreater(v_harvest["lens_roi_x"], 1.0)

        v_low = compute_routing_verdict(
            [{"pool": "agy_gemini_weekly", "pct": 12.0}, {"pool": "agy_claude_5h", "pct": 5.0}],
            now=datetime(2026, 11, 26),
        )
        self.assertEqual(v_low["mode"], "conserve_weekly")
        self.assertEqual(v_low["recommended_coding_model"], "antigravity/gemini-3.8-flash")

        with tempfile.TemporaryDirectory(prefix="fleet-cache-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            invalidate_telemetry_cache()
            with (
                mock.patch("fleet_hub.telemetry.probe_antigravity_quotas", return_value=([], {"lens": None})) as p_agy,
                mock.patch("fleet_hub.telemetry._probe_colab", return_value={"pool": "colab_cu", "title": "C", "badge": "ok", "badge_tone": "live", "primary": "1", "detail": "d", "pct": 50.0}),
                mock.patch("fleet_hub.telemetry._probe_storage", return_value={"pool": "gdrive_bus", "title": "G", "badge": "ok", "badge_tone": "live", "primary": "1", "detail": "d", "pct": 10.0}),
                mock.patch("fleet_hub.telemetry._probe_flow_genie", return_value={"pool": "flow_credits", "title": "F", "badge": "ok", "badge_tone": "live", "primary": "1", "detail": "d", "pct": 50.0}),
                mock.patch("fleet_hub.telemetry.collect_bridge_statuses", return_value=[]),
            ):
                collect_cockpit_snapshot(db, ai_hub, privacy=False)
                collect_cockpit_snapshot(db, ai_hub, privacy=False)
                self.assertEqual(p_agy.call_count, 1)
                collect_cockpit_snapshot(db, ai_hub, privacy=True)
                self.assertEqual(p_agy.call_count, 2)
                invalidate_telemetry_cache()
                collect_cockpit_snapshot(db, ai_hub, privacy=False)
                self.assertEqual(p_agy.call_count, 3)

    def test_rebalance_openmausbot_and_wakeup_endpoints(self) -> None:
        sec = RuntimeSecrets(openmausbot_url="http://127.0.0.1:8799")
        bots_payload = {
            "bots": [
                {"name": "Ultra Chief", "busy": False, "activity": "idle", "modelSelection": {"instanceId": "antigravity", "model": "gemini-3.8-flash"}},
                {"name": "Ultra Architect", "busy": False, "activity": "idle", "modelSelection": {"instanceId": "antigravity", "model": "claude-opus-5-5"}},
                {"name": "Flow & Colab Director", "busy": True, "activity": "thinking", "modelSelection": {"instanceId": "antigravity", "model": "gemini-4-carbon"}},
                {"name": "Mini-Game Factory", "busy": False, "activity": "idle", "modelSelection": {"instanceId": "codex", "model": "gpt-6.2-sol"}},
            ]
        }
        models_payload = {
            "instances": [
                {"instanceId": "antigravity", "models": {"options": [{"id": "claude-opus-5-5"}, {"id": "claude-sonnet-5-5"}, {"id": "gemini-3.8-flash"}]}}
            ]
        }
        routing = {"mode": "5h_harvest", "recommended_coding_model": "antigravity/claude-opus-5-5", "recommended_triage_model": "antigravity/claude-sonnet-5-5"}

        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            calls.append(cmd)
            joined = " ".join(cmd)
            if " bots " in joined:
                return mock.Mock(returncode=0, stdout=json.dumps(bots_payload), stderr="")
            if " models " in joined:
                return mock.Mock(returncode=0, stdout=json.dumps(models_payload), stderr="")
            return mock.Mock(returncode=0, stdout="ok", stderr="")

        with mock.patch("fleet_hub.mausbot_bridge.resolve_tool_bin", return_value=Path("/usr/local/bin/openmausbot")), mock.patch(
            "fleet_hub.mausbot_bridge.subprocess.run", side_effect=fake_run
        ):
            ok, msg, changes = rebalance_openmausbot_models(sec, routing)
            self.assertTrue(ok, msg)
            # Only Ultra Chief (idle + wrong model) should be switched; Flow Director is busy, Mini-Game is codex
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]["bot"], "Ultra Chief")
            self.assertEqual(changes[0]["to"], "antigravity/claude-sonnet-5-5")

        with tempfile.TemporaryDirectory(prefix="fleet-ops-") as td:
            root = Path(td)
            db = FleetDB(root / "test.sqlite")
            ai_hub = root / "AI-Projects"
            ai_hub.mkdir()
            c = CockpitServer(db, ai_hub, port=0)
            port = c.server.server_address[1]
            t = threading.Thread(target=c.serve_forever, daemon=True)
            t.start()
            try:
                fake_snap = {
                    "pools": [
                        {
                            "pool": "agy_claude_5h",
                            "title": "5h 中文",
                            "title_en": "Antigravity Claude 5h Rolling",
                            "badge": "live",
                            "badge_en": "Live LS RPC",
                            "badge_tone": "live",
                            "primary": "100%",
                            "primary_en": "100.0% left",
                            "detail": "ok",
                            "detail_en": "independent 5h clock",
                            "pct": 100.0,
                        }
                    ],
                    "advisor": [
                        {
                            "severity": "opportunity",
                            "pool": "5h 池",
                            "pool_en": "Claude 5.5 5h Rolling",
                            "title": "中文建议",
                            "title_en": "Claude 5.5 is 100% idle",
                            "action": "中文动作",
                            "action_en": "Switch idle bots to Claude 5.5",
                            "command": "ultra wakeup",
                        }
                    ],
                    "routing": routing,
                    "bridges": [
                        {
                            "id": "openmausbot",
                            "name": "OpenMausBot",
                            "name_en": "OpenMausBot (milind-soni/OpenMausBot)",
                            "tone": "live",
                            "status": "运行中",
                            "status_en": "Running 2 Bots",
                            "detail": "中文详情",
                            "detail_en": "Antigravity ACP active",
                            "action_url": "http://127.0.0.1:8799",
                            "bots": [{"name": "Ultra Chief", "instance": "antigravity", "model": "claude-sonnet-5-5", "busy": False}],
                        }
                    ],
                    "lens": {"d7_usd": 410.0, "d7_calls": 5000},
                }
                with mock.patch("fleet_hub.cockpit.collect_cockpit_snapshot", return_value=fake_snap) as p_snap, mock.patch(
                    "fleet_hub.cockpit.run_wakeup_trigger", return_value=(True, "woke up")
                ), mock.patch(
                    "fleet_hub.cockpit.rebalance_openmausbot_models", return_value=(True, "rebalanced 1", [{"bot": "Ultra Chief"}])
                ):
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/state", timeout=5) as resp:
                        st = json.loads(resp.read().decode("utf-8"))
                        self.assertIn("routing", st)
                        self.assertEqual(st["routing"]["mode"], "5h_harvest")

                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/?lang=en&privacy=1", timeout=5) as resp_html:
                        page = resp_html.read().decode("utf-8")
                        self.assertIn("antigravity/claude-sonnet-5-5", page)
                        self.assertIn("Antigravity Claude 5h Rolling", page)
                        self.assertIn("Claude 5.5 is 100% idle", page)
                        self.assertIn("Running 2 Bots", page)
                        self.assertIn("table-wrap", page)
                        self.assertIn("/api/rebalance", page)
                        self.assertIn("/api/wakeup", page)

                    req_wake = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/wakeup",
                        data=json.dumps({"csrf": c.csrf_token}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req_wake, timeout=5) as r_w:
                        self.assertTrue(json.loads(r_w.read().decode("utf-8"))["ok"])

                    req_reb = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/rebalance",
                        data=json.dumps({"csrf": c.csrf_token}).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req_reb, timeout=5) as r_r:
                        res_r = json.loads(r_r.read().decode("utf-8"))
                        self.assertTrue(res_r["ok"])
                        self.assertEqual(len(res_r["changes"]), 1)
                    self.assertTrue(any(call.kwargs.get("force") is True for call in p_snap.call_args_list))
            finally:
                c.shutdown()
                t.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
