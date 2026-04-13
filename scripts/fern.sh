#!/usr/bin/env bash
# Wrapper script to run Fern CLI with Node.js 22 (required - Node v25 has breaking crypto changes)
# Usage: ./scripts/fern.sh check | ./scripts/fern.sh docs publish
set -euo pipefail

NODE22="/opt/homebrew/opt/node@22/bin/node"

if [ ! -x "$NODE22" ]; then
  echo "Error: Node.js 22 not found at $NODE22"
  echo "Install with: brew install node@22"
  exit 1
fi

FERN_CLI="$(dirname "$0")/../node_modules/.bin/fern"

if [ ! -f "$FERN_CLI" ]; then
  echo "Error: fern-api not installed. Run: $NODE22 $(dirname $NODE22)/npm install --save-dev fern-api"
  exit 1
fi

exec "$NODE22" "$FERN_CLI" "$@"
