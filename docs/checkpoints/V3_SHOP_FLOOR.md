# V3 shop-floor checkpoint

The [floor adapter](../../specs/V3_SHOP_FLOOR.md) connects the independent native
reserve-point, floor-item, and sold-furniture classification branches.
Cartridge: `build/v3-shop-floor-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `872dfb3e7bbb971665af4f2856e68e1bb01f4ea828ed1c0ca615e5c74e70acdd`.
- UPS SHA-256: `79f598a0eb7196b963fc0e163f73d86c11cf2cb7268741f118b78fedd9bb7055`.
- Helper: 340 bytes, SHA-256 `1eb2d07ce79d931c529967844455371b7076cdfd4a7b67e9eca3f60b13d02a84`.
- Installed owner SHA-256: `82ffd00c3c6617bf62d55e830c5729313327fe5ef45c6b1805769443cb864f7c`.
- ABI 18; unchanged 48-KiB resident prefix, actor allocation, and saved format.

```sh
python3 tools/v3_asset_loader.py --shop-floor --output build/v3-shop-floor-01
python3 -m unittest discover -s tests -p test_v3_shop_floor.py -v
python3 tools/emulator_smoke.py \
  --rom build/v3-shop-floor-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-shop-floor-native-01 \
  --scenario tests/scenarios/v3_shop_floor.json --expansion-pak \
  --no-initial-screenshot --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

Construction, three focused tests, and the first native attempt pass. No retry
or old-build replay is needed. Harness work remains within 30 minutes.
The focused tests bind the exact three changed words, retained delay words,
complete remaining actor/relocation/descriptor, rejected descriptor mutation,
helper/dependency/memory/guard bounds, startup CRC/ABI, composition, UPS
reconstruction, and exact import-free V2.

The native check records 63 steps, twenty native calls, and 35 passing assertions:

- Actual native load/relocation produces the complete expected actor.
- Fifteen branch cases cover each changed branch with native furniture, an
  original out-of-range value, both selected imports, and disabled oil drum.
  Full integer and floating registers, HI/LO, stack/return register, branch
  targets, and intended delay/annul effects match.
- Eight complete reserve selections return native furniture positions for both
  imports and existing furniture; unknown/disabled imports are rejected.
  Existing paper/sold-marker mappings and event priority remain correct.
- Eight complete floor selections execute native field existence, coordinate
  bounds, block indexing, and grid lookup using one isolated synthetic block.
  Selected imports retain their exact rotated IDs, original clothing/furniture
  remain readable, and unknown/disabled, empty, and sold items are unavailable.
  The empty-item case traverses the original branch into the retained delay
  instruction, verifying why the adapter changes only one word per site.
- Complete code and all heap/stack/translation guards remain intact; the fault
  pointer stays clear. Live pointers/status are restored, the fixture is freed,
  and checkpoint restoration/graceful shutdown pass.

No physical audio, user save, FlashRAM/Pak write, ordinary controls, payment,
graphics submission, or model-removal callback is involved. The removal branch
is exercised, not a complete played sale. Earlier stock, interaction, delivered
letter, catalogue, and persistence evidence applies to unchanged code and is
not replayed.

Next: room scoring, then combined ordinary acquisition/placement/pickup and
persistence; continue villager houses/selection and Controller Pak transport.
The two pilots and broader English-donor imports remain unfinished. V3 source
may be pushed to its development branch; both web patchers stay V2 until user
testing and explicit approval.
