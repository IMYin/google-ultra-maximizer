"""Inbox parser, .gdoc pointer sanitizer, and attachment integrity verifier."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

SECTION_RE = re.compile(r"^##\s+\[(\d{4}-\d{2}-\d{2})\]\s+(.+?)\s*$", re.MULTILINE)
ATTACHMENT_RE = re.compile(r"(?:\.ai/specs/|specs/)([A-Za-z0-9_.\-/]+\.(?:zip|json|jpg|jpeg|png|webp|md))")
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True)
class InboxItem:
    project: str
    date: str
    title: str
    raw_markdown: str
    content_sha256: str
    task_id: str
    source_file: str


def sanitize_gdoc_pointers(ai_hub: Path) -> list[str]:
    """Find *.md.gdoc pointer files in AI-Projects and export missing .md siblings via gdrive CLI."""
    messages: list[str] = []
    if not ai_hub.exists():
        return messages

    gdrive_bin = shutil.which("gdrive")
    for gdoc_path in sorted(ai_hub.rglob("*.md.gdoc")):
        if "_archive" in gdoc_path.relative_to(ai_hub).parts:
            continue
        target_md = gdoc_path.with_suffix("")  # removes .gdoc -> keeps .md
        if target_md.exists() and target_md.stat().st_size > 0:
            continue
        try:
            payload = json.loads(gdoc_path.read_text(encoding="utf-8", errors="replace"))
            doc_id = payload.get("doc_id", "")
        except json.JSONDecodeError:
            doc_id = ""
        if not doc_id:
            continue

        if not gdrive_bin:
            messages.append(f"gdoc_pending:{gdoc_path.name} (gdrive CLI unavailable)")
            continue

        proc = subprocess.run(
            [gdrive_bin, "readonly", "export", doc_id, "--mime", "text/markdown", "--out", str(target_md)],
            capture_output=True,
            text=True,
            timeout=25,
        )
        if proc.returncode == 0 and target_md.exists() and target_md.stat().st_size > 0:
            messages.append(f"gdoc_exported:{target_md.name}")
        else:
            if target_md.exists() and target_md.stat().st_size == 0:
                target_md.unlink(missing_ok=True)
            messages.append(f"gdoc_needs_auth:{gdoc_path.name}")
    return messages


def parse_inbox_sections(project: str, inbox_path: Path) -> list[InboxItem]:
    """Extract dated `## [YYYY-MM-DD] Title` blocks from an INBOX.md file."""
    if not inbox_path.exists():
        return []
    text = inbox_path.read_text(encoding="utf-8", errors="replace")
    cleaned = COMMENT_RE.sub("", text)
    matches = list(SECTION_RE.finditer(cleaned))
    items: list[InboxItem] = []

    for idx, m in enumerate(matches):
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        block = cleaned[start:end].strip()
        if not block:
            continue
        date_str = m.group(1)
        title = m.group(2).strip()
        canonical = f"{project}::{date_str}::{title}::{block}"
        sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        compact_date = date_str.replace("-", "")
        safe_proj = re.sub(r"[^a-zA-Z0-9_-]+", "-", project).strip("-").lower() or "proj"
        task_id = f"{safe_proj}-{compact_date}-{sha[:8]}"
        items.append(
            InboxItem(
                project=project,
                date=date_str,
                title=title,
                raw_markdown=block,
                content_sha256=sha,
                task_id=task_id,
                source_file=str(inbox_path),
            )
        )
    return items


def verify_task_assets(project_ai_dir: Path, raw_markdown: str, debounce_sec: int = 10) -> tuple[bool, str]:
    """Ensure referenced specs/*.zip files exist, settled past debounce window, and pass CRC check."""
    refs = sorted(set(ATTACHMENT_RE.findall(raw_markdown)))
    if not refs:
        return True, "no_external_attachments"

    now = time.time()
    specs_root = project_ai_dir / "specs"
    for rel in refs:
        candidate = specs_root / rel
        if not candidate.exists():
            return False, f"missing_attachment:{rel}"
        age = now - candidate.stat().st_mtime
        if age < debounce_sec:
            return False, f"sync_debounce:{rel} ({age:.1f}s < {debounce_sec}s)"
        if candidate.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(candidate, "r") as zf:
                    bad = zf.testzip()
                    if bad is not None:
                        return False, f"corrupt_zip:{rel}:{bad}"
            except zipfile.BadZipFile:
                return False, f"incomplete_zip:{rel}"
    return True, f"verified_{len(refs)}_assets"
