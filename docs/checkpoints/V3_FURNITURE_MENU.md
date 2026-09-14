# V3 furniture menu checkpoint

## Completed implementation

The imported haz-mat barrel and oil drum now use the native furniture path for
the action menu, held-item destinations, and room-placement dispatch. Their
original imported IDs and rotations remain in the surrounding registers and
item fields. The [specification](../../specs/V3_FURNITURE_MENU.md) records exact
sites, parent/constructor lifetime assumptions, source guards, and remaining work.

The menu helper is 240 bytes at `8046A800`. ABI 9 retains the 48-KiB reservation,
model-tail layout, all prior helpers, and ordinary heap bounds. The current tag
file changes six instruction words without resizing its allocation or modifying
its relocation file. The parent owner remains unchanged. Both web patchers,
stable V2, existing saves, and the released trailer are preserved.

## Build and focused checks

```sh
python3 tools/v3_asset_loader.py --furniture-menu --output build/v3-furniture-menu-01
python3 -m unittest tests.test_v3_furniture_menu -v
```

All three focused checks pass without skips. The combined cartridge is
`build/v3-furniture-menu-01/animal-forest-v3-asset-loader.z64`, SHA-256
`f3d9435526c7c664b646729b1c4c380473ce64f00458453876b283b0f41e0aec`.
Its adjacent UPS has SHA-256
`1dbf2e44d7b8a821a2e11fb5ee3b3d6127c4ea9d5b5bb28749be28d16b1d1e7a`.
The compiled helper has SHA-256
`30c8d4713a2708e9a0c814dff013098e8e60231d6928e6414af4ef5e1c4a4c92`.
Generated ROMs, patches, source hooks, compiler output, and reports remain ignored.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-menu-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-menu-native-01 \
  --scenario tests/scenarios/v3_furniture_menu.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes 77 recorded steps:

- Twelve full-register window cases cover all three installed detours with
  original furniture, both selected imports, and a disabled oil-drum profile.
- Fifteen complete native held-item decisions cover five destinations for the
  original control and both imports. Only inventory and letter destinations
  accept held furniture; the complete held item/rotation is unchanged.
- The full action-menu selector returns identical furniture choices for the
  original control and both imports in each field context. Contexts 0–3 return
  menu types 1, 12, 8, and 8 respectively.
- Wrapped gifts retain menu type 11; quest items retain type 8.
- The complete resident prefix, complete tag image, allocation/stack/translation
  guards, and faulted-thread check pass. Checkpoint restoration and resumed
  execution pass.

The native loader reads and relocates the actual current tag owner. The fixture
supplies an isolated copy of the parent descriptor with its documented updated
constructor pointer; it does not run the complete submenu parent initialization.
No normal inventory interaction, full room-placement call, icon drawing, game
save, or imported-item reload is claimed. The isolated blank cartridge uses
private Xvfb and disabled physical audio. No existing save is read or modified.
Harness work stays inside the 30-minute batch allowance, without a setup retry.

## Next concrete reader

The native submenu parent has an independent leaf-icon type check at `8085C880`.
Its preceding mask at `8085C864` is in a branch delay slot. The intended next
adapter preserves that mask and the native gyroid/fossil/wrapped-gift branches,
then selects the ordinary furniture leaf descriptor at `8085DCF8` for a selected
import. The exact instruction context is preserved in
`build/disassembly/mail-submenu/code.asm` and the current parent source hash is
`3812a0538eead12ea59bc1826e8df7c6bd02e8575e0a3a36dfec31f717d262d3`.
This reader is not silently counted as completed menu work.

The native source also retains catalogue writes that only accept type 1 and use
the smaller furniture bitset. Do not redirect imported item numbers into that
bitset with unchecked arithmetic. Catalogue/persistence needs its own expanded
saved metadata and profile compatibility handling before acquisition is enabled.
