#!/usr/bin/env bash
# Complete house-sign names with all preceding translation layers.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_HOUSE_NAME=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/house-name-pilot}"
exec bash tools/build_conversation_names_pilot.sh
