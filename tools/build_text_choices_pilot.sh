#!/usr/bin/env bash
# Complete bounded choice substitutions and every preceding integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_TEXT_EXTENSION="${AF_TEXT_EXTENSION:-build/text-choices}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/text-choices-pilot}"
exec bash tools/build_text_extension_pilot.sh
