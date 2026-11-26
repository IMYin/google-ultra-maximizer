"""Main 0-token watcher daemon and single-scan orchestrator for fleet-hub."""

from __future__ import annotations

import json
import resource
import signal
import threading
import time
from pathlib import Path
from typing import Any

from .approval_md import process_markdown_decisions, render_approval_center
from .config import detect_ai_hub, load_secrets
from .db import FleetDB
from .sanitizer import parse_inbox_sections, sanitize_gdoc_pointers, verify_task_assets
from .notifier import notify_awaiting_approval
from .telemetry import collect_cockpit_snapshot
from .triage import check_monthly_harvesters, triage_task
from .worktree import create_isolated_worktree, resolve_repo_map
from .cockpit import CockpitServer


def scan_once(db: FleetDB, ai_hub: Path) -> dict[str, Any]:
    """Run one deterministic scan across AI-Projects with 0 LLM tokens unless Paid API key is set."""
    secrets = load_secrets()
    repo_map = resolve_repo_map(ai_hub)

    # 1. Process any checkboxes user ticked in _APPROVAL_CENTER.md
    md_actions = process_markdown_decisions(db, ai_hub)

    # 2. Export any .md.gdoc pointer files if gdrive CLI is ready
    gdoc_events = sanitize_gdoc_pointers(ai_hub)
    for ev in gdoc_events:
        db.add_event("sanitizer", "GDOC_CHECK", ev)

    # 3. Scan every linked project's INBOX.md via mtime/sha256
    ingested: list[str] = []
    for proj, meta in repo_map.items():
        ai_dir = ai_hub / proj
        inbox = ai_dir / "INBOX.md"
        if not inbox.exists():
            continue

        items = parse_inbox_sections(proj, inbox)
        context_path = ai_dir / "CONTEXT.md"
        context_md = context_path.read_text(encoding="utf-8", errors="replace") if context_path.exists() else ""

        for item in items:
            existing = db.get_task_by_sha(item.content_sha256)
            if existing is None:
                triage = triage_task(db, proj, item.title, item.raw_markdown, context_md, secrets)
                assets_ok, asset_msg = verify_task_assets(ai_dir, item.raw_markdown, secrets.debounce_sec)
                if triage.get("zone") == "RED":
                    status = "BLOCKED_RED_ZONE"
                elif assets_ok:
                    status = "READY"
                else:
                    status = "WAITING_ASSETS"

                db.upsert_task(
                    {
                        "task_id": item.task_id,
                        "project": proj,
                        "project_repo_path": meta["local_path"],
                        "title": item.title,
                        "source_file": item.source_file,
                        "content_sha256": item.content_sha256,
                        "raw_markdown": item.raw_markdown,
                        "pool": triage.get("pool", "agy_core"),
                        "zone": triage.get("zone", "YELLOW"),
                        "status": status,
                        "cost_summary": f"{triage.get('mode', 'rules')} · {asset_msg}",
                        "triage_json": json.dumps(triage, ensure_ascii=False),
                    }
                )
                db.add_event(item.task_id, "INGESTED", f"status={status} ({asset_msg})")
                ingested.append(item.task_id)
            elif existing["status"] == "WAITING_ASSETS":
                assets_ok, asset_msg = verify_task_assets(ai_dir, item.raw_markdown, secrets.debounce_sec)
                if assets_ok:
                    db.update_task_fields(existing["task_id"], status="READY", cost_summary=f"assets_ready · {asset_msg}")
                    db.add_event(existing["task_id"], "ASSETS_READY", asset_msg)

    # 4. Check monthly quota harvesters (22nd / 24th)
    harvester_alerts = check_monthly_harvesters(db, secrets)

    # 5. Notify Telegram for any un-notified AWAITING_APPROVAL tasks
    for task in db.list_tasks(status="AWAITING_APPROVAL", limit=20):
        notify_awaiting_approval(db, secrets, task)

    # 6. Render _APPROVAL_CENTER.md cleanly
    render_approval_center(db, ai_hub, secrets)

    return {
        "repos": len(repo_map),
        "ingested": ingested,
        "md_actions": md_actions,
        "harvester_alerts": harvester_alerts,
    }


