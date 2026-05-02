#!/usr/bin/env bash
# Contract Net Router — install wizard
# Supports: Linux, WSL, Termux (Android)
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
prompt()  { echo -e "${YELLOW}[INPUT]${NC} $*"; }

detect_platform() {
    if [ -n "${TERMUX_VERSION:-}" ] || [ -d "/data/data/com.termux" ]; then echo "termux"
    elif grep -qi microsoft /proc/version 2>/dev/null; then echo "wsl"
    else echo "linux"; fi
}

install_deps_system() {
    local plat="$1"
    case "$plat" in
        termux) pkg update -y; pkg install -y python git ;;
        wsl|linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y python3 python3-venv python3-pip git
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y python3 python3-virtualenv git
            elif command -v pacman &>/dev/null; then
                sudo pacman -Sy --noconfirm python git
            elif command -v apk &>/dev/null; then
                sudo apk add --no-cache python3 py3-pip git
            fi ;;
    esac
}

PLATFORM=$(detect_platform)
INSTALL_DIR="${HOME}/.local/share/contract-net-router"
VENV_DIR="${INSTALL_DIR}/.venv"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      Contract Net Router  v1.0.0         ║"
echo "║   Capability-matched agent task bidding  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "Platform: $PLATFORM"

install_deps_system "$PLATFORM"
mkdir -p "$INSTALL_DIR"
if [ "$PLATFORM" = "termux" ]; then python -m venv "$VENV_DIR"
else python3 -m venv "$VENV_DIR"; fi
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install . -q

ENV_FILE="${INSTALL_DIR}/.env"
touch "$ENV_FILE"; chmod 600 "$ENV_FILE"

echo ""
echo "────────────────────────────────────────────"
echo " Agent Registry Configuration (optional)"
echo " Define your agents in a YAML file."
echo " See examples/demo.py for the schema."
echo "────────────────────────────────────────────"

prompt "Path to agent registry YAML (leave blank to use built-in demo agents):"
read -r registry_path
if [ -n "$registry_path" ]; then echo "CONTRACT_NET_AGENT_REGISTRY=${registry_path}" >> "$ENV_FILE"; fi

prompt "Contract Net home directory (default: $INSTALL_DIR):"
read -r home_path
if [ -n "$home_path" ]; then echo "CONTRACT_NET_HOME=${home_path}" >> "$ENV_FILE"; fi

success "Config saved to $ENV_FILE"

WRAPPER="${HOME}/.local/bin/cnr"
mkdir -p "$(dirname "$WRAPPER")"
cat > "$WRAPPER" << WRAPEOF
#!/usr/bin/env bash
set -a; [ -f "${ENV_FILE}" ] && . "${ENV_FILE}"; set +a
exec "${VENV_DIR}/bin/cnr" "\$@"
WRAPEOF
chmod +x "$WRAPPER"

echo ""
success "Installation complete!"
echo ""
echo "  Usage:  cnr --help"
echo "  Docs:   https://github.com/M00C1FER/contract-net-router"
