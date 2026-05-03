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
  if command -v apt-get >/dev/null 2>&1; then
    install_hint="sudo apt update && sudo apt install -y libxcb-cursor0"
  elif command -v dnf >/dev/null 2>&1; then
    install_hint="sudo dnf install -y xcb-util-cursor"
  elif command -v yum >/dev/null 2>&1; then
    install_hint="sudo yum install -y xcb-util-cursor"
  else
    install_hint="install package providing libxcb-cursor.so.0"
  fi
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
