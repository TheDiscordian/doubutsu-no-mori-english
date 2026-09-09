#!/usr/bin/env bash
# Complete local integration recipe. Inputs and output ROM/patch remain ignored.
set -euo pipefail
cd "$(dirname "$0")/.."
gyroid_args=()
if [[ -n "${AF_GYROID_DEFAULT:-}" ]]; then
  gyroid_args=(--english-gyroid-default "$AF_GYROID_DEFAULT")
fi
hboard_args=()
if [[ -n "${AF_HBOARD_EDITOR:-}" ]]; then
  hboard_args=(--english-hboard-editor "$AF_HBOARD_EDITOR")
fi
inventory_args=()
if [[ -n "${AF_INVENTORY_ENGLISH:-}" ]]; then
  inventory_args=(--english-inventory "$AF_INVENTORY_ENGLISH")
fi
catalogue_args=()
if [[ -n "${AF_CATALOGUE_NAMES:-}" ]]; then
  catalogue_args=(--english-catalogue "$AF_CATALOGUE_NAMES")
fi
town_suffix_args=()
if [[ "${AF_ENGLISH_TOWN_SUFFIX:-0}" == 1 ]]; then
  town_suffix_args=(--english-town-suffix)
fi
shop_item_args=()
if [[ "${AF_ENGLISH_SHOP_ITEMS:-0}" == 1 ]]; then
  shop_item_args=(--english-shop-item-names)
fi
player_item_args=()
if [[ "${AF_ENGLISH_PLAYER_ITEMS:-0}" == 1 ]]; then
  player_item_args=(--english-player-item-names)
fi
exec python3 tools/build.py \
  --rom 'local/rom/Doubutsu no Mori (Japan).z64' \
  --translations "${AF_TRANSLATIONS:-build/native-items-candidates/translations.json}" \
  --english-keyboard --english-runtime --runtime-module build/notice-seasonal-runtime \
  --english-fortunes --english-resetti-replies --english-shop-units \
  --english-resident-words --english-shared-npc-words --english-credits --english-song-names \
  --english-dialogue-dates --extended-items "${AF_ITEM_RESOURCE:-build/native-items-resource}" \
  --display-names build/display-names --catchphrases build/catchphrases \
  --mail-catalog build/mail-glyph-resources --english-mail-layout \
  --english-mail-snapshots --english-mail-grading build/mail-grading-npc \
  --npc-mail-generation "${AF_CREATOR:-build/noticeboard-seasonal/creator}" --extended-font "${AF_EXTENDED_FONT:-build/mail-font-cartridge}" \
  --english-fortune-slips build/shop-notice-fortune --english-leaflet-dates build/leaflet-dates \
  --english-renewal-letters build/shop-notice-renewal --english-event-letters build/shop-notice-event \
  --english-mother-letters --english-departed-letters --english-villager-event-letters \
  --english-academy-letters --english-academy-scores --english-post-office-letters \
  --english-museum-letters --english-shop-notices build/shop-notice-owners \
  --english-snowman-letters build/shop-notice-snowman --english-secret-letters build/secret-actor \
  --english-quest-replies build/quest-reply-owners \
  --english-noticeboard build/noticeboard-seasonal/reader \
  --english-notice-treasure build/noticeboard-treasure/owners \
  --english-notice-seasonal build/noticeboard-seasonal/owner \
  "${gyroid_args[@]}" \
  "${hboard_args[@]}" \
  "${inventory_args[@]}" \
  "${catalogue_args[@]}" \
  "${town_suffix_args[@]}" \
  "${shop_item_args[@]}" \
  "${player_item_args[@]}" \
  --output "${AF_BUILD_OUTPUT:-build/notice-seasonal-pilot}"
