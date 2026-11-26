"""Isolated Git Worktree manager, Red-Zone hook guard, and approval merge workflow."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import WORKTREES_ROOT, wrap_cmd
from .db import FleetDB

REGISTRY_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$"
)


def _run_git(repo: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    cmd = wrap_cmd(["git", "-C", str(repo), *args])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def resolve_repo_map(ai_hub: Path) -> dict[str, dict[str, str]]:
    """Parse AI-Projects/_REGISTRY.md to map project names to local repo paths & metadata."""
    reg_file = ai_hub / "_REGISTRY.md"
    result: dict[str, dict[str, str]] = {}
    if not reg_file.exists():
        return result
    for line in reg_file.read_text(encoding="utf-8", errors="replace").splitlines():
        m = REGISTRY_ROW_RE.match(line.strip())
        if not m:
            continue
        name, local_path, cloud_path, summary, updated = [x.strip() for x in m.groups()]
        if name == "项目名称":
            continue
        result[name] = {
            "project": name,
            "local_path": local_path,
            "cloud_path": cloud_path,
            "summary": summary,
            "updated": updated,
        }
    return result


def install_redzone_pre_push_hook(repo_path: Path) -> None:
    """Install a Red-Zone pre-push hook blocking accidental pushes from bot branches."""
    git_dir_proc = _run_git(repo_path, ["rev-parse", "--git-common-dir"])
    if git_dir_proc.returncode != 0:
        return
    common_dir = Path(git_dir_proc.stdout.strip())
    if not common_dir.is_absolute():
        common_dir = (repo_path / common_dir).resolve()
    hooks_dir = common_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_file = hooks_dir / "pre-push"
    marker = "# FLEET_REDZONE_GUARD"
    if hook_file.exists() and marker in hook_file.read_text(encoding="utf-8", errors="replace"):
        return

    existing = hook_file.read_text(encoding="utf-8", errors="replace") if hook_file.exists() else "#!/usr/bin/env bash\n"
    snippet = f"""
{marker}
# Block bot/* branches from pushing automatically (prevents triggering remote CI or prod deploys).
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
if [[ "$CURRENT_BRANCH" == bot/* ]] && [[ "${{FLEET_ALLOW_PUSH:-0}}" != "1" ]]; then
  echo "❌ [Red-Zone Guard] 禁止 Bot 分支 ($CURRENT_BRANCH) 自动推送或触发云端 CI。请通过审批台确认后由主人手动推送。" >&2
  exit 1
fi
"""
    hook_file.write_text(existing.rstrip() + "\n" + snippet, encoding="utf-8")
    os.chmod(hook_file, 0o755)


def create_isolated_worktree(
    repo_path: Path,
    ai_hub: Path,
    project: str,
    slug: str,
    base_ref: str = "HEAD",
) -> tuple[Path, str, str]:
    """Create `<worktrees_root>/<project>-<slug>` on branch `bot/<slug>` and link `.ai`."""
    WORKTREES_ROOT.mkdir(parents=True, exist_ok=True)
    wt_path = WORKTREES_ROOT / f"{project}-{slug}"
    branch = f"bot/{slug}"

    base_proc = _run_git(repo_path, ["rev-parse", base_ref])
    if base_proc.returncode != 0:
        raise RuntimeError(f"git rev-parse failed for {repo_path}: {base_proc.stderr.strip()}")
    base_sha = base_proc.stdout.strip()

    if not wt_path.exists():
        add_proc = _run_git(repo_path, ["worktree", "add", "-B", branch, str(wt_path), base_sha])
        if add_proc.returncode != 0:
            raise RuntimeError(f"git worktree add failed: {add_proc.stderr.strip()}")

    # Mirror .ai symlink inside the worktree
    wt_ai = wt_path / ".ai"
    cloud_ai = ai_hub / project
    if cloud_ai.exists() and not wt_ai.exists():
        os.symlink(cloud_ai, wt_ai)

    install_redzone_pre_push_hook(repo_path)
    return wt_path, branch, base_sha


def _archive_inbox_and_update_status(ai_dir: Path, ai_hub: Path, project: str, task: dict[str, Any]) -> None:
    """Move completed section note to STATUS.md and update _REGISTRY.md date."""
    today = datetime.now().strftime("%Y-%m-%d")
    status_file = ai_dir / "STATUS.md"
    if status_file.exists():
        st = status_file.read_text(encoding="utf-8", errors="replace")
        bullet = f"- [x] **[Fleet Approved {today}]** {task['title']}（`{task['branch_name']}` -> `main` @ `{task['head_sha'][:8]}`）"
        if bullet not in st:
            marker = "## 近期已完成事项"
            if marker in st:
                st = st.replace(marker, f"{marker}\n{bullet}", 1)
            else:
                st = st.rstrip() + f"\n\n{marker}\n{bullet}\n"
            status_file.write_text(st, encoding="utf-8")

    inbox_file = ai_dir / "INBOX.md"
    if inbox_file.exists():
        content = inbox_file.read_text(encoding="utf-8", errors="replace")
        block = task.get("raw_markdown", "").strip()
        if block and block in content:
            content = content.replace(block, f"<!-- ARCHIVED {today}: {task['title']} ({task['task_id']}) -->").strip() + "\n"
            inbox_file.write_text(content, encoding="utf-8")

    reg_file = ai_hub / "_REGISTRY.md"
    if reg_file.exists():
        lines = reg_file.read_text(encoding="utf-8", errors="replace").splitlines()
        updated_lines: list[str] = []
        for line in lines:
            m = REGISTRY_ROW_RE.match(line.strip())
            if m and m.group(1).strip() == project:
                _, lp, cp, summary, _ = [x.strip() for x in m.groups()]
                updated_lines.append(f"| {project} | `{lp}` | `{cp}` | {summary} | {today} |")
            else:
                updated_lines.append(line)
        reg_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def approve_task(db: FleetDB, ai_hub: Path, task_id: str) -> tuple[bool, str]:
    """Safely merge an AWAITING_APPROVAL worktree branch into main and clean up."""
    task = db.get_task(task_id)
    if not task:
        return False, f"未找到任务 {task_id}"
    if task["status"] not in ("AWAITING_APPROVAL", "APPROVED", "REVISE_REQUESTED"):
        return False, f"任务当前状态为 {task['status']}，不可执行合入"

    repo_path = Path(task["project_repo_path"])
    wt_path = Path(task["worktree_path"]) if task["worktree_path"] else None
    branch = task["branch_name"]

    if not repo_path.exists():
        return False, f"主仓库不存在: {repo_path}"

    # Ensure main repo has no dirty tracked files (untracked ?? files are fine unless conflicting)
    st_proc = _run_git(repo_path, ["status", "--porcelain", "--untracked-files=no"])
    if st_proc.returncode != 0:
        return False, f"主仓库状态检查失败: {st_proc.stderr.strip()}"
    if st_proc.stdout.strip():
        return False, f"主仓库存在未提交的已跟踪修改，请先清理后再合入:\n{st_proc.stdout.strip()}"

    if wt_path and wt_path.exists():
        wt_st = _run_git(wt_path, ["status", "--porcelain", "--untracked-files=no"])
        if wt_st.stdout.strip():
            return False, f"Worktree 尚有未提交改动，拒绝合入:\n{wt_st.stdout.strip()}"
        wt_head = _run_git(wt_path, ["rev-parse", "HEAD"]).stdout.strip()
        if task["head_sha"] and wt_head != task["head_sha"]:
            return False, f"Worktree HEAD ({wt_head[:8]}) 与待批指纹 ({task['head_sha'][:8]}) 不一致，已拦截"

    cur_branch = _run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    if cur_branch != "main":
        return False, f"主仓库当前位于分支 `{cur_branch}` 而非 `main`，请切回 `main` 后再批"

    merge_proc = _run_git(
        repo_path,
        ["merge", "--no-ff", branch, "-m", f"Merge {branch} (approved via fleet-hub) [skip ci]"],
        timeout=60,
    )
    if merge_proc.returncode != 0:
        _run_git(repo_path, ["merge", "--abort"])
        return False, f"自动合入失败（已回滚）：{merge_proc.stderr.strip() or merge_proc.stdout.strip()}"

    new_head = _run_git(repo_path, ["rev-parse", "HEAD"]).stdout.strip()
    if wt_path and wt_path.exists():
        wt_ai = wt_path / ".ai"
        if wt_ai.is_symlink():
            wt_ai.unlink(missing_ok=True)
        rm_proc = _run_git(repo_path, ["worktree", "remove", "--force", str(wt_path)], timeout=60)
        if rm_proc.returncode != 0 and wt_path.exists():
            shutil.rmtree(wt_path, ignore_errors=True)
            _run_git(repo_path, ["worktree", "prune"])

    project = task["project"]
    ai_dir = ai_hub / project
    _archive_inbox_and_update_status(ai_dir, ai_hub, project, task)

    db.update_task_fields(task_id, status="MERGED", head_sha=new_head)
    db.add_event(task_id, "MERGED", f"Merged {branch} -> main @ {new_head[:8]}")
    return True, f"已批准并安全合入 main @ {new_head[:8]}，已清理 worktree 并归档 STATUS.md"


def request_revision(db: FleetDB, task_id: str, note: str) -> tuple[bool, str]:
    """Mark an awaiting task as REVISE_REQUESTED while keeping its worktree intact."""
    task = db.get_task(task_id)
    if not task:
        return False, f"未找到任务 {task_id}"
    clean_note = note.strip() or "需要人工或 Bot 进一步调整"
    db.update_task_fields(task_id, status="REVISE_REQUESTED", revision_note=clean_note)
    db.add_event(task_id, "REVISE_REQUESTED", clean_note)
    return True, f"已退回修改（Worktree 保留在 {task['worktree_path']}）：{clean_note}"
