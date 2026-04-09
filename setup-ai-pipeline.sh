#!/usr/bin/env bash
# setup-ai-pipeline.sh — Bootstrap the TRDAP AI pipeline environment
#
# Creates a clean Python venv, installs dependencies, validates structure,
# and optionally clones fieldlinked repos for training data integration.
#
# Usage:
#   chmod +x setup-ai-pipeline.sh
#   ./setup-ai-pipeline.sh            # full setup
#   ./setup-ai-pipeline.sh --no-venv  # skip venv creation
#   ./setup-ai-pipeline.sh --link     # also clone fieldlinked repos
#
# License: CC0 1.0

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PIPELINE_DIR="${REPO_ROOT}/ai-pipeline"
TRAINING_DIR="${PIPELINE_DIR}/training"
LINKED_DIR="${REPO_ROOT}/.linked-repos"

PYTHON="${PYTHON:-python3}"
MIN_PYTHON="3.9"

# Fieldlinked repositories
FIELDLINK_REPOS=(
    "https://github.com/JinnZ2/Infrastructure-assistance.git"
    "https://github.com/JinnZ2/Nexus-emergency-management.git"
    "https://github.com/JinnZ2/Seed-physics.git"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

check_python() {
    if ! command -v "${PYTHON}" &>/dev/null; then
        error "Python not found. Install Python >= ${MIN_PYTHON} and retry."
    fi

    local ver
    ver=$("${PYTHON}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major minor
    major=$(echo "${ver}" | cut -d. -f1)
    minor=$(echo "${ver}" | cut -d. -f2)

    local req_major req_minor
    req_major=$(echo "${MIN_PYTHON}" | cut -d. -f1)
    req_minor=$(echo "${MIN_PYTHON}" | cut -d. -f2)

    if [ "${major}" -lt "${req_major}" ] || { [ "${major}" -eq "${req_major}" ] && [ "${minor}" -lt "${req_minor}" ]; }; then
        error "Python ${MIN_PYTHON}+ required, found ${ver}"
    fi

    info "Python ${ver} found at $(command -v "${PYTHON}")"
}

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------

SKIP_VENV=false
DO_LINK=false

for arg in "$@"; do
    case "${arg}" in
        --no-venv) SKIP_VENV=true ;;
        --link)    DO_LINK=true ;;
        --help|-h)
            echo "Usage: $0 [--no-venv] [--link] [--help]"
            echo ""
            echo "  --no-venv   Skip virtual environment creation"
            echo "  --link      Clone fieldlinked repos (Infrastructure-assistance,"
            echo "              Nexus-emergency-management, Seed-physics)"
            echo "  --help      Show this help"
            exit 0
            ;;
        *) warn "Unknown argument: ${arg}" ;;
    esac
done

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "============================================"
echo "  TRDAP AI Pipeline Setup"
echo "============================================"
echo ""

# 1. Check Python
info "Checking Python..."
check_python

# 2. Create virtual environment
if [ "${SKIP_VENV}" = false ]; then
    if [ -d "${VENV_DIR}" ]; then
        info "Virtual environment already exists at ${VENV_DIR}"
    else
        info "Creating virtual environment..."
        "${PYTHON}" -m venv "${VENV_DIR}"
        info "Virtual environment created at ${VENV_DIR}"
    fi

    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    info "Activated venv: $(which python)"

    info "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet numpy
    info "Dependencies installed."
else
    info "Skipping venv (--no-venv)"
fi

# 3. Verify directory structure
info "Verifying pipeline directory structure..."

