"""Configuration discovery and hot-reloadable secrets loader for Google AI Ultra Maximizer (Fleet-Hub)."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


def _discover_hub_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _discover_workspace_root(hub_root: Path) -> Path:
    env_ws = os.environ.get("FLEET_WORKSPACE_ROOT", "").strip()
    if env_ws:
        return Path(env_ws).expanduser().resolve()
    # If installed inside <workspace>/tools/fleet-hub, use <workspace>.
    if hub_root.parent.name == "tools" and (hub_root.parent.parent / "projects").is_dir():
        return hub_root.parent.parent
    return Path.home() / "workspace"


def _discover_cmd_wrapper() -> Path | None:
    env_wrap = os.environ.get("FLEET_CMD_WRAPPER", "").strip()
    if env_wrap:
        p = Path(env_wrap).expanduser()
        return p if p.exists() else None
    found = shutil.which("dev-external")
    if found:
        return Path(found)
    local_candidate = Path.home() / ".local" / "bin" / "dev-external"
    if local_candidate.exists() and os.access(local_candidate, os.X_OK):
        return local_candidate
    return None


def _discover_secrets_path() -> Path:
    env_path = os.environ.get("FLEET_SECRETS_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser()
    primary = Path.home() / ".config" / "ultra-maximizer" / "secrets.env"
    legacy = Path.home() / ".config" / "fleet-hub" / "secrets.env"
    if primary.exists():
        return primary
    return legacy


HUB_ROOT = _discover_hub_root()
WORKSPACE_ROOT = _discover_workspace_root(HUB_ROOT)
PROJECTS_ROOT = Path(os.environ.get("FLEET_PROJECTS_ROOT", str(WORKSPACE_ROOT / "projects"))).expanduser()
WORKTREES_ROOT = Path(os.environ.get("FLEET_WORKTREES_ROOT", str(WORKSPACE_ROOT / "worktrees"))).expanduser()
ARTIFACTS_ROOT = Path(os.environ.get("FLEET_ARTIFACTS_ROOT", str(WORKSPACE_ROOT / "agent-artifacts"))).expanduser()
STATE_DIR = Path(os.environ.get("FLEET_STATE_DIR", str(HUB_ROOT / "state"))).expanduser()
LOGS_DIR = Path(os.environ.get("FLEET_LOGS_DIR", str(HUB_ROOT / "logs"))).expanduser()
DB_PATH = STATE_DIR / "fleet.sqlite"
SECRETS_ENV_PATH = _discover_secrets_path()
DEV_EXTERNAL = _discover_cmd_wrapper()
PLAYWRIGHT_BROWSERS_DIR = os.environ.get(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(WORKSPACE_ROOT / "tools" / "playwright-browsers"),
)


def wrap_cmd(cmd: list[str]) -> list[str]:
    """Prefix an external command wrapper (e.g. dev-external) if present on this machine."""
    if DEV_EXTERNAL is not None and DEV_EXTERNAL.exists():
        return [str(DEV_EXTERNAL), *cmd]
    return list(cmd)


def resolve_tool_bin(name: str, extra_candidates: tuple[Path, ...] = ()) -> Path | None:
    """Locate an external CLI binary on PATH, ~/.local/bin, or known tool directories."""
    found = shutil.which(name)
    if found:
        return Path(found)
    candidates = [
        Path.home() / ".local" / "bin" / name,
        WORKSPACE_ROOT / "tools" / "npm-global" / "bin" / name,
        *extra_candidates,
    ]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    return None


def detect_ai_hub() -> Path:
    """Locate the shared AI-Projects synchronization directory (Google Drive or local fallback)."""
    env_override = os.environ.get("FLEET_AI_HUB", "").strip()
    if env_override:
        p = Path(env_override).expanduser()
        if p.exists():
            return p

    cloud_root = Path.home() / "Library" / "CloudStorage"
    if cloud_root.exists():
        for gd in sorted(cloud_root.glob("GoogleDrive-*")):
            for drive_name in ("我的云端硬盘", "My Drive"):
                candidate = gd / drive_name / "AI-Projects"
                if candidate.exists():
                    return candidate

    # Fallback via any project's .ai symlink
    if PROJECTS_ROOT.exists():
        for project_dir in sorted(PROJECTS_ROOT.iterdir()):
            symlink_ai = project_dir / ".ai"
            if symlink_ai.is_symlink():
                target = symlink_ai.resolve()
                if target.parent.exists():
                    return target.parent

    return WORKSPACE_ROOT / "AI-Projects"


@dataclass(frozen=True)
class RuntimeSecrets:
    """Hot-reloaded credentials, notification channels, and daemon settings."""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    fleet_notify_urls: str = ""
    gemini_paid_api_key: str = ""
    gemini_triage_model: str = "gemini-2.5-flash"
    fleet_port: int = 7788
    scan_interval_sec: int = 8
    debounce_sec: int = 10
    max_concurrency: int = 3
    fleet_proxy: str = ""
    fleet_auto_proxy_port: int = 1082
    fleet_privacy_mode: bool = False
    ui_lang: str = "zh"
    flow_monthly_credits: float = 25000.0
    colab_monthly_cu: float = 2000.0
    paid_api_monthly_usd: float = 0.0
    paid_api_external_used_usd: float = 0.0

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    def all_notify_urls(self) -> list[str]:
        """Return deduplicated Apprise notification URLs including derived Telegram channel."""
        urls: list[str] = []
        for token in self.fleet_notify_urls.replace(";", "\n").replace(",", "\n").splitlines():
            cleaned = token.strip()
            if cleaned and cleaned not in urls:
                urls.append(cleaned)
        if self.telegram_enabled:
            tg_url = f"tgram://{self.telegram_bot_token}/{self.telegram_chat_id}"
            if tg_url not in urls:
                urls.append(tg_url)
        return urls

    @property
    def notify_enabled(self) -> bool:
        return bool(self.all_notify_urls())

    @property
    def paid_api_enabled(self) -> bool:
        return bool(self.gemini_paid_api_key)


def load_secrets(secrets_path: Path = SECRETS_ENV_PATH) -> RuntimeSecrets:
    """Parse secrets.env safely without logging secret values."""
    raw: dict[str, str] = {}
    if secrets_path.exists():
        for line in secrets_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            raw[k.strip()] = v.strip().strip('"').strip("'")

    def _get(key: str, default: str = "") -> str:
        return raw.get(key) or os.environ.get(key, default)

    def _int(key: str, default: int) -> int:
        val = _get(key)
        try:
            return int(val) if val else default
        except ValueError:
            return default

    def _float(key: str, default: float) -> float:
        val = _get(key)
        try:
            return float(val) if val else default
        except ValueError:
            return default

    def _bool(key: str, default: bool = False) -> bool:
        val = _get(key).lower()
        if not val:
            return default
        return val in ("1", "true", "yes", "on")

    return RuntimeSecrets(
        telegram_bot_token=_get("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=_get("TELEGRAM_CHAT_ID"),
        fleet_notify_urls=_get("FLEET_NOTIFY_URLS"),
        gemini_paid_api_key=_get("GEMINI_PAID_API_KEY"),
        gemini_triage_model=_get("GEMINI_TRIAGE_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash",
        fleet_port=_int("FLEET_PORT", 7788),
        scan_interval_sec=_int("FLEET_SCAN_INTERVAL_SEC", 8),
        debounce_sec=_int("FLEET_DEBOUNCE_SEC", 10),
        max_concurrency=_int("FLEET_MAX_CONCURRENCY", 3),
        fleet_proxy=_get("FLEET_PROXY"),
        fleet_auto_proxy_port=_int("FLEET_AUTO_PROXY_PORT", 1082),
        fleet_privacy_mode=_bool("FLEET_PRIVACY_MODE", False),
        ui_lang=(_get("FLEET_LANG", "zh").lower() if _get("FLEET_LANG", "zh").lower() in ("zh", "en") else "zh"),
        flow_monthly_credits=_float("FLOW_MONTHLY_CREDITS", 25000.0),
        colab_monthly_cu=_float("COLAB_MONTHLY_CU", 2000.0),
        paid_api_monthly_usd=_float("PAID_API_MONTHLY_USD", 0.0),
        paid_api_external_used_usd=_float("PAID_API_EXTERNAL_USED_USD", 0.0),
    )


def save_settings_patch(updates: dict[str, str], secrets_path: Path = SECRETS_ENV_PATH) -> Path:
    """Safely update or append settings in secrets.env while preserving comments and untouched keys."""
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = (
        secrets_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if secrets_path.exists()
        else []
    )
    remaining = {k: str(v).strip() for k, v in updates.items()}
    new_lines: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        k_clean = key.strip()
        if k_clean in remaining:
            val = remaining.pop(k_clean)
            if val:
                new_lines.append(f"{k_clean}={val}")
            # If val is empty string for a non-secret calibration field, omit to reset to default
        else:
            new_lines.append(line)

    for k_clean, val in remaining.items():
        if val:
            new_lines.append(f"{k_clean}={val}")

    tmp = secrets_path.with_suffix(".tmp")
    tmp.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(secrets_path)
    os.chmod(secrets_path, 0o600)
    return secrets_path


def mask_email(email: str, privacy: bool = False) -> str:
    """Mask email when privacy mode is enabled for public demos/screenshots."""
    if not email or not privacy or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    prefix = local[:1] if local else "*"
    return f"{prefix}***@{domain}"


def redact_path(path_str: str, privacy: bool = False) -> str:
    """Replace user home directory prefix with ~ when privacy mode is enabled."""
    if not privacy or not path_str:
        return path_str
    home_str = str(Path.home())
    if path_str.startswith(home_str):
        return "~" + path_str[len(home_str) :]
    return path_str
