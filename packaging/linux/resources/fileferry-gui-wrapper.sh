#!/usr/bin/env bash
set -euo pipefail

APP_BIN="/opt/fileferry-gui/fileferry-gui"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/fileferry"
LOG_FILE="$STATE_DIR/gui-launch.log"

log_line() {
  local message="$1"
  mkdir -p "$STATE_DIR" 2>/dev/null || true
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$message" >> "$LOG_FILE" 2>/dev/null || true
}

show_error_dialog() {
  local message="$1"
  if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    return 0
  fi
  if command -v zenity >/dev/null 2>&1; then
    zenity --error --title="FileFerry" --text="$message" >/dev/null 2>&1 || true
    return 0
  fi
  if command -v xmessage >/dev/null 2>&1; then
    xmessage -center "$message" >/dev/null 2>&1 || true
  fi
}

extract_missing_sonames() {
  local content="$1"
  awk '
    /=> not found/ { print $1 }
  ' <<< "$content" | sort -u
}

map_missing_to_apt_package() {
  case "$1" in
    libxcb-cursor.so.0) echo "libxcb-cursor0" ;;
    libxcb-icccm.so.4) echo "libxcb-icccm4" ;;
    libxcb-image.so.0) echo "libxcb-image0" ;;
    libxcb-keysyms.so.1) echo "libxcb-keysyms1" ;;
    libxcb-render-util.so.0) echo "libxcb-render-util0" ;;
    libxcb-randr.so.0) echo "libxcb-randr0" ;;
    libxcb-shape.so.0) echo "libxcb-shape0" ;;
    libxcb-shm.so.0) echo "libxcb-shm0" ;;
    libxcb-sync.so.1) echo "libxcb-sync1" ;;
    libxcb-xfixes.so.0) echo "libxcb-xfixes0" ;;
    libxcb-xinerama.so.0) echo "libxcb-xinerama0" ;;
    libxkbcommon-x11.so.0) echo "libxkbcommon-x11-0" ;;
    libxkbcommon.so.0) echo "libxkbcommon0" ;;
    libx11-xcb.so.1) echo "libx11-xcb1" ;;
    libXrender.so.1) echo "libxrender1" ;;
    libXi.so.6) echo "libxi6" ;;
    libEGL.so.1) echo "libegl1" ;;
    libGL.so.1) echo "libgl1" ;;
    *) echo "" ;;
  esac
}

map_missing_to_dnf_package() {
  case "$1" in
    libxcb-cursor.so.0) echo "xcb-util-cursor" ;;
    libxcb-icccm.so.4) echo "xcb-util-wm" ;;
    libxcb-image.so.0) echo "xcb-util-image" ;;
    libxcb-keysyms.so.1) echo "xcb-util-keysyms" ;;
    libxcb-render-util.so.0) echo "xcb-util-renderutil" ;;
    libxkbcommon-x11.so.0) echo "libxkbcommon-x11" ;;
    libEGL.so.1) echo "mesa-libEGL" ;;
    libGL.so.1) echo "mesa-libGL" ;;
    *) echo "" ;;
  esac
}

collect_xcb_plugin_missing_libs() {
  local app_dir plugin output
  app_dir="$(dirname "$APP_BIN")"
  plugin="$(find "$app_dir" -type f -name 'libqxcb.so' 2>/dev/null | head -n 1)"
  if [[ -z "$plugin" ]] || ! command -v ldd >/dev/null 2>&1; then
    return 0
  fi
  output="$(ldd "$plugin" 2>/dev/null || true)"
  if [[ -n "$output" ]]; then
    extract_missing_sonames "$output"
  fi
}

build_install_hint() {
  local missing_libs="$1"
  local package_list package
  package_list=""

  if command -v apt-get >/dev/null 2>&1; then
    while IFS= read -r lib; do
      [[ -n "$lib" ]] || continue
      package="$(map_missing_to_apt_package "$lib")"
      [[ -n "$package" ]] || continue
      package_list="$package_list"$'\n'"$package"
    done <<< "$missing_libs"
    package_list="$(sort -u <<< "$package_list" | sed '/^$/d' | tr '\n' ' ')"
    if [[ -n "$package_list" ]]; then
      echo "sudo apt update && sudo apt install -y $package_list"
      return 0
    fi
    echo "sudo apt update && sudo apt install -y libxcb-cursor0"
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    while IFS= read -r lib; do
      [[ -n "$lib" ]] || continue
      package="$(map_missing_to_dnf_package "$lib")"
      [[ -n "$package" ]] || continue
      package_list="$package_list"$'\n'"$package"
    done <<< "$missing_libs"
    package_list="$(sort -u <<< "$package_list" | sed '/^$/d' | tr '\n' ' ')"
    if [[ -n "$package_list" ]]; then
      echo "sudo dnf install -y $package_list"
      return 0
    fi
    echo "sudo dnf install -y xcb-util-cursor"
    return 0
  fi

  if command -v yum >/dev/null 2>&1; then
    echo "sudo yum install -y xcb-util-cursor"
    return 0
  fi

  echo "install package providing missing XCB/Qt runtime libraries"
}

if [[ ! -x "$APP_BIN" ]]; then
  msg="FileFerry GUI runtime not found at $APP_BIN"
  log_line "error: $msg"
  echo "error: $msg" >&2
  show_error_dialog "FileFerry GUI 运行时缺失，请重新安装。"
  exit 1
fi

tmp_log="$(mktemp)"
if "$APP_BIN" "$@" >"$tmp_log" 2>&1; then
  rm -f "$tmp_log"
  exit 0
else
  status=$?
fi

output="$(cat "$tmp_log")"
rm -f "$tmp_log"

if [[ -n "$output" ]]; then
  while IFS= read -r line; do
    log_line "$line"
  done <<< "$output"
  printf '%s\n' "$output" >&2
fi

install_hint=""
if [[ "$output" == *"xcb-cursor0 or libxcb-cursor0"* ]] || [[ "$output" == *'Qt platform plugin "xcb"'* ]]; then
  missing_libs="$(collect_xcb_plugin_missing_libs)"
  if [[ -n "$missing_libs" ]]; then
    log_line "missing shared libraries:"
    while IFS= read -r lib; do
      [[ -n "$lib" ]] || continue
      log_line "  $lib"
    done <<< "$missing_libs"
    echo "missing shared libraries:" >&2
    printf '%s\n' "$missing_libs" | sed 's/^/  /' >&2
  fi
  install_hint="$(build_install_hint "${missing_libs:-}")"
  log_line "hint: run $install_hint"
  echo "hint: run $install_hint" >&2
fi

log_line "error: gui launcher exited with code $status"
dialog_msg="FileFerry GUI 启动失败（退出码 $status）。\n日志：$LOG_FILE"
if [[ -n "$install_hint" ]]; then
  dialog_msg="$dialog_msg\n建议执行：$install_hint"
fi
show_error_dialog "$dialog_msg"
exit "$status"
