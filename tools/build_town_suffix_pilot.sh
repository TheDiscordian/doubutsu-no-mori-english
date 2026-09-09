#!/usr/bin/env bash
# English town-name suffix plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_TOWN_SUFFIX=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/town-suffix-pilot}"
exec bash tools/build_world_names_pilot.sh
