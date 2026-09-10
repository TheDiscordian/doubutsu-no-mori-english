#!/usr/bin/env bash
# Complete ambiguous borrowed catchphrase display with all preceding translations.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_TEXT_EXTENSION="${AF_TEXT_EXTENSION:-build/text-catchphrases}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/borrowed-catchphrases-pilot}"
exec bash tools/build_letter_names_pilot.sh
