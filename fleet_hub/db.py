"""SQLite WAL state store for fleet-hub tasks, events, and 6-pool quota ledger."""

from __future__ import annotations

import contextlib
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import DB_PATH

DEFAULT_POOLS: tuple[tuple[str, float, str], ...] = (
    ("agy_core", 100.0, "% rolling"),
    ("paid_gemini_api", 0.0, "USD/mo"),
    ("ai_studio_daily", 100.0, "% daily"),
    ("gdrive_bus", 30720.0, "GB"),
    ("colab_cu", 2000.0, "CU/mo"),
    ("flow_credits", 25000.0, "pts/mo"),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


class FleetDB:
    """Thread-safe SQLite wrapper using short-lived WAL connections."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    project TEXT NOT NULL,
                    project_repo_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    content_sha256 TEXT UNIQUE NOT NULL,
                    raw_markdown TEXT NOT NULL,
                    pool TEXT NOT NULL DEFAULT 'agy_core',
                    zone TEXT NOT NULL DEFAULT 'YELLOW',
                    status TEXT NOT NULL DEFAULT 'NEW',
                    worktree_path TEXT DEFAULT '',
                    branch_name TEXT DEFAULT '',
                    base_sha TEXT DEFAULT '',
                    head_sha TEXT DEFAULT '',
                    diff_stat TEXT DEFAULT '',
                    verify_output TEXT DEFAULT '',
                    cost_summary TEXT DEFAULT '',
                    triage_json TEXT DEFAULT '',
                    revision_note TEXT DEFAULT '',
                    tg_message_id INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS quota_ledger (
                    month TEXT NOT NULL,
                    pool TEXT NOT NULL,
                    used_units REAL NOT NULL DEFAULT 0,
                    budget_units REAL NOT NULL,
                    unit_name TEXT NOT NULL,
                    last_harvester_run TEXT DEFAULT '',
                    PRIMARY KEY (month, pool)
                );

                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
        self.ensure_month_pools()

    def ensure_month_pools(self, month: str | None = None) -> None:
        m = month or current_month()
        with self._connect() as conn:
            for pool, budget, unit in DEFAULT_POOLS:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO quota_ledger (month, pool, used_units, budget_units, unit_name)
                    VALUES (?, ?, 0.0, ?, ?)
                    """,
                    (m, pool, budget, unit),
                )

    def add_event(self, task_id: str, event_type: str, detail: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (task_id, event_type, detail, created_at) VALUES (?, ?, ?, ?)",
                (task_id, event_type, detail[:2000], now_iso()),
            )

    def get_task_by_sha(self, sha256: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE content_sha256 = ?", (sha256,)).fetchone()
            return dict(row) if row else None

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list_tasks(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def upsert_task(self, data: dict[str, Any]) -> None:
        ts = now_iso()
        with self._connect() as conn:
            existing = conn.execute("SELECT task_id FROM tasks WHERE task_id = ?", (data["task_id"],)).fetchone()
            if existing:
                cols = [k for k in data.keys() if k != "task_id"]
                assigns = ", ".join(f"{c} = ?" for c in cols)
                vals = [data[c] for c in cols] + [ts, data["task_id"]]
                conn.execute(f"UPDATE tasks SET {assigns}, updated_at = ? WHERE task_id = ?", vals)
            else:
                payload = dict(data)
                payload.setdefault("created_at", ts)
                payload.setdefault("updated_at", ts)
                cols = list(payload.keys())
                placeholders = ", ".join("?" for _ in cols)
                conn.execute(
                    f"INSERT INTO tasks ({', '.join(cols)}) VALUES ({placeholders})",
                    [payload[c] for c in cols],
                )

    def update_task_fields(self, task_id: str, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = now_iso()
        assigns = ", ".join(f"{k} = ?" for k in fields.keys())
        vals = list(fields.values()) + [task_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE tasks SET {assigns} WHERE task_id = ?", vals)

    def get_quota_ledger(self, month: str | None = None) -> list[dict[str, Any]]:
        m = month or current_month()
        self.ensure_month_pools(m)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM quota_ledger WHERE month = ? ORDER BY pool ASC",
                (m,),
            ).fetchall()
            return [dict(r) for r in rows]

    def increment_quota(self, pool: str, delta: float, month: str | None = None) -> None:
        m = month or current_month()
        self.ensure_month_pools(m)
        with self._connect() as conn:
            conn.execute(
                "UPDATE quota_ledger SET used_units = used_units + ? WHERE month = ? AND pool = ?",
                (delta, m, pool),
            )

    def sync_pool_budget(self, pool: str, budget_units: float, month: str | None = None) -> None:
        m = month or current_month()
        self.ensure_month_pools(m)
        with self._connect() as conn:
            conn.execute(
                "UPDATE quota_ledger SET budget_units = ? WHERE month = ? AND pool = ?",
                (float(budget_units), m, pool),
            )

    def mark_harvester_run(self, pool: str, stamp: str, month: str | None = None) -> None:
        m = month or current_month()
        self.ensure_month_pools(m)
        with self._connect() as conn:
            conn.execute(
                "UPDATE quota_ledger SET last_harvester_run = ? WHERE month = ? AND pool = ?",
                (stamp, m, pool),
            )

    def recent_events(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_meta(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
            return str(row["value"]) if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def get_or_create_csrf_token(self) -> str:
        existing = self.get_meta("cockpit_csrf_token", "")
        if existing:
            return existing
        token = secrets.token_hex(24)
        self.set_meta("cockpit_csrf_token", token)
        return token
