#!/usr/bin/env bash
set -euo pipefail

MAX=8
i=1

while [ $i -le $MAX ]; do
  echo "=== Refactor Loop: Attempt $i/$MAX ==="
  if ./scripts/verify.sh; then
    echo "✅ All checks passed."
    exit 0
  else
    echo "❌ Checks failed."
    echo "Action: Fix issues and run again."
  fi
  i=$((i+1))
done

echo "🛑 Reached max attempts. Manual intervention needed."
exit 1