def register_delivery(
    db: FleetDB,
    ai_hub: Path,
    task_id: str,
    worktree_path: str,
    branch_name: str,
    head_sha: str,
    diff_stat: str,
    verify_output: str,
    cost_summary: str,
    title: str = "",
    project: str = "",
) -> dict[str, Any]:
    """Register a completed isolated worktree delivery into AWAITING_APPROVAL and notify."""
    secrets = load_secrets()
    existing = db.get_task(task_id)
    if existing:
        db.update_task_fields(
            task_id,
            status="AWAITING_APPROVAL",
            zone="YELLOW",
            worktree_path=worktree_path,
            branch_name=branch_name,
            head_sha=head_sha,
            diff_stat=diff_stat,
            verify_output=verify_output,
            cost_summary=cost_summary,
        )
    else:
        repo_map = resolve_repo_map(ai_hub)
        proj = project or "unknown"
        repo_path = repo_map.get(proj, {}).get("local_path", "")
        db.upsert_task(
            {
                "task_id": task_id,
                "project": proj,
                "project_repo_path": repo_path,
                "title": title or task_id,
                "source_file": "manual-register",
                "content_sha256": task_id,
                "raw_markdown": title or task_id,
                "pool": "agy_core",
                "zone": "YELLOW",
                "status": "AWAITING_APPROVAL",
                "worktree_path": worktree_path,
                "branch_name": branch_name,
                "head_sha": head_sha,
                "diff_stat": diff_stat,
                "verify_output": verify_output,
                "cost_summary": cost_summary,
            }
        )

    db.add_event(task_id, "AWAITING_APPROVAL", f"{branch_name} @ {head_sha[:8]}")
    task = db.get_task(task_id)
    assert task is not None
    notify_awaiting_approval(db, secrets, task)
    render_approval_center(db, ai_hub, secrets)
    return task


def run_daemon() -> None:
    """Run continuous 0-token watcher + localhost:7788 telemetry/governance cockpit."""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        target = min(hard, 4096) if hard > 0 else 4096
        if soft < target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
    except (ValueError, OSError):
        pass

    ai_hub = detect_ai_hub()
    db = FleetDB()
    secrets = load_secrets()
    stop_event = threading.Event()

    def _stop_handler(_signum: int, _frame: Any) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, _stop_handler)
    signal.signal(signal.SIGINT, _stop_handler)

    cockpit = CockpitServer(db, ai_hub, port=secrets.fleet_port)
    http_thread = threading.Thread(target=cockpit.serve_forever, daemon=True, name="fleet-cockpit")
    http_thread.start()

    last_mtimes: dict[str, float] = {}
    last_scan_ts = 0.0
    last_warm_ts = 0.0

    def _bg_warm_cache() -> None:
        try:
            collect_cockpit_snapshot(db, ai_hub, force=True)
        except Exception as exc:  # noqa: BLE001
            db.add_event("daemon", "TELEMETRY_WARM_ERROR", str(exc))

    try:
        while not stop_event.is_set():
            runtime = load_secrets()
            watched_files = [ai_hub / "_APPROVAL_CENTER.md", ai_hub / "_REGISTRY.md", ai_hub / "_GLOBAL_INBOX.md"]
            watched_files.extend(ai_hub.glob("*/INBOX.md"))

            changed = False
            for f in watched_files:
                try:
                    mtime = f.stat().st_mtime
                except FileNotFoundError:
                    mtime = -1.0
                key = str(f)
                if last_mtimes.get(key) != mtime:
                    last_mtimes[key] = mtime
                    changed = True

            now = time.time()
            # Run full scan when a watched file changed, or every 60s for asset debounce / harvester check
            if changed or (now - last_scan_ts >= 60.0):
                try:
                    scan_once(db, ai_hub)
                except Exception as exc:  # noqa: BLE001
                    db.add_event("daemon", "SCAN_ERROR", str(exc))
                last_scan_ts = now

            # Pre-warm live telemetry cache in background every 150s so web/bot /api/state stays <15ms
            if now - last_warm_ts >= 150.0:
                last_warm_ts = now
                threading.Thread(target=_bg_warm_cache, daemon=True, name="fleet-warm").start()

            stop_event.wait(float(runtime.scan_interval_sec))
    finally:
        cockpit.shutdown()
