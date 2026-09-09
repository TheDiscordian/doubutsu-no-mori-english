#!/usr/bin/env bash
# Complete native designs, consistent native species, and existing runtime features.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/design-items-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_BUILD_OUTPUT=build/design-items-pilot \
exec bash tools/build_seasonal_pilot.sh
