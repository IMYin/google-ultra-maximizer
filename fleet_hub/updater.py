"""GitHub update checker and safe --ff-only self-updater for Google AI Ultra Maximizer."""

from __future__ import annotations

import json
import os
import platform
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from . import __version__
from .bridges import GITHUB_REPO
from .config import HUB_ROOT, RuntimeSecrets, wrap_cmd
from .db import FleetDB, now_iso
from .service_manager import SYSTEMD_UNIT_NAME, _detect_macos_plist, manage_service

UPDATE_TTL_SEC = 6 * 3600
_SEMVER_RE = re.compile(r"^[vV]?(\d+(?:\.\d+)*)")


def parse_semver(version_str: str) -> tuple[int, ...]:
    """Parse leading dotted integer segments from a version or tag string."""
    cleaned = str(version_str or "").strip()
    m = _SEMVER_RE.match(cleaned)
    if not m:
        return (0,)
    return tuple(int(part) for part in m.group(1).split("."))


def _proxy_url(secrets: RuntimeSecrets) -> str:
    proxy = secrets.fleet_proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy and secrets.fleet_auto_proxy_port > 0:
        try:
            with socket.create_connection(("127.0.0.1", secrets.fleet_auto_proxy_port), timeout=0.3):
                proxy = f"http://127.0.0.1:{secrets.fleet_auto_proxy_port}"
        except OSError:
            proxy = ""
    return proxy


def _build_opener(secrets: RuntimeSecrets) -> urllib.request.OpenerDirector:
    proxy = _proxy_url(secrets)
    if proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener()


def _git_env(secrets: RuntimeSecrets) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    proxy = _proxy_url(secrets)
    if proxy:
        env.setdefault("HTTP_PROXY", proxy)
        env.setdefault("HTTPS_PROXY", proxy)
        env.setdefault("http_proxy", proxy)
        env.setdefault("https_proxy", proxy)
    env.setdefault("NO_PROXY", "127.0.0.1,localhost")
    env.setdefault("no_proxy", "127.0.0.1,localhost")
    return env


def _github_get_json(url: str, secrets: RuntimeSecrets, timeout: float = 8.0) -> tuple[int, dict[str, Any] | None]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"google-ultra-maximizer/{__version__}",
        },
        method="GET",
    )
    opener = _build_opener(secrets)
    try:
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return resp.status, (data if isinstance(data, dict) else None)
    except urllib.error.HTTPError as err:
        return int(err.code), None
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return 0, None


