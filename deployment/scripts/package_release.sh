#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
VERSION="${1:-$(grep -E '^version = ' "$ROOT_DIR/pyproject.toml" | sed 's/^version = \"//; s/\"$//' | head -n1)}"
PACKAGE_NAME="agents-production-studio-${VERSION}"
STAGE_DIR="$(mktemp -d)"
TARGET_DIR="$STAGE_DIR/$PACKAGE_NAME"

if [[ -z "$VERSION" ]]; then
  echo "Unable to resolve version from pyproject.toml" >&2
  exit 1
fi

mkdir -p "$DIST_DIR" "$TARGET_DIR"

INCLUDE_ITEMS=(
  ".github"
  "agents_corpus_workflow"
  "tests"
  "docs"
  "examples"
  "deployment"
  "README.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  "CODE_OF_CONDUCT.md"
  "CHANGELOG.md"
  "LICENSE"
  "Makefile"
  "pyproject.toml"
  "requirements.txt"
  ".env.example"
  ".gitignore"
  ".dockerignore"
  "USAGE.md"
  "USAGE.zh-CN.md"
)

(
  cd "$ROOT_DIR"
  tar -cf - "${INCLUDE_ITEMS[@]}"
) | (
  cd "$TARGET_DIR"
  tar -xf -
)

find "$TARGET_DIR" -type d -name '__pycache__' -exec rm -rf {} +
find "$TARGET_DIR" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

tar -C "$STAGE_DIR" -czf "$DIST_DIR/$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"

echo "$DIST_DIR/$PACKAGE_NAME.tar.gz"
