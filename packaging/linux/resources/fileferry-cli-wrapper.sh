#!/usr/bin/env bash
set -euo pipefail

APP_BIN="/opt/fileferry/fileferry"

if [[ ! -x "$APP_BIN" ]]; then
  echo "error: FileFerry runtime not found at $APP_BIN" >&2
  exit 1
fi

exec "$APP_BIN" "$@"
