#!/usr/bin/env bash
set -euo pipefail

echo "==> lint"
pnpm -s lint

echo "==> typecheck"
pnpm -s typecheck

echo "==> test"
pnpm -s test
