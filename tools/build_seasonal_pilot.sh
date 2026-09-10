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
event_item_args=()
if [[ "${AF_ENGLISH_EVENT_ITEMS:-0}" == 1 ]]; then
  event_item_args=(--english-event-item-names)
fi
stall_choice_args=()
if [[ "${AF_ENGLISH_STALL_CHOICES:-0}" == 1 ]]; then
  stall_choice_args=(--english-stall-choices)
fi
text_extension_args=()
if [[ -n "${AF_TEXT_EXTENSION:-}" ]]; then
  text_extension_args=(--english-text-extension "$AF_TEXT_EXTENSION")
fi
actor_name_args=()
if [[ "${AF_ENGLISH_ACTOR_NAMES:-0}" == 1 ]]; then
  actor_name_args=(--english-actor-display-names)
fi
map_name_args=()
if [[ -n "${AF_MAP_NAMES:-}" ]]; then
  map_name_args=(--english-map-names "$AF_MAP_NAMES")
fi
guide_name_args=()
if [[ "${AF_ENGLISH_GUIDE_NAME:-0}" == 1 ]]; then
  guide_name_args=(--english-guide-name)
fi
fishing_name_args=()
if [[ -n "${AF_FISHING_NAME:-}" ]]; then
  fishing_name_args=(--english-fishing-name "$AF_FISHING_NAME")
fi
conversation_name_args=()
if [[ "${AF_CONVERSATION_NAMES:-0}" == 1 ]]; then
  conversation_name_args=(--english-conversation-names)
fi
house_name_args=()
if [[ "${AF_HOUSE_NAME:-0}" == 1 ]]; then
  house_name_args=(--english-house-name)
fi
letter_name_args=()
if [[ -n "${AF_LETTER_NAMES:-}" ]]; then
  letter_name_args=(--english-letter-editor-names "$AF_LETTER_NAMES")
fi
reserve_args=()
apology_args=()
if [[ -n "${AF_APOLOGY_INPUT:-}" ]]; then
  apology_args=(--english-apology-input "$AF_APOLOGY_INPUT")
fi
if [[ "${AF_RESERVE_STRINGS:-0}" == 1 ]]; then
  reserve_args=(--english-reserve-strings)
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
  "${event_item_args[@]}" \
  "${stall_choice_args[@]}" \
  "${text_extension_args[@]}" \
  "${actor_name_args[@]}" \
  "${map_name_args[@]}" \
  "${guide_name_args[@]}" \
  "${fishing_name_args[@]}" \
  "${conversation_name_args[@]}" \
  "${house_name_args[@]}" \
  "${letter_name_args[@]}" \
  "${reserve_args[@]}" \
  "${apology_args[@]}" \
  --output "${AF_BUILD_OUTPUT:-build/notice-seasonal-pilot}"
