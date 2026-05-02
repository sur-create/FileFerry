#!/usr/bin/env bash
set -euo pipefail

TARGET_APP="/Applications/FileFerry.app"
TARGET_BIN="/usr/local/bin/fileferry"
TARGET_SHARE="/usr/local/share/fileferry"
PACKAGE_ID="io.fileferry.app"

remove_path() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "remove $path"
    rm -rf "$path"
  fi
}

remove_path "$TARGET_APP"
remove_path "$TARGET_BIN"
remove_path "$TARGET_SHARE"

if command -v pkgutil >/dev/null 2>&1; then
  pkgutil --forget "$PACKAGE_ID" >/dev/null 2>&1 || true
fi

echo "FileFerry uninstall complete"
