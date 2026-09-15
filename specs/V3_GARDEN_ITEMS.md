# Garden decorations

## Scope and identity

Six GAFE01-r0 decorations have complete N64 graphics conversion and verified
donor metadata. They are not installed or selectable yet. The current cartridge
and both served web patchers remain unchanged by this source-conversion batch.

`tools/v3_furniture_art.py --batch garden` verifies the complete pinned REL and
symbols, both actual furniture-quality tables, profiles, names, and all graphics
relocations. `tools/v3_garden_items.py` binds the prices, full HRA/feng shui
records, unique membership across all 23 acquisition lists, and actual catalogue
positions/preview modes. The pinned identity worksheet corroborates that all six
lack AF identity/name/model/texture entries; it is not executable game source.

| Donor ID | Index | Name | Price | Acquisition | Object bytes |
| --- | ---: | --- | ---: | --- | ---: |
| `3268` | 1178 | birdhouse | 1,620 | ordinary B | 4,048 |
| `3284` | 1185 | bird feeder | 1,260 | ordinary C | 3,840 |
| `3290` | 1188 | Mr. Flamingo | 1,530 | ordinary B | 3,680 |
| `3294` | 1189 | mailbox | 4,000 | post office | 3,456 |
| `32A0` | 1192 | garden gnome | 3,380 | lottery | 3,728 |
| `32A4` | 1193 | Mrs. Flamingo | 1,530 | ordinary A | 3,680 |

The indices are donor furniture indices, not an assertion of installed native
IDs. A future registry reservation must remain independent of checkbox order.
The mailbox is decorative furniture, not the player's operational mailbox.
Neither the mailbox nor the gnome may be silently added to ordinary goods lists.

## Complete graphics

All six profiles have a single opaque model, height 42.43, scale 0.01, 1×1 shape
4, collision kind 0, lighting flag 1, and no skeleton, texture animation, or
callback table. Preserve the exact float/scalar data. Bird-feeder assets use
`int_yaz_b_feeder`, but its vertex symbol is `int_yos_b_feeder_v` and profile is
`iam_yos_b_feeder`; verify these actual relocations rather than fixing spelling.

The converter retains 406 vertices, 251 triangles, 24,448 CI4 texels, and all six
16-entry palettes. Total native object size is 22,432 bytes. Each fits a 4-KiB
storage slot and the current 5,120-byte furniture bank. Asset capacity does not
establish available space for resident profiles or the final cartridge layout.

Some clamped textures have heights 40, 48, or 56. Use the actual height in the
native load/tile size and zero T mask. A floor-log2 mask would wrap the image at
32 pixels. Repeated or mirrored axes must remain powers of two; reject unsupported
dimensions instead of cropping/padding without review.

The explicit garden parser mode admits only the reviewed clamp, S-mirror, and
T-repeat settings, plus five verified shape/extent combinations. Birdhouse's
standalone `D280F800` means explicit GX C4 with mirrored S using the current
32×40 image. Convert it to a native tile update, reset its implicit size, and
retain the following explicit 64×40 extent. Never emit the Dolphin command into
an N64 display list. Other parser modes keep their existing restrictions.

## Gameplay distinctions

Five items belong to donor backyard series 56. The existing expanded HRA storage
has a disabled placeholder there; supply its real theme definition and complete
English score-letter name before enabling these items. Donor surface index 26
is not automatically a native wall/floor match.

| Item | Donor HRA | Native layout | Feng shui |
| --- | --- | --- | --- |
| birdhouse | `E0058100` | `E0058200` | `0000` |
| bird feeder | `E0058200` | `E0058400` | `0000` |
| Mr. Flamingo | `E0050100` | `E0050200` | `0001` |
| mailbox | `D405D300` | pending category support | `0500` |
| garden gnome | `E0054780` | `E0054F00` | `0001` |
| Mrs. Flamingo | `E0050000` | `E0050000` | `0001` |

Keep face/lucky/surface bits and feng shui facing penalties, not just colours.
The gnome is lucky and placeable on a surface. The mailbox uses post-office birth
category 19, absent from the native point-table/counter contract. Its prepared
metadata deliberately leaves native HRA null until the complete evaluator is
adapted; writing index 19 into the existing path is not safe support.

## Integration work

Install fixed registry entries, expanded static/item records, complete model
resources, selected stock/event acquisition, catalogue/ownership, rewards,
scoring, save dependencies, and optional composition. Preserve existing content
and the import-free V2 result. Verify changed native readers and representative
model/gameplay paths with bounded testing; do not replay unchanged old builds.

The [checkpoint](../docs/checkpoints/V3_GARDEN_ITEMS.md) owns artifact hashes and
executed evidence. Both patchers remain V2 until user testing and explicit approval.
