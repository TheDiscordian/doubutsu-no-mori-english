#!/usr/bin/env bash
# Complete festival-stall choices plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_STALL_CHOICES=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/stall-choices-pilot}"
exec bash tools/build_event_item_names_pilot.sh
