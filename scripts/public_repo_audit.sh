#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== PUBLIC REPOSITORY AUDIT ==="
echo "Repository: $ROOT"
echo

echo "=== TRACKED LARGE FILES (>5 MiB) ==="
git ls-files -z | xargs -0 -r du -h 2>/dev/null | awk '$1 ~ /M|G/ {print}' | sort -h || true

echo
echo "=== POSSIBLE SECRET FILES ==="
find . -type f \( -name '.env' -o -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name '*.pfx' \) \
  -not -path './.git/*' -print || true

echo
echo "=== BACKUP / TEMP FILES ==="
find . -type f \( -name '*.before-*' -o -name '*.bak*' -o -name '*.tmp' -o -name '*~' \) \
  -not -path './.git/*' -print || true

echo
echo "=== GIT STATUS ==="
git status --short

echo
echo "=== DIFF CHECK ==="
git diff --check || true
