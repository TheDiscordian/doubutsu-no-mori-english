#!/usr/bin/env bash
# Complete message-system diagnostic using its guarded native continuation.
set -euo pipefail
cd "$(dirname "$0")/.."
AF_TRANSLATIONS=build/message-diagnostic-candidates/translations.json \
AF_ITEM_RESOURCE=build/design-items-resource \
AF_CREATOR=build/design-items-creator \
AF_BUILD_OUTPUT=build/message-diagnostic-pilot \
exec bash tools/build_seasonal_pilot.sh
