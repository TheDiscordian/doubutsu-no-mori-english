#!/usr/bin/env bash
# Complete both symbol targets with apology-only input and all prior translations.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_APOLOGY_INPUT="${AF_APOLOGY_INPUT:-build/apology-input-overlay}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/apology-input-pilot}"
exec bash tools/build_reserve_strings_pilot.sh
