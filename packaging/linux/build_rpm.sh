#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_BIN_DIR="$ROOT_DIR/dist/fileferry"
DIST_GUI_DIR="$ROOT_DIR/dist/fileferry-gui"
INSTALLER_DIR="$ROOT_DIR/dist/installer"
BUILD_DIR="$ROOT_DIR/build/linux/rpm"
RPM_TOP="$BUILD_DIR/rpmbuild"
STAGE_ROOT="$BUILD_DIR/stage"

fail() {
  echo "error: $*" >&2
  exit 1
}

need_tool() {
  command -v "$1" >/dev/null 2>&1 || fail "required tool not found: $1"
}

need_tool python3
need_tool rpmbuild
need_tool tar

[[ -d "$DIST_BIN_DIR" ]] || fail "missing dist/fileferry. Run: python3 scripts/build_binary.py --clean"
[[ -d "$DIST_GUI_DIR" ]] || fail "missing dist/fileferry-gui. Run: python3 scripts/build_binary.py --clean"

VERSION="$(python3 -c 'from fileferry import __version__; print(__version__)')"
ARCH="$(rpm --eval '%{_arch}')"
SRC_DIR_NAME="fileferry-${VERSION}"
SRC_STAGE="$STAGE_ROOT/$SRC_DIR_NAME"

rm -rf "$BUILD_DIR"
mkdir -p "$RPM_TOP"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} "$SRC_STAGE/opt/fileferry" "$SRC_STAGE/opt/fileferry-gui" "$SRC_STAGE/usr/bin" "$SRC_STAGE/usr/share/applications" "$INSTALLER_DIR"

cp -a "$DIST_BIN_DIR/." "$SRC_STAGE/opt/fileferry/"
cp -a "$DIST_GUI_DIR/." "$SRC_STAGE/opt/fileferry-gui/"
install -m 0755 "$ROOT_DIR/packaging/linux/resources/fileferry-cli-wrapper.sh" "$SRC_STAGE/usr/bin/fileferry"
install -m 0755 "$ROOT_DIR/packaging/linux/resources/fileferry-gui-wrapper.sh" "$SRC_STAGE/usr/bin/fileferry-gui"
install -m 0644 "$ROOT_DIR/packaging/linux/resources/fileferry.desktop" "$SRC_STAGE/usr/share/applications/fileferry.desktop"

TARBALL="$RPM_TOP/SOURCES/${SRC_DIR_NAME}.tar.gz"
tar -C "$STAGE_ROOT" -czf "$TARBALL" "$SRC_DIR_NAME"

SPEC_FILE="$RPM_TOP/SPECS/fileferry.spec"
cat > "$SPEC_FILE" <<SPEC
Name:           fileferry
Version:        ${VERSION}
Release:        1%{?dist}
Summary:        FileFerry LAN file transfer tool with GUI
License:        Proprietary
URL:            https://example.invalid/fileferry
Source0:        ${SRC_DIR_NAME}.tar.gz
BuildArch:      ${ARCH}

%description
FileFerry is a self-contained LAN transfer tool with CLI and desktop GUI.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -a opt %{buildroot}/
cp -a usr %{buildroot}/

%files
/opt/fileferry
/opt/fileferry-gui
/usr/bin/fileferry
/usr/bin/fileferry-gui
/usr/share/applications/fileferry.desktop

%changelog
* $(LC_ALL=C date '+%a %b %d %Y') FileFerry Team <support@fileferry.local> - ${VERSION}-1
- Automated build
SPEC

rpmbuild --define "_topdir $RPM_TOP" -bb "$SPEC_FILE"
mapfile -t RPM_FILES < <(find "$RPM_TOP/RPMS" -name "fileferry-${VERSION}-*.rpm")
[[ "${#RPM_FILES[@]}" -gt 0 ]] || fail "rpmbuild completed but no rpm artifacts were found"
cp "${RPM_FILES[@]}" "$INSTALLER_DIR/"

echo "created rpm packages under: $INSTALLER_DIR"
