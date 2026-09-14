# V3 furniture pocket checkpoint

The [pocket adapter](../../specs/V3_FURNITURE_POCKETS.md) includes selected
furniture in both complete shared inventory searches without changing saved data.

```sh
python3 tools/v3_asset_loader.py --furniture-pockets --output build/v3-furniture-pockets-01
python3 -m unittest tests.test_v3_furniture_pockets -v
```

All four focused checks pass without skips. The current combined cartridge is
`build/v3-furniture-pockets-01/animal-forest-v3-asset-loader.z64`, SHA-256
`0234ce93a2f1549880a5cce8811af0412c2448613336ea08db877e14782fcd6a`.
The UPS has SHA-256
`46199672ed7982a0ce3c099aa4be30e82d38f5229e50d9bcb5f972bc8225700b`.
The 372-byte helper SHA-256 is
`1f44ecfd6d9c4394e39a0025234316445cdd5d5ec7cedd65e5a7017b25dcebd7`.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-pockets-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-pockets-native-01 \
  --scenario tests/scenarios/v3_furniture_pockets.json --expansion-pak \
  --no-initial-screenshot --seconds 120 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes 51 recorded steps, including 28 complete native queries:
mixed original/imported pockets, slots 2/7/14, all four conditions, an invalid
condition, 16-bit type conversion, native empty/ordinary/raw-type-3/no-match
fallbacks, disabled oil drums, and null pointers. The complete private record
and resident prefix remain unchanged. Stack/allocation/translation guards and
the faulted-thread check pass. Checkpoint restoration and resumed execution pass.
Harness construction/execution stays inside the 30-minute allowance without a retry.

The test uses private Xvfb, disabled physical audio, and blank isolated storage.
No ordinary acquisition, save/reload, or hardware acceptance is claimed. Existing
saves, stable V2, both web patchers, and the trailer remain unchanged.
