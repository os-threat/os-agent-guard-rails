#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/mock"
export BASE_URL="${BASE_URL:-http://127.0.0.1:8082}"
npm run test:contract
