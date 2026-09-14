# V3 shared furniture item-reader checkpoint

## Completed batch

The haz-mat barrel and oil drum now have installed full sixteen-byte names,
furniture-leaf classification, actual donor price values, size queries, and
complete 1×1 placement-footprint records. Readers reject disabled profiles and
unsupported imports. Original item handling retains its complete native/V2
function bodies through checked return bridges.

The [specification](../../specs/V3_FURNITURE_ITEMS.md) records the metadata,
entry points, RAM layout, and remaining caller integration. A footprint reader
does not establish a working placed actor. Acquisition, ordinary inventory,
placement/pickup/rendering, catalogue/scoring, and saved-item/profile support are
still pending. Neither web patcher changes, and no playtest release is cut.

## Build and focused checks

```sh
python3 tools/v3_asset_loader.py --furniture-items --output build/v3-furniture-items-01
python3 -m unittest tests.test_v3_furniture_items -v
```

Construction succeeds. The combined 32-MiB cartridge is
`build/v3-furniture-items-01/animal-forest-v3-asset-loader.z64`, SHA-256
`6cc7f9d714fd09ca7c1721a054cde93508b2d73823ce238baa9017a399ee9cb6`.
`asset-loader.ups` has SHA-256
`38e7d058ecb752e971b3e6a0969c2ac0bca2c61388caa033eed42819a1a11cce`.
`build.json` records source, compiler, metadata, original-entry, bridge, and output
hashes. Generated assets, ROM, patch, and reports stay ignored.

All **four focused tests pass**, without skips in the completed run. They cover
sanitized helper execution, complete actual donor metadata, installed entries
and unchanged original bodies, bridge/layout bounds, CRC/configuration, exact
UPS/composition reconstruction, and import-free V2 retention. The initial host
fixture needed an explicit sixteen-byte copy instead of a string initializer
rejected by the host compiler's unterminated-string warning. No production code
change or warning suppression was needed for that fixture correction.

The resident reservation remains 32 KiB. Metadata uses 64 bytes, original-function
bridges use 80 bytes, and compiled item helpers use 700 bytes, SHA-256
`23eb898a81e9457ba67a50144e5351e1b8ff1c25104d6c3fa822d702a16b9fbe`.
V3 ABI 6 retains the loader's ROM-only model tail and original furniture banks.
The preceding furniture-loader native evidence is preserved, not replayed.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-items-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-items-native-02 \
  --scenario tests/scenarios/v3_furniture_items.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The corrected run passes **73 recorded steps**:

- Both imported names through the installed full-name entry, at an unaligned
  destination, including rotated IDs and complete padding.
- Both item types, donor prices, size queries, and all four footprint records.
- Invalid capacity/ID no-write cases and actual disabled-profile rejection.
- All five original-item fallbacks, including full name DMA, native footprint
  data, and the real transient price-resource allocation/read/free path.
- Resident prefix and adjacent allocation/stack/translation guards remain
  intact; no faulted thread appears. Checkpoint restore and resumed execution pass.

The first native attempt in `build/v3-furniture-items-native-01` passes the import
checks but stops at an incorrect original-price expectation. The fixture had
read VROM `011F8000`, which contains unrelated artwork. The actual native
`LUI 011F` / `ADDIU -8000` pair selects `011E8000`; its first price is 41,240,
exactly the native function's returned value. Correcting that fixture address
uses the single permitted setup retry. The cartridge and runtime code do not
change between attempts. Both records are preserved; the failed run is not
reported as a pass.

Harness construction and correction stay inside the 30-minute batch budget.
Both runs use isolated blank cartridge storage, private Xvfb, disabled physical
audio, and no game-save/Controller Pak write calls. Existing saves remain
untouched. No ordinary inventory, placed actor, appearance/collision, save/reload,
or hardware verification is claimed.

The existing loader fixture's bank-selector arguments are corrected to
`(index, game, item)` for future use. Its preceding recorded calls supplied zero
as the static item argument; those profiles have no item-dependent callback.
That fixture-only correction does not invalidate the recorded complete model
transfer or bank-lifetime evidence and does not trigger an old-build replay.

## Next integration

Connect the native-range checks and inline index conversions in room creation,
inventory/field handling, pickup, catalogue/scoring, mail articles, and saved
dependencies. Then exercise an actual placed pilot and its ordinary acquisition/
save cycle. The native constructor and index-reader locations are recorded in
the specification. Imported villagers' houses and the remaining Punchy clothing/
animated furniture dependencies remain part of the complete V3 work.
