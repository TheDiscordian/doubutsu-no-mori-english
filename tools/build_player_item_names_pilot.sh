#!/usr/bin/env bash
# Complete capture/dig names plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_PLAYER_ITEMS=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/player-item-names-pilot}"
exec bash tools/build_shop_item_names_pilot.sh
