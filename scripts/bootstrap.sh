#!/usr/bin/env bash
# Turnkey idempotent bootstrapper for Google AI Ultra Maximizer (Fleet-Hub v3.0)
# Usage: ./scripts/bootstrap.sh [--minimal | --with-wheels | --with-skills | --all] [--start-service]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${HOME}/.local/bin"
WORKSPACE_ROOT="${FLEET_WORKSPACE_ROOT:-}"
if [ -z "${WORKSPACE_ROOT}" ]; then
  if [ "${REPO_ROOT%/*/*}" != "${REPO_ROOT}" ] && [ "$(basename "$(dirname "${REPO_ROOT}")")" = "tools" ]; then
    WORKSPACE_ROOT="$(dirname "$(dirname "${REPO_ROOT}")")"
  else
    WORKSPACE_ROOT="${HOME}/workspace"
  fi
fi

WITH_WHEELS=0
WITH_SKILLS=0
START_SERVICE=0

for arg in "$@"; do
  case "$arg" in
    --minimal)
      WITH_WHEELS=0
      WITH_SKILLS=0
      ;;
    --with-wheels)
      WITH_WHEELS=1
      ;;
    --with-skills)
      WITH_SKILLS=1
      ;;
    --all)
      WITH_WHEELS=1
      WITH_SKILLS=1
      ;;
    --start-service)
      START_SERVICE=1
      ;;
    -h|--help)
      cat <<'EOF'
Google AI Ultra Maximizer (Fleet-Hub) Bootstrapper

Usage:
  ./scripts/bootstrap.sh [options]

Options:
  --minimal         Install core CLI (`ultra` / `fleet`) + initialize config only (default)
  --with-wheels     Also install core open-source wheels (`agy-lens`, `agent-desktop`, `antigravity-usage`, `apprise`)
  --with-skills     Also install curated `mattpocock/skills`, `agent-desktop`, `ultra-quota-advisor`, and `gemini-web-research` into ~/.agents/skills
  --all             Equivalent to `--with-wheels --with-skills`
  --start-service   Install and start the background daemon (`launchd` on macOS, `systemd --user` on Linux)
  -h, --help        Show this help message
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (use --help)" >&2
      exit 1
      ;;
  esac
done

echo "==> Checking prerequisites (Python >= 3.11, git)..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required (>= 3.11)." >&2
  exit 1
fi
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(f"Python >= 3.11 required, found {sys.version}")
print(f"    Python {sys.version.split()[0]} OK")
PY

command -v git >/dev/null 2>&1 || { echo "Error: git is required." >&2; exit 1; }

echo "==> Linking CLI binaries (`ultra` and `fleet`) into ${BIN_DIR}..."
mkdir -p "${BIN_DIR}"
chmod +x "${REPO_ROOT}/bin/fleet"
ln -sf "${REPO_ROOT}/bin/fleet" "${BIN_DIR}/ultra"
ln -sf "${REPO_ROOT}/bin/fleet" "${BIN_DIR}/fleet"

export FLEET_WORKSPACE_ROOT="${WORKSPACE_ROOT}"
echo "==> Initializing workspace & config (${WORKSPACE_ROOT})..."
"${BIN_DIR}/ultra" init

if [ "${WITH_WHEELS}" -eq 1 ]; then
  echo "==> Installing recommended open-source wheels..."
  VENDOR_DIR="${WORKSPACE_ROOT}/tools/vendor"
  NPM_PREFIX="${WORKSPACE_ROOT}/tools/npm-global"
  mkdir -p "${VENDOR_DIR}" "${NPM_PREFIX}"

  if [ ! -d "${VENDOR_DIR}/agy-lens/.git" ]; then
    echo "  -> Cloning Aoike123/agy-lens..."
    git clone --depth 1 https://github.com/Aoike123/agy-lens.git "${VENDOR_DIR}/agy-lens" || \
      echo "  [warn] agy-lens clone failed."
  fi
  if [ -d "${VENDOR_DIR}/agy-lens" ]; then
    mkdir -p "${HOME}/.gemini/config/plugins"
    ln -sfn "${VENDOR_DIR}/agy-lens" "${HOME}/.gemini/config/plugins/agy-lens"
    chmod +x "${VENDOR_DIR}/agy-lens/bin/cli.mjs"
    ln -sf "${VENDOR_DIR}/agy-lens/bin/cli.mjs" "${BIN_DIR}/agy-lens"
  fi

  if command -v npm >/dev/null 2>&1; then
    echo "  -> Installing vercel-labs/agent-desktop and antigravity-usage via npm..."
    npm install -g --prefix "${NPM_PREFIX}" agent-desktop antigravity-usage || \
      echo "  [warn] npm wheel installation failed."
    [ -x "${NPM_PREFIX}/bin/agent-desktop" ] && ln -sf "${NPM_PREFIX}/bin/agent-desktop" "${BIN_DIR}/agent-desktop"
    [ -x "${NPM_PREFIX}/bin/antigravity-usage" ] && ln -sf "${NPM_PREFIX}/bin/antigravity-usage" "${BIN_DIR}/antigravity-usage"
  else
    echo "  [skip] npm not found; install Node.js >= 18 to install agent-desktop and antigravity-usage."
  fi

  if command -v uv >/dev/null 2>&1; then
    echo "  -> Installing caronc/apprise via uv..."
    uv tool install apprise || true
  elif command -v pip3 >/dev/null 2>&1; then
    echo "  -> Installing caronc/apprise via pip3 --user..."
    pip3 install --user apprise || true
  fi
