#!/bin/bash
# Launch the production frontend.

set -euo pipefail

DEFAULT_NODE_BIN="/home/eric/.nvm/versions/node/v20.19.6/bin"
export PATH="${MEDICAL_DEID_NODE_BIN:-$DEFAULT_NODE_BIN}:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec node "$SCRIPT_DIR/frontend-server.mjs"
