#!/usr/bin/env bash
# Complete integration with the four-line save-preserving gyroid default.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/gyroid-default-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_GYROID_DEFAULT=build/gyroid-default-actor \
AF_BUILD_OUTPUT=build/gyroid-default-pilot \
exec bash tools/build_seasonal_pilot.sh