def _run_git(repo_root: Path, args: list[str], *, env: dict[str, str] | None = None, timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        wrap_cmd(["git", "-C", str(repo_root), *args]),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def get_local_repo_info(repo_root: Path = HUB_ROOT) -> dict[str, Any]:
    """Inspect local version, git branch, HEAD SHA, and dirty status."""
    is_git = (repo_root / ".git").exists()
    sha = ""
    branch = ""
    dirty = False
    if is_git:
        try:
            r_sha = _run_git(repo_root, ["rev-parse", "HEAD"], timeout=5.0)
            if r_sha.returncode == 0:
                sha = r_sha.stdout.strip()
            r_br = _run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"], timeout=5.0)
            if r_br.returncode == 0:
                branch = r_br.stdout.strip()
            r_st = _run_git(repo_root, ["status", "--porcelain"], timeout=5.0)
            if r_st.returncode == 0:
                dirty = bool(r_st.stdout.strip())
        except (subprocess.SubprocessError, OSError):
            pass

    return {
        "version": __version__,
        "is_git": is_git,
        "sha": sha,
        "short_sha": sha[:7] if sha else "",
        "branch": branch,
        "dirty": dirty,
    }


def _auto_update_gate(local: dict[str, Any]) -> tuple[bool, str, str]:
    if not local.get("is_git"):
        return False, "非 Git 克隆目录，请手动拉取最新版", "Not a Git clone; update manually"
    branch = str(local.get("branch") or "")
    if branch not in ("main", "master"):
        return (
            False,
            f"当前位于分支 {branch or 'unknown'}（非 main），请手动合并更新",
            f"On branch {branch or 'unknown'} (not main); merge manually",
        )
    if local.get("dirty"):
        return (
            False,
            "本地工作区存在未提交改动，请先提交或暂存后再自动更新",
            "Local uncommitted changes detected; commit or stash first",
        )
    return True, "", ""


def _first_summary_line(text: str, limit: int = 180) -> str:
    for line in str(text or "").splitlines():
        cleaned = re.sub(r"^[#>*\-\s]+", "", line).strip()
        if cleaned:
            return cleaned[:limit]
    return ""


def check_for_updates(
    db: FleetDB,
    secrets: RuntimeSecrets,
    *,
    force: bool = False,
    repo_root: Path = HUB_ROOT,
    repository: str = GITHUB_REPO,
) -> dict[str, Any]:
    """Check GitHub latest Release and main branch commit against local HEAD without false positives."""
    local = get_local_repo_info(repo_root)
    can_auto, block_zh, block_en = _auto_update_gate(local)

    cached_raw = db.get_meta("telemetry_update_check_json", "")
    cached: dict[str, Any] | None = None
    if cached_raw:
        try:
            parsed_cache = json.loads(cached_raw)
            if isinstance(parsed_cache, dict):
                cached = parsed_cache
        except json.JSONDecodeError:
            cached = None

    if (
        not force
        and cached is not None
        and (time.time() - float(cached.get("checked_ts") or 0.0)) < UPDATE_TTL_SEC
        and cached.get("local_sha") == local["sha"]
        and cached.get("local_version") == local["version"]
    ):
        refreshed = dict(cached)
        refreshed.update(
            {
                "branch": local["branch"],
                "dirty": local["dirty"],
                "can_auto_update": can_auto,
                "block_reason": block_zh,
                "block_reason_en": block_en,
            }
        )
        return refreshed

    rel_status, rel_data = _github_get_json(f"https://api.github.com/repos/{repository}/releases/latest", secrets)
    com_status, com_data = _github_get_json(f"https://api.github.com/repos/{repository}/commits/main", secrets)

    if rel_status == 0 and com_status == 0:
        if cached is not None:
            stale_copy = dict(cached)
            stale_copy.update(
                {
                    "ok": True,
                    "stale": True,
                    "branch": local["branch"],
                    "dirty": local["dirty"],
                    "can_auto_update": can_auto,
                    "block_reason": block_zh,
                    "block_reason_en": block_en,
                }
            )
            return stale_copy
        return {
            "ok": False,
            "stale": False,
            "error": "network_unreachable",
            "update_available": False,
            "channel": "offline",
            "local_version": local["version"],
            "local_sha": local["sha"],
            "local_short_sha": local["short_sha"],
            "branch": local["branch"],
            "dirty": local["dirty"],
            "can_auto_update": can_auto,
            "block_reason": block_zh,
            "block_reason_en": block_en,
            "checked_at": now_iso(),
        }

    release_tag = ""
    release_name = ""
    release_summary = ""
    release_url = ""
    if rel_status == 200 and isinstance(rel_data, dict) and not rel_data.get("draft"):
        release_tag = str(rel_data.get("tag_name") or "").strip()
        release_name = str(rel_data.get("name") or release_tag).strip()
        release_summary = _first_summary_line(str(rel_data.get("body") or ""))
        release_url = str(rel_data.get("html_url") or "").strip()

    remote_sha = ""
    commit_message = ""
    commit_url = ""
    if com_status == 200 and isinstance(com_data, dict):
        remote_sha = str(com_data.get("sha") or "").strip()
        commit_obj = com_data.get("commit") if isinstance(com_data.get("commit"), dict) else {}
        commit_message = _first_summary_line(str(commit_obj.get("message") or ""))
        commit_url = str(com_data.get("html_url") or "").strip()

    release_newer = bool(release_tag and parse_semver(release_tag) > parse_semver(local["version"]))

    commit_behind = False
    behind_count = 0
    if remote_sha and local["is_git"] and local["sha"] and remote_sha != local["sha"]:
        is_ancestor = False
        try:
            anc = _run_git(repo_root, ["merge-base", "--is-ancestor", remote_sha, "HEAD"], timeout=5.0)
            is_ancestor = anc.returncode == 0
        except (subprocess.SubprocessError, OSError):
            is_ancestor = False

        if not is_ancestor:
            cmp_status, cmp_data = _github_get_json(
                f"https://api.github.com/repos/{repository}/compare/{local['sha']}...main",
                secrets,
            )
            if cmp_status == 200 and isinstance(cmp_data, dict):
                cmp_state = str(cmp_data.get("status") or "")
                ahead_by = int(cmp_data.get("ahead_by") or 0)
                if cmp_state in ("ahead", "diverged") and ahead_by > 0:
                    commit_behind = True
                    behind_count = ahead_by
            elif cmp_status == 404:
                try:
                    om = _run_git(repo_root, ["rev-parse", "origin/main"], timeout=5.0)
                    if om.returncode == 0 and om.stdout.strip() != remote_sha:
                        commit_behind = True
                        behind_count = 1
                except (subprocess.SubprocessError, OSError):
                    pass

    update_available = release_newer or commit_behind
    channel = "release" if release_newer else ("commit" if commit_behind else "up_to_date")
    target_ref = release_tag if release_newer else (remote_sha[:7] if remote_sha else "")
    if release_newer and release_url:
        compare_url = release_url
    elif local["short_sha"] and remote_sha:
        compare_url = f"https://github.com/{repository}/compare/{local['short_sha']}...{remote_sha[:7]}"
    else:
        compare_url = commit_url or f"https://github.com/{repository}"

    result: dict[str, Any] = {
        "ok": True,
        "stale": False,
        "update_available": update_available,
        "channel": channel,
        "target_ref": target_ref,
        "release_tag": release_tag,
        "release_name": release_name,
        "release_summary": release_summary,
        "release_url": release_url,
        "remote_sha": remote_sha,
        "remote_short_sha": remote_sha[:7] if remote_sha else "",
        "commit_message": commit_message,
        "commit_url": commit_url,
        "behind_count": behind_count,
        "compare_url": compare_url,
        "local_version": local["version"],
        "local_sha": local["sha"],
        "local_short_sha": local["short_sha"],
        "branch": local["branch"],
        "dirty": local["dirty"],
        "can_auto_update": can_auto,
        "block_reason": block_zh,
        "block_reason_en": block_en,
        "checked_at": now_iso(),
        "checked_ts": time.time(),
    }
    db.set_meta("telemetry_update_check_json", json.dumps(result, ensure_ascii=False))
    return result


def _trigger_detached_restart() -> None:
    """Restart the managed background daemon cleanly after HTTP response has flushed."""
    sys_name = platform.system()
    try:
        if sys_name == "Darwin":
            label, _ = _detect_macos_plist()
            subprocess.Popen(
                ["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{label}"],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys_name == "Linux":
            subprocess.Popen(
                ["systemctl", "--user", "restart", SYSTEMD_UNIT_NAME],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except OSError:
        pass


def _sync_existing_skills(repo_root: Path) -> None:
    repo_skills = repo_root / "skills"
    installed_root = Path.home() / ".agents" / "skills"
    if not repo_skills.is_dir() or not installed_root.is_dir():
        return
    for skill_dir in repo_skills.iterdir():
        if not skill_dir.is_dir():
            continue
        src_md = skill_dir / "SKILL.md"
        dst_dir = installed_root / skill_dir.name
        if src_md.is_file() and dst_dir.is_dir():
            (dst_dir / "SKILL.md").write_text(src_md.read_text(encoding="utf-8"), encoding="utf-8")


def perform_self_update(
    db: FleetDB,
    secrets: RuntimeSecrets,
    *,
    repo_root: Path = HUB_ROOT,
    schedule_restart: bool = True,
) -> tuple[bool, str, dict[str, Any]]:
    """Fast-forward local repository from origin and optionally schedule a background daemon restart."""
    local = get_local_repo_info(repo_root)
    can_auto, block_zh, _ = _auto_update_gate(local)
    if not can_auto:
        return False, block_zh, {"updated": False, "restarting": False, "dirty": local["dirty"]}

    branch = str(local["branch"])
    env = _git_env(secrets)
    try:
        fetch_proc = _run_git(repo_root, ["fetch", "origin", branch, "--tags"], env=env, timeout=30.0)
        if fetch_proc.returncode != 0:
            err = (fetch_proc.stderr or fetch_proc.stdout or "git fetch failed").strip()
            return False, f"拉取远端失败: {err[:240]}", {"updated": False, "restarting": False}

        pull_proc = _run_git(repo_root, ["pull", "--ff-only", "origin", branch], env=env, timeout=30.0)
        if pull_proc.returncode != 0:
            err = (pull_proc.stderr or pull_proc.stdout or "git pull --ff-only failed").strip()
            return False, f"无法快进更新（请手动合并）: {err[:240]}", {"updated": False, "restarting": False}

        after_proc = _run_git(repo_root, ["rev-parse", "HEAD"], timeout=5.0)
        after_sha = after_proc.stdout.strip() if after_proc.returncode == 0 else local["sha"]
    except (subprocess.SubprocessError, OSError) as exc:
        return False, f"执行 Git 更新异常: {exc}", {"updated": False, "restarting": False}

    db.set_meta("telemetry_update_check_json", "")
    from_short = local["short_sha"]
    to_short = after_sha[:7] if after_sha else from_short

    if after_sha == local["sha"]:
        return (
            True,
            "当前已是最新版本，无需更新",
            {"updated": False, "restarting": False, "from_sha": from_short, "to_sha": to_short},
        )

    _sync_existing_skills(repo_root)
    db.add_event("updater", "SELF_UPDATED", f"{from_short} -> {to_short}")

    managed_running = False
    try:
        managed_running = bool(manage_service("status")[0])
    except Exception:  # noqa: BLE001
        managed_running = False

    will_restart = bool(schedule_restart and managed_running)
    if will_restart:
        timer = threading.Timer(0.8, _trigger_detached_restart)
        timer.daemon = True
        timer.start()

    msg = f"已更新至 {to_short}，正在自动重启驾驶舱…" if will_restart else f"已更新至 {to_short}"
    return True, msg, {"updated": True, "restarting": will_restart, "from_sha": from_short, "to_sha": to_short}
