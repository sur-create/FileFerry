#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_BIN_DIR="$ROOT_DIR/dist/fileferry"
DIST_GUI_DIR="$ROOT_DIR/dist/fileferry-gui"
INSTALLER_DIR="$ROOT_DIR/dist/installer"
BUILD_DIR="$ROOT_DIR/build/linux/deb"
PKG_ROOT="$BUILD_DIR/pkgroot"

fail() {
  echo "error: $*" >&2
  exit 1
}

need_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

map_arch() {
  local raw_arch="$1"
  case "$raw_arch" in
    x86_64|amd64) echo "amd64" ;;
    aarch64|arm64) echo "arm64" ;;
    armv7l) echo "armhf" ;;
    *) echo "$raw_arch" ;;
  esac
}

need_tool python3
need_tool dpkg-deb

[[ -d "$DIST_BIN_DIR" ]] || fail "missing dist/fileferry. Run: python3 scripts/build_binary.py --clean"
[[ -d "$DIST_GUI_DIR" ]] || fail "missing dist/fileferry-gui. Run: python3 scripts/build_binary.py --clean"

VERSION="$(python3 -c 'from fileferry import __version__; print(__version__)')"
RAW_ARCH="$(dpkg --print-architecture 2>/dev/null || uname -m)"
ARCH="$(map_arch "$RAW_ARCH")"

rm -rf "$BUILD_DIR"
mkdir -p "$PKG_ROOT/DEBIAN" "$PKG_ROOT/opt/fileferry" "$PKG_ROOT/opt/fileferry-gui" "$PKG_ROOT/usr/bin" "$PKG_ROOT/usr/share/applications" "$INSTALLER_DIR"

cp -a "$DIST_BIN_DIR/." "$PKG_ROOT/opt/fileferry/"
cp -a "$DIST_GUI_DIR/." "$PKG_ROOT/opt/fileferry-gui/"
install -m 0755 "$ROOT_DIR/packaging/linux/resources/fileferry-cli-wrapper.sh" "$PKG_ROOT/usr/bin/fileferry"
install -m 0755 "$ROOT_DIR/packaging/linux/resources/fileferry-gui-wrapper.sh" "$PKG_ROOT/usr/bin/fileferry-gui"
install -m 0644 "$ROOT_DIR/packaging/linux/resources/fileferry.desktop" "$PKG_ROOT/usr/share/applications/fileferry.desktop"

cat > "$PKG_ROOT/DEBIAN/control" <<CONTROL
Package: fileferry
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: FileFerry Team <support@fileferry.local>
Depends: libc6
Description: FileFerry LAN file transfer tool with GUI
 Self-contained LAN transfer utility supporting CLI and desktop GUI.
CONTROL

OUT_FILE="$INSTALLER_DIR/fileferry_${VERSION}_${ARCH}.deb"
dpkg-deb --build "$PKG_ROOT" "$OUT_FILE"

echo "created: $OUT_FILE"
