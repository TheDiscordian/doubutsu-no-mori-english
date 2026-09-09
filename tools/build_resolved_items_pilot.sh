#!/usr/bin/env bash
# Keep every installed runtime feature with the resolved complete-name profile.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/resolved-items-candidates/translations.json \
AF_ITEM_RESOURCE=build/resolved-items-resource \
AF_CREATOR=build/resolved-items-creator \
AF_BUILD_OUTPUT=build/resolved-items-pilot \
exec bash tools/build_seasonal_pilot.sh
