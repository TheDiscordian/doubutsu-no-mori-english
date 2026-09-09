#!/usr/bin/env bash
# Complete base integration with full inventory category and question text.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/gyroid-default-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_GYROID_DEFAULT=build/gyroid-default-actor \
AF_HBOARD_EDITOR=build/hboard-editor-overlay \
AF_INVENTORY_ENGLISH=build/inventory-menu-text-overlay \
AF_CATALOGUE_NAMES=build/catalogue-names-overlay \
AF_BUILD_OUTPUT=build/inventory-menu-text-pilot \
exec bash tools/build_seasonal_pilot.sh