fi

if [ "${WITH_SKILLS}" -eq 1 ]; then
  echo "==> Installing curated mattpocock/skills + agent-desktop skills..."
  VENDOR_DIR="${WORKSPACE_ROOT}/tools/vendor"
  SKILLS_TARGET="${HOME}/.agents/skills"
  mkdir -p "${VENDOR_DIR}" "${SKILLS_TARGET}"

  if [ ! -d "${VENDOR_DIR}/mattpocock-skills/.git" ]; then
    git clone --depth 1 https://github.com/mattpocock/skills.git "${VENDOR_DIR}/mattpocock-skills" || true
  fi
  if [ -d "${VENDOR_DIR}/mattpocock-skills/skills" ]; then
    for rel in \
      engineering/codebase-design \
      engineering/diagnosing-bugs \
      engineering/tdd \
      engineering/domain-modeling \
      engineering/code-review \
      engineering/prototype \
      engineering/grill-with-docs \
      engineering/improve-codebase-architecture \
      engineering/to-spec \
      engineering/to-tickets \
      engineering/implement-spec \
      engineering/retro \
      productivity/writing-for-agents \
      productivity/handoff \
      in-progress/software-factory \
      in-progress/chief-of-staff
    do
      src="${VENDOR_DIR}/mattpocock-skills/skills/${rel}"
      name="$(basename "${rel}")"
      if [ -d "${src}" ]; then
        rm -rf "${SKILLS_TARGET:?}/${name}"
        cp -R "${src}" "${SKILLS_TARGET}/${name}"
      fi
    done
  fi

  if [ ! -d "${VENDOR_DIR}/agent-desktop-repo/.git" ]; then
    git clone --depth 1 --filter=blob:none --sparse https://github.com/vercel-labs/agent-desktop.git "${VENDOR_DIR}/agent-desktop-repo" || true
    [ -d "${VENDOR_DIR}/agent-desktop-repo/.git" ] && git -C "${VENDOR_DIR}/agent-desktop-repo" sparse-checkout set skills || true
  fi
  if [ -d "${VENDOR_DIR}/agent-desktop-repo/skills" ]; then
    for name in agent-desktop agent-desktop-macos; do
      src="${VENDOR_DIR}/agent-desktop-repo/skills/${name}"
      if [ -d "${src}" ]; then
        rm -rf "${SKILLS_TARGET:?}/${name}"
        cp -R "${src}" "${SKILLS_TARGET}/${name}"
      fi
    done
  fi

  for skill_name in ultra-quota-advisor gemini-web-research; do
    if [ -d "${REPO_ROOT}/skills/${skill_name}" ]; then
      rm -rf "${SKILLS_TARGET}/${skill_name}"
      cp -R "${REPO_ROOT}/skills/${skill_name}" "${SKILLS_TARGET}/${skill_name}"
    fi
  done

  if [ -f "${HOME}/.gemini/config/skills.json" ]; then
    python3 - <<'PY'
import json
from pathlib import Path
p = Path.home() / ".gemini" / "config" / "skills.json"
data = json.loads(p.read_text(encoding="utf-8"))
wanted = [
    "codebase-design", "diagnosing-bugs", "tdd", "domain-modeling", "code-review",
    "prototype", "grill-with-docs", "improve-codebase-architecture", "to-spec",
    "to-tickets", "implement-spec", "retro", "writing-for-agents", "handoff",
    "software-factory", "chief-of-staff", "agent-desktop", "agent-desktop-macos",
    "ultra-quota-advisor", "gemini-web-research",
]
target_dir = str(Path.home() / ".agents" / "skills")
for entry in data.get("entries", []):
    if entry.get("path") == target_dir and isinstance(entry.get("include_only"), list):
        for w in wanted:
            if w not in entry["include_only"]:
                entry["include_only"].append(w)
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("    Updated ~/.gemini/config/skills.json allowlist.")
PY
  fi
fi

if [ "${START_SERVICE}" -eq 1 ]; then
  echo "==> Installing and starting background daemon..."
  "${BIN_DIR}/ultra" service install
fi

echo "==> Running doctor check..."
"${BIN_DIR}/ultra" doctor
echo ""
echo "Done! Next steps:"
echo "  1. Start foreground cockpit: ultra daemon (then open http://127.0.0.1:7788)"
echo "  2. Or run in background   : ultra service install"
echo "  3. Calibrate Cloud credit : Click 'Settings / Calibrate' in the web cockpit ($10 / $40 / $50 / $100)"
echo "  4. Add '${BIN_DIR}' to your shell PATH if not already present."
