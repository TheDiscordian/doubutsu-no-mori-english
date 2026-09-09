#!/usr/bin/env bash
# Complete shop item names plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_SHOP_ITEMS=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/shop-item-names-pilot}"
exec bash tools/build_town_suffix_pilot.sh
