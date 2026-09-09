#!/usr/bin/env bash
# Save-preserving fishing names with all preceding translation layers.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_FISHING_NAME="${AF_FISHING_NAME:-build/fishing-name-overlay}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/fishing-name-pilot}"
exec bash tools/build_map_labels_pilot.sh