REQUIRED_DIRS=(
    "${PIPELINE_DIR}"
    "${PIPELINE_DIR}/config"
    "${PIPELINE_DIR}/scripts"
    "${TRAINING_DIR}/data"
    "${TRAINING_DIR}/models"
    "${TRAINING_DIR}/checkpoints"
    "${TRAINING_DIR}/logs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "${dir}" ]; then
        info "Creating ${dir}"
        mkdir -p "${dir}"
    fi
done

info "Directory structure verified."

# 4. Verify critical files
REQUIRED_FILES=(
    "${PIPELINE_DIR}/pipeline.py"
    "${PIPELINE_DIR}/config/pipeline.yaml"
    "${PIPELINE_DIR}/scripts/validate_data.py"
)

all_present=true
for f in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "${f}" ]; then
        warn "Missing: ${f}"
        all_present=false
    fi
done

if [ "${all_present}" = true ]; then
    info "All pipeline files present."
else
    warn "Some files missing — check the ai-pipeline/ directory."
fi

# 5. Syntax check
info "Running Python syntax checks..."
"${PYTHON}" -m py_compile "${PIPELINE_DIR}/pipeline.py" && info "  pipeline.py — OK"
"${PYTHON}" -m py_compile "${PIPELINE_DIR}/scripts/validate_data.py" && info "  validate_data.py — OK"

# 6. Clone fieldlinked repos (optional)
if [ "${DO_LINK}" = true ]; then
    info "Cloning fieldlinked repositories..."
    mkdir -p "${LINKED_DIR}"

    for repo_url in "${FIELDLINK_REPOS[@]}"; do
        repo_name=$(basename "${repo_url}" .git)
        target="${LINKED_DIR}/${repo_name}"

        if [ -d "${target}" ]; then
            info "  ${repo_name} already cloned, pulling latest..."
            git -C "${target}" pull --quiet origin main 2>/dev/null || \
                git -C "${target}" pull --quiet 2>/dev/null || \
                warn "  Could not pull ${repo_name}"
        else
            info "  Cloning ${repo_name}..."
            git clone --quiet --depth 1 "${repo_url}" "${target}" 2>/dev/null || \
                warn "  Could not clone ${repo_name} — check access permissions"
        fi
    done

    info "Fieldlinked repos available at ${LINKED_DIR}/"
fi

# 7. Add .linked-repos to .gitignore if not already present
GITIGNORE="${REPO_ROOT}/.gitignore"
if [ ! -f "${GITIGNORE}" ]; then
    echo ".linked-repos/" > "${GITIGNORE}"
    echo ".venv/" >> "${GITIGNORE}"
    info "Created .gitignore"
elif ! grep -q ".linked-repos" "${GITIGNORE}" 2>/dev/null; then
    echo "" >> "${GITIGNORE}"
    echo "# AI pipeline local state" >> "${GITIGNORE}"
    echo ".linked-repos/" >> "${GITIGNORE}"
    echo ".venv/" >> "${GITIGNORE}"
    info "Updated .gitignore"
fi

# 8. Summary
echo ""
echo "============================================"
echo "  Setup complete"
echo "============================================"
echo ""
echo "  Pipeline:   ${PIPELINE_DIR}/pipeline.py"
echo "  Config:     ${PIPELINE_DIR}/config/pipeline.yaml"
echo "  Training:   ${TRAINING_DIR}/"
echo "  Validator:  ${PIPELINE_DIR}/scripts/validate_data.py"
echo ""
echo "Next steps:"
echo "  1. Place TRDAP JSON messages in ${TRAINING_DIR}/data/"
echo "  2. Validate:  python ${PIPELINE_DIR}/scripts/validate_data.py --data-dir ${TRAINING_DIR}/data/"
echo "  3. Train:     python ${PIPELINE_DIR}/pipeline.py train --config ${PIPELINE_DIR}/config/pipeline.yaml"
echo "  4. Infer:     python ${PIPELINE_DIR}/pipeline.py infer --model ${TRAINING_DIR}/models/latest.json --input <file>"
echo ""
if [ "${DO_LINK}" = false ]; then
    echo "  To clone fieldlinked repos: ./setup-ai-pipeline.sh --link"
    echo ""
fi
