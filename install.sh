#!/usr/bin/env bash
# zero.md installer
# Supports:
#   curl -fsSL https://raw.githubusercontent.com/amrimangunsong/zero.md/main/install.sh | bash
#   or local git clone execution: ./install.sh

set -e

REPO_RAW_URL="https://raw.githubusercontent.com/amrimangunsong/zero.md/main"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
TARGET_BIN="$BIN_DIR/zero.md"
TARGET_DESKTOP="$APP_DIR/zero.md.desktop"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "    ███████╗███████╗██████╗  ██████╗         ███╗   ███╗██████╗ "
echo "    ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗        ████╗ ████║██╔══██╗"
echo "      ███╔╝ █████╗  ██████╔╝██║   ██║        ██╔████╔██║██║  ██║"
echo "     ███╔╝  ██╔══╝  ██╔══██╗██║   ██║  ██╗   ██║╚██╔╝██║██║  ██║"
echo "    ███████╗███████╗██║  ██║╚██████╔╝  ╚═╝██╗██║ ╚═╝ ██║██████╔╝"
echo "    ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝      ╚═╝╚═╝     ╚═╝╚═════╝ "
echo "                 Zero-bloat native Markdown viewer"
echo -e "${NC}"

mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"

# 1. Detect if running locally from repo or from curl pipe
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "$SCRIPT_DIR/zero.py" ]; then
    echo -e "${BLUE}==>${NC} Installing from local source..."
    cp "$SCRIPT_DIR/zero.py" "$TARGET_BIN"
    cp "$SCRIPT_DIR/zero.md.desktop" "$TARGET_DESKTOP"
else
    echo -e "${BLUE}==>${NC} Downloading zero.md from GitHub..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$REPO_RAW_URL/zero.py" -o "$TARGET_BIN"
        curl -fsSL "$REPO_RAW_URL/zero.md.desktop" -o "$TARGET_DESKTOP"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$TARGET_BIN" "$REPO_RAW_URL/zero.py"
        wget -qO "$TARGET_DESKTOP" "$REPO_RAW_URL/zero.md.desktop"
    else
        echo -e "${RED}Error: curl or wget is required to install zero.md.${NC}"
        exit 1
    fi
fi

# 2. Permissions and aliases
chmod +x "$TARGET_BIN"
chmod +x "$TARGET_DESKTOP"
ln -sf "$TARGET_BIN" "$BIN_DIR/zeromd"
ln -sf "$TARGET_BIN" "$BIN_DIR/zero-md"

# 3. Register Desktop MIME associations
if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default zero.md.desktop text/markdown
    xdg-mime default zero.md.desktop text/x-markdown
    xdg-mime default zero.md.desktop text/plain
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

# 4. Check dependencies
echo -e "${BLUE}==>${NC} Verifying system dependencies..."
python3 -c "
import sys
missing = []
try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('WebKit2', '4.1')
    from gi.repository import Gtk, WebKit2
except Exception:
    missing.append('python3-gi / WebKit2 (gir1.2-webkit2-4.1)')

try:
    import markdown_it
except Exception:
    missing.append('python3-markdown-it')

try:
    import pygments
except Exception:
    missing.append('python3-pygments')

if missing:
    print('WARN:' + ', '.join(missing))
else:
    print('OK')
" > /tmp/zero_dep_check.txt 2>&1 || true

DEP_STATUS=$(cat /tmp/zero_dep_check.txt)
rm -f /tmp/zero_dep_check.txt

if [[ "$DEP_STATUS" == WARN:* ]]; then
    MISSING_PKGS=${DEP_STATUS#WARN:}
    echo -e "${YELLOW}Warning: Missing optional dependencies: $MISSING_PKGS${NC}"
    echo "On Ubuntu/Debian, install with:"
    echo "  sudo apt install python3-gi gir1.2-webkit2-4.1 python3-markdown-it python3-pygments"
    echo "On Fedora:"
    echo "  sudo dnf install python3-gobject webkit2gtk4.1 python3-markdown-it python3-pygments"
    echo "On Arch Linux:"
    echo "  sudo pacman -S python-gobject webkit2gtk-4.1 python-markdown-it python-pygments"
else
    echo -e "${GREEN}✓ All system dependencies are satisfied!${NC}"
fi

# 5. Check PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "\n${YELLOW}Note:${NC} '$HOME/.local/bin' is not in your current PATH."
    echo "Add it to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo -e "\n${GREEN}===============================================${NC}"
echo -e "${GREEN}   zero.md installed successfully!             ${NC}"
echo -e "${GREEN}===============================================${NC}"
echo "How to use:"
echo "  1. Double click any .md file in your File Manager!"
echo "  2. Or run from terminal:  zero.md filename.md"
echo ""
echo "To uninstall anytime:"
echo "  curl -fsSL $REPO_RAW_URL/uninstall.sh | bash"
echo ""
