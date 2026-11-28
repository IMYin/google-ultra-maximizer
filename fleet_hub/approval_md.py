"""Bi-directional Markdown Approval Center (AI-Projects/_APPROVAL_CENTER.md)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .config import RuntimeSecrets
from .db import FleetDB
from .worktree import approve_task, request_revision

APPROVE_CHECK_RE = re.compile(r"^-\s+\[[xX]\]\s+APPROVE\s*<!--\s*task_id:\s*([A-Za-z0-9_.-]+)\s*-->", re.MULTILINE)
REVISE_CHECK_RE = re.compile(
    r"^-\s+\[[xX]\]\s+REVISE:\s*(.*?)\s*<!--\s*task_id:\s*([A-Za-z0-9_.-]+)\s*-->",
    re.MULTILINE,
)


def process_markdown_decisions(db: FleetDB, ai_hub: Path) -> list[str]:
    """Parse user-checked boxes in AI-Projects/_APPROVAL_CENTER.md and act on them."""
    md_path = ai_hub / "_APPROVAL_CENTER.md"
    if not md_path.exists():
        return []

    text = md_path.read_text(encoding="utf-8", errors="replace")
    actions: list[str] = []

    for m in APPROVE_CHECK_RE.finditer(text):
        task_id = m.group(1)
        task = db.get_task(task_id)
        if task and task["status"] == "AWAITING_APPROVAL":
            ok, msg = approve_task(db, ai_hub, task_id)
            actions.append(f"{task_id}: {'APPROVED' if ok else 'ERR'} - {msg}")

    for m in REVISE_CHECK_RE.finditer(text):
        note, task_id = m.group(1).strip(), m.group(2)
        if note == "在此填写修改意见":
            note = "请按审批备注复查调整"
        task = db.get_task(task_id)
        if task and task["status"] == "AWAITING_APPROVAL":
            ok, msg = request_revision(db, task_id, note)
            actions.append(f"{task_id}: {'REVISE' if ok else 'ERR'} - {msg}")

    return actions


def render_approval_center(db: FleetDB, ai_hub: Path, secrets: RuntimeSecrets) -> Path:
    """Regenerate AI-Projects/_APPROVAL_CENTER.md cleanly from SQLite state."""
    md_path = ai_hub / "_APPROVAL_CENTER.md"
    awaiting = db.list_tasks(status="AWAITING_APPROVAL", limit=20)
    revise = db.list_tasks(status="REVISE_REQUESTED", limit=10)
    active = [t for t in db.list_tasks(limit=30) if t["status"] in ("NEW", "WAITING_ASSETS", "READY", "RUNNING", "BLOCKED_RED_ZONE", "FAILED")]
    merged = db.list_tasks(status="MERGED", limit=10)

    triage_mode = f"Paid Gemini API (`{secrets.gemini_triage_model}`)" if secrets.paid_api_enabled else "零 Token 规则引擎（待填入 GEMINI_PAID_API_KEY 自动升级）"
    notify_mode = f"Apprise 已接入 ({len(secrets.all_notify_urls())} 通道) ✅" if secrets.notify_enabled else "未配置（交互审批可直接用驾驶舱）"

    lines: list[str] = [
        "# Google AI Ultra Maximizer · 统一审批中心 (`_APPROVAL_CENTER`)",
        "",
        f"> **监听模式**: 0-Token FSEvents/Stat | **分诊引擎**: {triage_mode} | **推送**: {notify_mode}",
        f"> **本地驾驶舱**: `http://127.0.0.1:{secrets.fleet_port}` | **原生执行面**: Antigravity 2.0",
        "",
        "**手机端审批操作**：在下方任意黄区工单中，将 `- [ ] APPROVE` 改为 `- [x] APPROVE`（或勾选 `REVISE:` 并写修改意见）保存，本地 `fleetd` 将在数秒内自动合入 `main`、清理隔离 Worktree 并更新项目台账。",
        "",
        "---",
        "",
        f"## 待你拍板（黄区审批单 · {len(awaiting)} 项）",
        "",
    ]

    if not awaiting:
        lines.append("_当前没有待审批的黄区工单。所有 Bot 均在 0-Token 休眠待命中。_")
        lines.append("")
    else:
        for t in awaiting:
            lines.extend(
                [
                    f"### [{t['project']}] {t['title']}",
                    f"- **工单 ID**: `{t['task_id']}` | **算力池**: `{t['pool']}` | **隔离分支**: `{t['branch_name']}` (`{t['head_sha'][:8]}`)",
                    f"- **隔离 Worktree**: `{t['worktree_path']}`",
                    f"- **改动摘要 (`diff --stat`)**:",
                    "```text",
                    (t["diff_stat"] or "(无 diff 摘要)").strip(),
                    "```",
                    f"- **自动化校验结果**:",
                    "```text",
                    (t["verify_output"] or "(未附带测试日志)").strip(),
                    "```",
                    f"- **算力与成本账本**: `{t['cost_summary'] or '0-Token / 本地验证'}`",
                    "",
                    f"- [ ] APPROVE <!-- task_id: {t['task_id']} -->",
                    f"- [ ] REVISE: 在此填写修改意见 <!-- task_id: {t['task_id']} -->",
                    "",
                ]
            )

    if revise:
        lines.extend(["---", "", f"## 退回修改中（{len(revise)} 项）", ""])
        for t in revise:
            lines.append(f"- `{t['task_id']}` **[{t['project']}]** {t['title']} — 意见：`{t['revision_note']}`（Worktree: `{t['worktree_path']}`）")
        lines.append("")

    if active:
        lines.extend(["---", "", f"## 队列 / 拦截中（{len(active)} 项）", ""])
        for t in active:
            lines.append(f"- `{t['task_id']}` **[{t['status']}]** [{t['project']}] {t['title']} ({t['cost_summary']})")
        lines.append("")

    lines.extend(["---", "", f"## 最近已放行归档（近 {len(merged)} 单）", ""])
    if not merged:
        lines.append("_暂无已归档审批记录。_")
    else:
        for t in merged:
            lines.append(f"- ✅ `{t['updated_at']}` **[{t['project']}]** {t['title']} (`{t['head_sha'][:8]}`)")
    lines.append("")

    new_content = "\n".join(lines)
    if not md_path.exists() or md_path.read_text(encoding="utf-8", errors="replace") != new_content:
        md_path.write_text(new_content, encoding="utf-8")
    return md_path
