#!/usr/bin/env bash
# zero.md uninstaller
set -e

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"

rm -f "$BIN_DIR/zero.md"
rm -f "$BIN_DIR/zeromd"
rm -f "$BIN_DIR/zero-md"
rm -f "$APP_DIR/zero.md.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "zero.md has been cleanly uninstalled from your system."
