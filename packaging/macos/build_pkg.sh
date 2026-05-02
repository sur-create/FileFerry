#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_BIN_DIR="$ROOT_DIR/dist/fileferry"
DIST_GUI_DIR="$ROOT_DIR/dist/fileferry-gui"
INSTALLER_DIR="$ROOT_DIR/dist/installer"
BUILD_DIR="$ROOT_DIR/build/macos"
APP_BUNDLE="$BUILD_DIR/FileFerry.app"
PKG_ROOT="$BUILD_DIR/pkgroot"
COMPONENT_PKG="$BUILD_DIR/fileferry-component.pkg"

fail() {
  echo "error: $*" >&2
  exit 1
}

need_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

[[ "$(uname -s)" == "Darwin" ]] || fail "macOS packaging must run on macOS"
need_tool python3
need_tool pkgbuild
need_tool productbuild

if [[ ! -d "$DIST_BIN_DIR" || ! -d "$DIST_GUI_DIR" ]]; then
  echo "dist/fileferry or dist/fileferry-gui missing. building binaries first..."
  python3 "$ROOT_DIR/scripts/build_binary.py" --clean
fi

VERSION="$(python3 -c 'from fileferry import __version__; print(__version__)')"

rm -rf "$BUILD_DIR"
mkdir -p "$APP_BUNDLE/Contents/MacOS" "$APP_BUNDLE/Contents/Resources/runtime_gui" "$APP_BUNDLE/Contents/Resources/runtime_cli" "$PKG_ROOT/Applications" "$PKG_ROOT/usr/local/bin" "$PKG_ROOT/usr/local/share/fileferry" "$INSTALLER_DIR"

cp -a "$DIST_GUI_DIR/." "$APP_BUNDLE/Contents/Resources/runtime_gui/"
cp -a "$DIST_BIN_DIR/." "$APP_BUNDLE/Contents/Resources/runtime_cli/"

cat > "$APP_BUNDLE/Contents/MacOS/FileFerry" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_BIN="$SCRIPT_DIR/../Resources/runtime_gui/fileferry-gui"

if [[ ! -x "$RUNTIME_BIN" ]]; then
  echo "FileFerry GUI runtime not found. Please reinstall FileFerry."
  exit 1
fi

exec "$RUNTIME_BIN" "$@"
LAUNCHER
chmod +x "$APP_BUNDLE/Contents/MacOS/FileFerry"

cat > "$APP_BUNDLE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>FileFerry</string>
  <key>CFBundleDisplayName</key>
  <string>FileFerry</string>
  <key>CFBundleIdentifier</key>
  <string>io.fileferry.app</string>
  <key>CFBundleVersion</key>
  <string>${VERSION}</string>
  <key>CFBundleShortVersionString</key>
  <string>${VERSION}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleExecutable</key>
  <string>FileFerry</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
  <key>LSApplicationCategoryType</key>
  <string>public.app-category.utilities</string>
</dict>
</plist>
PLIST

cp -a "$APP_BUNDLE" "$PKG_ROOT/Applications/"
install -m 0755 "$ROOT_DIR/packaging/macos/fileferry-wrapper.sh" "$PKG_ROOT/usr/local/bin/fileferry"
install -m 0755 "$ROOT_DIR/packaging/macos/uninstall_fileferry.sh" "$PKG_ROOT/usr/local/share/fileferry/uninstall_fileferry.sh"

pkgbuild \
  --root "$PKG_ROOT" \
  --identifier "io.fileferry.app" \
  --version "$VERSION" \
  --install-location "/" \
  "$COMPONENT_PKG"

productbuild --package "$COMPONENT_PKG" "$INSTALLER_DIR/FileFerry-${VERSION}-macos.pkg"

echo "created: $INSTALLER_DIR/FileFerry-${VERSION}-macos.pkg"
