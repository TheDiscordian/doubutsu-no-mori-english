# V3 catalogue checkpoint

The [catalogue adapter](../../specs/V3_CATALOGUE.md) connects collected imports
to the catalogue list, complete names, selection, previews, completion, and
prices. The current cartridge is
`build/v3-catalogue-04/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `b59114172c60daafdc4d6664fc541f395f6e6f66aa131d018a20ec6ff5665922`.
- UPS SHA-256: `dd507337ac6bce1bfaa75d49f968206f111b74326f8026dcb84edbfce76bc192`.
- Catalogue: 55,824 bytes, SHA-256 `9c9a314f81e7a329e4bb60e2529520fc8b22a9a2db64c9229033b35392f627d3`.
- Relocation: 688 bytes, SHA-256 `59c59abccc55a06b2a143e2fffb469f85ee46ae58278dd6159f58aa0be71d934`.
- Compiled suffix: 2,144 bytes, SHA-256 `939d5d48e1765b7d8fc66d22d7e1c2e8b9172f292f614613508950c7cb24176e`.
- Conservative menu use: 273,408 / 274,560 bytes, with no added reservation.

```sh
python3 tools/v3_asset_loader.py --catalogue --output build/v3-catalogue-04
python3 -m unittest discover -s tests -p test_v3_catalogue.py -v
```

Construction and all four focused tests pass. Checks include original-row
preservation, distinct catalogue/room index encodings, donor order/mode/shop
membership, real category/pool capacity, complete compiled helper installation,
alignment, actual relocation, the current parent descriptor, unchanged save
helper, resized composition, UPS reconstruction, and exact import-free V2.
ASan/UBSan checks cover ownership, original fallbacks, static profiles, invalid
or disabled profiles, null preview rejection, and catalogue-local eligibility.

## Bounded native execution

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-catalogue-04/animal-forest-v3-asset-loader.z64 \
  --output build/v3-catalogue-native-03 \
  --scenario tests/scenarios/v3_catalogue.json --expansion-pak \
  --no-initial-screenshot --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The corrected cartridge passes 70 steps, including 14 native calls and 48
assertions. Actual native relocation matches the independent complete image.
The fixture substitutes only the entry-animation callback; list construction,
name-cache initialization, full preview setup, selection, and DMA run natively.

- With no imported ownership, neither item appears.
- Native collection calls record the rotated barrel and oil drum. Reopening
  produces the two actual item IDs in order, with complete sixteen-byte English
  names and an incomplete-collection indicator.
- Initial preview and changed selection use the two resident profiles and
  separate native model buffers. Every model byte, both prices, furniture draw
  type, timer, donor scale/position, and native viewing height match.
- With all native bits owned, initialization produces 438 rows and the complete
  indicator without exceeding the 444-slot category. The original furniture
  preview fallback also executes successfully.
- Resident code, catalogue code, buffer guards, and translation guards remain
  intact. Live player data, active pointer, import state, and segment/debug
  globals are restored. Checkpoint restoration and graceful shutdown pass.

No physical audio, GPU preview presentation, ordinary order/delivery, or
FlashRAM write is performed. The isolated cartridge flash remains blank.
Unchanged collection/FlashRAM results are reused, not replayed.

## Failed attempts and correction

The first construction stops on an incorrect installer-relative entry offset;
the guard is corrected from `148` to `48`. Source review then finds the separate
selection classifier and adds its actual hook before native execution.

`v3-catalogue-native-01` stops before loading: its 180,224-byte test allocation
returns null at title boot. The fixture is reduced to 114,688 bytes by sharing
unused portions of its synthetic overlay-address window with owned code storage.
Only the fields actually read by the tested entries occupy that window.

`v3-catalogue-native-02` loads the unpadded development image and encounters a
native DMA alignment fault. The fixture places relocation storage immediately
after the image, at `802EA46C`, which is not eight-byte aligned. This is not proof
that ordinary catalogue opening crashes: the normal program-overlay loader
allocates relocation separately. The image is padded from 55,820 to 55,824 bytes,
and construction now requires 16-byte alignment. The next execution targets
that corrected cartridge and passes. No further native replay is queued.

Harness work stays under 30 minutes. These attempts do not establish an ordinary
shop playthrough, save compatibility beyond prior evidence, or hardware approval.
Both public and local patchers, user saves, and the released trailer are unchanged.

## Next implementation

Finish ordinary stock/acquisition and scoring, catalogue order/payment and
complete imported-name delivery letters, placement/persistence, houses/move-in,
and Controller Pak transport. No complete import is selectable yet. The broad
English-donor import goal remains active; these two pilots do not replace it.
