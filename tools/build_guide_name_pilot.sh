#!/usr/bin/env bash
# Complete opening-guide and map names with every preceding translation layer.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_GUIDE_NAME=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/guide-name-pilot}"
exec bash tools/build_map_names_pilot.sh
