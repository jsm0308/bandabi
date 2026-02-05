$ErrorActionPreference = "Stop"

Write-Host "==> lint"
pnpm -s lint

Write-Host "==> typecheck"
pnpm -s typecheck

Write-Host "==> test"
pnpm -s test
