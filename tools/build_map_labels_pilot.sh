#!/usr/bin/env bash
# Complete map landmarks, resident names, and every preceding translation layer.
set -euo pipefail
cd "$(dirname "$0")/.."
export AF_MAP_NAMES="${AF_MAP_NAMES:-build/map-labels-overlay}"
export AF_BUILD_OUTPUT="${AF_BUILD_OUTPUT:-build/map-labels-pilot}"
exec bash tools/build_guide_name_pilot.sh
