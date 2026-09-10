#!/usr/bin/env bash
# Translate the native reserve labels while retaining all previous integrations.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_RESERVE_STRINGS=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/reserve-strings-pilot}"
exec bash tools/build_borrowed_catchphrases_pilot.sh
