#!/usr/bin/env bash
# Retain all seasonal/runtime resources while installing the next full name batch.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/sheet-items-candidates/translations.json \
AF_ITEM_RESOURCE=build/sheet-items-resource \
AF_CREATOR=build/sheet-items-creator \
AF_BUILD_OUTPUT=build/sheet-items-pilot \
exec bash tools/build_seasonal_pilot.sh
