#!/usr/bin/env bash
# Full festival/reserve display names and every preceding integration.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_ENGLISH_ACTOR_NAMES=1
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/actor-names-pilot}"
exec bash tools/build_text_choices_pilot.sh
