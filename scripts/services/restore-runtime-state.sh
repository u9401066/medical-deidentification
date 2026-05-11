#!/bin/bash
# Restore a backup created by backup-runtime-state.sh.

set -euo pipefail

ARCHIVE="${1:-}"

if [ "$EUID" -ne 0 ]; then
    echo "請以 sudo 執行：sudo $0 /var/backups/medical-deid/medical-deid-runtime-*.tar.gz"
    exit 1
fi

if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
    echo "找不到備份檔：$ARCHIVE"
    exit 1
fi

systemctl stop medical-deid-frontend.service medical-deid-backend.service 2>/dev/null || true
tar -xzf "$ARCHIVE" --absolute-names
systemctl daemon-reload
systemctl restart medical-deid-backend.service
sleep 2
systemctl restart medical-deid-frontend.service

echo "Restored runtime state from $ARCHIVE"
