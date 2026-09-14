# V3 shared furniture-grid checkpoint

## Completed batch

The native sequential furniture-index builder and occupied-cell item-map builder
now include selected imports. Their original traversal, complete item IDs,
rotations, and shared footprint calls remain intact. The native shop predicate
recognises the verified donor groups for both static pilots. The unchanged
action-sound fallback matches both donors' no-sound profiles.

The [specification](../../specs/V3_FURNITURE_FIELDS.md) records entry points,
donor proof, memory bounds, and evidence limits. Inventory/acquisition, catalogue,
remaining outside-field consumers, ordinary placed actors, and save/profile work
remain in the V3 queue. Both patchers and the stable V2 cartridge are unchanged.

## Build and focused checks

```sh
python3 tools/v3_asset_loader.py --furniture-fields --output build/v3-furniture-fields-01
python3 -m unittest tests.test_v3_furniture_fields -v
```

All four focused checks pass without skips. The current combined cartridge is
`build/v3-furniture-fields-01/animal-forest-v3-asset-loader.z64`, SHA-256
`bc1d9f5217a01bd62d5628e5a0a666667baaa1df565faa2cdbba9e14e28f0925`.
Its adjacent UPS has SHA-256
`3bc3b5ec33fba183680becfd97fb1a206d4b63d1ab97072ef5f9e3ed065ac09e`.
V3 ABI 8 retains 49,152 resident bytes and a 60,560-byte ROM file. The new
252-byte helper has SHA-256
`cb4d296981eaa9f8a50e0e45f48d915f3ead87d26c119aa14e467a4052e5f8ba`.
The preceding 4,436-byte room code is unchanged; its recorded native detour
proof is retained, not replayed. Generated assets and cartridge outputs remain
ignored. No release or web-patcher update is performed.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-fields-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-fields-native-01 \
  --scenario tests/scenarios/v3_furniture_fields.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes all 56 recorded steps. It calls both complete native
grid functions on two layers, compares every output cell, checks sequential
indices across layers, and retains each placed item/rotation value. The inputs
mix original furniture, both static imports, and a rejected `3000` item. A second
selection configuration disables the oil drum and verifies omission without
corrupting either layer's numbering or unrelated cells.

Both import shop predicates, original Halloween/event fallbacks, and actual
native no-action-sound results pass. Source grids, the complete resident prefix,
allocation/stack/translation guards, and the faulted-thread check pass. The
checkpoint restores successfully and the game resumes. No setup retry is needed;
harness construction stays within the 30-minute batch allowance.

The isolated blank cartridge uses private Xvfb and disabled physical audio.
No game-save or Controller Pak write function runs; existing saves remain
untouched. Ordinary inventory, rendered/colliding furniture, acquisition,
imported-item save/reload, and hardware compatibility are not claimed.
