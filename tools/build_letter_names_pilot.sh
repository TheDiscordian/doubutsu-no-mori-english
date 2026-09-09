#!/usr/bin/env bash
# Complete letter-editor recipient names and every preceding translation layer.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_LETTER_NAMES="${AF_LETTER_NAMES:-build/letter-names-overlay}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/letter-names-pilot}"
exec bash tools/build_house_name_pilot.sh
