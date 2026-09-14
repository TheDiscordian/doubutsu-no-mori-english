# V3 feng shui checkpoint

The [feng shui adapter](../../specs/V3_FENG_SHUI.md) connects actual donor colours
to native item/room evaluation. Current cartridge:
`build/v3-feng-shui-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `3a99e5fd7870b7d03a3dbcd203f41a8dc9dd4069cccddf8d65e15c06ba5831ce`.
- UPS SHA-256: `e97205df05f35cfdf8c8947d77e28cc87fafd6cddf84bed083a148e0ea177655`.
- Expanded owner: 6,400 bytes, SHA-256 `20dd24c908e6e7cedfdfef5eeadbb2b1cb82cc562104f48e7b4eabfa5ebff9b4`.
- Relocation: 80 bytes, SHA-256 `0b7932a711aeb8018975e145c57be200c19766942284be0030779e0b216bc11c`.
- Suffix: 2,784 bytes, SHA-256 `ae8990009cf6b3e330b359b98e360267ffe0db21fc3e05c681b9919bb59ab1e1`.
- Metadata SHA-256: `6c5c56d5a5582f3691bacc60827c92ae4df51ed3500fe26600d2765f7db6a857`.
- ABI 20; unchanged permanent allocation, saved format, and complete HRA image.

```sh
python3 tools/v3_asset_loader.py --feng-shui --output build/v3-feng-shui-02
python3 -m unittest discover -s tests -p test_v3_feng_shui.py -v
python3 tools/emulator_smoke.py \
  --rom build/v3-feng-shui-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-feng-shui-native-01 \
  --scenario tests/scenarios/v3_feng_shui.json --expansion-pak \
  --no-initial-screenshot --seconds 120 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first construction attempt rejects an assumed equality between native and
donor point tables. Actual comparison establishes identical direction masks and
money weights, but four-times-larger GC item-luck weights. The converter checks
this relationship explicitly and retains native balance. No ROM is produced by
the rejected attempt.

All three focused checks pass. The initial combined check's HRA-retention tail
compares a generated assembly hash containing the fresh output-directory path;
that test assumption is corrected and only the affected test is rerun. HRA's
actual code, metadata, relocation, scheduler changes, and other report facts
remain identical. No game-code correction or native retry is needed.

The focused checks cover every native metadata row; empty, single-item, both-item,
and reversed selections; the actual donor/native rule relationship; duplicate
rejection; exact code/allocation changes; source ownership; retained DMA indices
and adjacency; rejected scheduler reuse; complete composition/UPS reconstruction;
retained HRA; and exact import-free V2.

The first native attempt passes **45 steps, eleven native calls, and 26 assertions**:

- Actual native loading/relocation produces the complete expected image.
- Five complete single-item evaluations cover original red furniture, imported
  red on east/west sides, and imported orange on north/south sides. Rotations,
  footprint lookup, and native money/item-luck contributions are correct.
- Three complete two-layer room evaluations cover native plus both imported
  furniture, a disabled oil drum, an unknown `3000` ID, and the empty-room
  fallback. Final totals include native halving/rounding, not GC weights.
- Complete code/metadata, the resident prefix, all fixture/stack/translation
  guards, and the clear fault pointer pass. Live owner/power globals are restored,
  the fixture freed, and checkpoint restoration and graceful exit pass.

Harness construction/debugging remains within thirty minutes. No physical audio,
user-save modification, FlashRAM/Pak write, whole-house scheduler invocation,
ordinary controls, or original-hardware test occurs. Earlier HRA/shop/catalogue/
persistence evidence is retained for unchanged code, not replayed.

Next: combined ordinary acquisition/payment/model removal, placement/pickup,
and persistence, then villager houses/selection and Controller Pak transport.
No complete import is enabled yet. V3 source may be pushed to GitHub; public and
local web patchers remain V2 until user testing and explicit approval.
