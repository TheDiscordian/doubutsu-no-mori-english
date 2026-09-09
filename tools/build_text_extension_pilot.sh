#!/usr/bin/env bash
# Complete general message fields plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_TEXT_EXTENSION="${AF_TEXT_EXTENSION:-build/text-extension}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/text-extension-pilot}"
exec bash tools/build_stall_choices_pilot.sh
