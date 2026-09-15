# Garden decorations

## Scope and identity

Six GAFE01-r0 decorations have complete N64 graphics conversion, verified donor
metadata, and experimental runtime installation. The offline composer supports
individual selections. Post-office reward delivery and ordinary gameplay remain
unfinished; neither served patcher changes.

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

The registry assigns these same indices and additive item IDs independently of
checkbox order. Native identities and earlier imported identities remain intact.
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

Five items belong to donor backyard series 56. The installed HRA definition uses
theme type 2 and its full English score-letter name. Native surface FF explicitly
means no matching surface; donor surface index 26 is not an established native
wall/floor match.

| Item | Donor HRA | Native layout | Feng shui |
| --- | --- | --- | --- |
| birdhouse | `E0058100` | `E0058200` | `0000` |
| bird feeder | `E0058200` | `E0058400` | `0000` |
| Mr. Flamingo | `E0050100` | `E0050200` | `0001` |
| mailbox | `D405D300` | `D405E600`, checked ABI-63 prerequisite | `0500` |
| garden gnome | `E0054780` | `E0054F00` | `0001` |
| Mrs. Flamingo | `E0050000` | `E0050000` | `0001` |

Keep face/lucky/surface bits and feng shui facing penalties, not just colours.
The gnome is lucky and placeable on a surface. The mailbox uses post-office birth
category 19. The [reward-category adapter](V3_HRA_BIRTH.md) supplies its actual
points and expanded counters in ABI 63. The source-only metadata retains null
native HRA until an installer verifies that prerequisite; older evaluators cannot
safely accept category 19.

## Runtime storage and readers

`tools/v3_garden_runtime.py` installs ABI 64 on the complete ABI-63 source.
The six fixed object VROMs are `0235D000`, `0235E000`, `0235F000`, `02360000`,
`02361000`, and `02362000`, in the table's order. Each retains its own 4-KiB slot.
The fifteen 80-byte static rows occupy RAM `80481500..804819AF`. Sixteen 32-byte
item records occupy `80481A00..80481BFF`; copy all ten preceding records before
reusing their old storage. The existing package guard at `80481FF0` remains.
No permanent RAM or shared-menu allocation increases.

The actual clothing-aware item reader at `8046D000` retains every save-code
instruction and public symbol. Only its two table start/end operands change.
The static helper remains within its existing 2-KiB reservation. Both resource
CRCs, the checked startup prefix, DMA bounds, and N64 checksums are verified.
Every output must reconstruct completely through its UPS patch.

The catalogue contains 452 furniture and 248 clothing entries in the existing
753-slot pages. Its image occupies 62,288 bytes; conservative shared-menu use
is 279,936 of 280,704 reserved bytes. All original ordering and complete clothing
entries remain. The mailbox is visible but not orderable. The donor catalogue
permits lottery furniture, so the gnome remains orderable through native list 5.

Four garden items enter their true A/B/C lists. The gnome enters native lottery
list 5, whose thirty original items all retain birth category 7. Its first
terminator is at resource offset `334`, followed by two alignment bytes;
inserting after the first terminator would make the new item unreachable.
The mailbox is not added to a substitute stock list. Its reward delivery remains
an explicit unfinished acquisition route.

The HRA image keeps all ABI-63 counter instructions, weights, and relocations.
Only six metadata records and backyard's definition/name change. The feng shui
image changes only six records. The score-letter image grows by 32 bytes to
62,688, with a 57th complete 26-byte name record, six padding bytes, and the
unchanged 960-byte relocation format. Five counters and loader sizing/CRC change;
all original keys, boxing, templates, and unrelated relocated code remain.

Saved format 2 stays unchanged; the profile adds six furniture dependencies.
An older profile must reject these saves safely. The offline composer excludes
unselected HRA records from native grouping/recommendations as well as disabling
their runtime profiles. Imports are not a backwards-compatible V2 save format.

## Remaining work

Finish post-office reward delivery and ordinary acquisition, placement,
persistence, and player testing. Preserve the exact import-free V2 result.
Source conversion and callable native checks do not certify ordinary gameplay
or original-hardware appearance.

The [source checkpoint](../docs/checkpoints/V3_GARDEN_ITEMS.md) and
[runtime checkpoint](../docs/checkpoints/V3_GARDEN_RUNTIME.md) own artifact hashes
and executed evidence. Both patchers remain V2 until user testing and explicit approval.
