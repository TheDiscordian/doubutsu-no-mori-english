#!/usr/bin/env bash
# Complete event/home item names plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_EVENT_ITEMS=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/event-item-names-pilot}"
exec bash tools/build_player_item_names_pilot.sh
