#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

SOURCE_ROOT="${SOURCE_ROOT:-$ROOT_DIR}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/tmp}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"

mkdir -p "$OUTPUT_DIR"

exec python -m agents_corpus_workflow.cli serve-api \
  --source-root "$SOURCE_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --host "$HOST" \
  --port "$PORT"
