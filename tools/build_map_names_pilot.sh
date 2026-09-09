#!/usr/bin/env bash
# Complete map villager names and every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_MAP_NAMES="${AF_MAP_NAMES:-build/map-names-overlay}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/map-names-pilot}"
exec bash tools/build_actor_names_pilot.sh
