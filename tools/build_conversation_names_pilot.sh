#!/usr/bin/env bash
# Complete conversation identity names with all preceding translation layers.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_TEXT_EXTENSION="${AF_TEXT_EXTENSION:-build/text-names}"
export AF_CONVERSATION_NAMES=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/conversation-names-pilot}"
exec bash tools/build_fishing_name_pilot.sh
