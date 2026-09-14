# V3 furniture icon checkpoint

## Completed implementation

The haz-mat barrel and oil drum use the original inventory leaf descriptor.
Only two instruction words change in the submenu parent. Gifts, gyroids,
fossils, textures, the renderer, allocations, and relocation entries are retained.
The [specification](../../specs/V3_FURNITURE_ICON.md) records the checked addresses
and full-register continuation. The 76-byte helper keeps the resident allocation
at 48 KiB. The source branch advances without changing either V2 web patcher.

## Build and focused checks

```sh
python3 tools/v3_asset_loader.py --furniture-icon --output build/v3-furniture-icon-02
python3 -m unittest tests.test_v3_furniture_icon -v
```

All three focused checks pass without skips. The current combined cartridge is
`build/v3-furniture-icon-02/animal-forest-v3-asset-loader.z64`, SHA-256
`b4351d0a0d1744c47163ca5697abc5240fce5e6d83bfbc99e10b6de1c60106b5`.
Its UPS has SHA-256
`de02cdb254e8570185d6da22ecab53b365422b8cfeadbb4b07876964c26e7c34`.
The helper SHA-256 is
`337afddcc4008a95f375e61725ff0c6f5906714990f7cf161f841a288aff60a6`.
Build 01 preceded the section-relative relocation-guard correction; build 02
binds the corrected installer. Generated ROMs, patches, and reports stay ignored.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-icon-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-icon-native-01 \
  --scenario tests/scenarios/v3_furniture_icon.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first native attempt passes all 59 recorded steps. Harness construction and
execution stay inside the 30-minute batch allowance, with no setup retry.

- The native loader reads and relocates the actual current parent and zeros its
  BSS. The complete 79,392-byte result matches the independent relocation model.
- Five windows verify full GPR, HI/LO, and floating-point register preservation
  for original furniture, both imports, a disabled oil drum, and an unknown ID.
- Six native selection paths resolve the expected leaf, gyroid, fossil, or gift
  descriptor while retaining item/condition arguments.
- Six calls execute the entire native icon renderer into isolated command
  storage. Both imports and the original furniture control emit 27 identical
  commands; their SHA-256 is
  `ce0f31770f45ff6c6eda7bd2fa35ae3582931222e67c6e13021476da319e08bb`.
  Gyroid, fossil, and gift output each remains distinct from that leaf output.
- The complete parent/BSS and resident prefix remain unchanged. Allocation,
  graphics, stack, and translation guards pass, with no faulted thread. The
  original parent pointer is restored, the fixture is freed, and checkpoint
  restoration/resumed execution pass.

No display list is submitted to the GPU. The test uses silent private Xvfb and
blank isolated storage; no existing save is read or modified. No ordinary
inventory interaction, item acquisition, room placement, save/reload, or hardware
acceptance is claimed. Existing passing menu/grid/room checks are reused for
their unchanged code rather than replaying previous builds.
