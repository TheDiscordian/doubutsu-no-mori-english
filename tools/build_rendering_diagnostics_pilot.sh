#!/usr/bin/env bash
# Original rendering/sound diagnostics with the complete native-design build.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/rendering-diagnostics-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_BUILD_OUTPUT=build/rendering-diagnostics-pilot \
exec bash tools/build_seasonal_pilot.sh
