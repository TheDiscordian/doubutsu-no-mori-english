#!/usr/bin/env bash
# Complete world labels plus every preceding translation integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_EXTENDED_FONT=build/world-names-font
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/world-names-pilot}"
exec bash tools/build_tag_descriptions_pilot.sh
