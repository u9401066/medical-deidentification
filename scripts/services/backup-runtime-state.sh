#!/bin/bash
# Back up mutable runtime state before service updates or rollback drills.

set -euo pipefail

BACKUP_DIR="${1:-/var/backups/medical-deid}"
ENV_DIR="/etc/medical-deid"
DATA_DIR="${MEDICAL_DEID_DATA_DIR:-/var/lib/medical-deid}"
LOG_DIR="${MEDICAL_DEID_LOG_DIR:-/var/log/medical-deid}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/medical-deid-runtime-$STAMP.tar.gz"

if [ "$EUID" -ne 0 ]; then
    echo "請以 sudo 執行：sudo $0 [/var/backups/medical-deid]"
    exit 1
fi

install -d -m 700 -o root -g root "$BACKUP_DIR"

paths=(
    /etc/systemd/system/medical-deid-backend.service \
    /etc/systemd/system/medical-deid-frontend.service \
    "$ENV_DIR" \
    "$DATA_DIR" \
    "$LOG_DIR"
)

existing_paths=()
for path in "${paths[@]}"; do
    if [ -e "$path" ]; then
        existing_paths+=("$path")
    else
        echo "Skip missing path: $path" >&2
    fi
done

if [ "${#existing_paths[@]}" -eq 0 ]; then
    echo "沒有可備份的 runtime 路徑" >&2
    exit 1
fi

tar --warning=no-file-changed -czf "$ARCHIVE" \
    --absolute-names \
    "${existing_paths[@]}" 2>/tmp/medical-deid-backup.err || {
        code=$?
        cat /tmp/medical-deid-backup.err >&2 || true
        rm -f /tmp/medical-deid-backup.err
        exit "$code"
    }
rm -f /tmp/medical-deid-backup.err
chmod 600 "$ARCHIVE"

echo "$ARCHIVE"
