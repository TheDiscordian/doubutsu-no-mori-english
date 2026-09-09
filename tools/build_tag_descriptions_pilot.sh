#!/usr/bin/env bash
set -euo pipefail
export AF_TRANSLATIONS=build/gyroid-default-candidates/translations.json
export AF_ITEM_RESOURCE=build/design-items-resource
export AF_CREATOR=build/design-items-creator
export AF_GYROID_DEFAULT=build/gyroid-default-actor
export AF_HBOARD_EDITOR=build/hboard-editor-overlay
export AF_INVENTORY_ENGLISH=build/tag-descriptions-overlay
export AF_CATALOGUE_NAMES=build/catalogue-names-overlay
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/tag-descriptions-pilot}"
exec bash tools/build_seasonal_pilot.sh
