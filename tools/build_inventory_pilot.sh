#!/usr/bin/env bash
# Complete base translation with the full inventory labels/name consumer.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/gyroid-default-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_GYROID_DEFAULT=build/gyroid-default-actor \
AF_HBOARD_EDITOR=build/hboard-editor-overlay \
AF_INVENTORY_ENGLISH=build/inventory-english-overlay \
AF_BUILD_OUTPUT=build/inventory-english-pilot \
exec bash tools/build_seasonal_pilot.sh
