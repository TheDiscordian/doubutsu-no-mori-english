# Map and inventory artwork checkpoint

## Combined candidate

`build/inventory-artwork-02/animal-forest-halfwidth.z64` includes the English
map heading/acre layout, inventory headings, twelve shop textures, both
first-job conversation fixes, the Shrine correction, and all earlier English
resources. ROM SHA-256:
`15c7a2830f5a561a8470ba70bc4aaa907e65ab1ee5ebb921266df17e6b1cac3c`.
UPS SHA-256:
`96d64ffef20ab9e81ef051948ea9d4f538515b00bdf22c8a2edb09ac2cea42f5`.
The cartridge remains 32 MiB; RAM use remains four MiB. The title preview is
separate, and the original hardware-fix handoff remains untouched.

The map-only retained candidate is `build/map-artwork-01`, ROM SHA-256
`29576ea8bc82a55193a263b913a15ffe81554746a2cec5cdcff3bf84a26b6cdc`,
UPS SHA-256
`c667801c56d1fbc8e400f4a4356f36f6944930bada9998a0741393cb59692c56`.

## Implemented

- Map: exact GameCube TOWN MAP and Acre textures; source-sized heading and
  Acre label; selected letter/number on one line with the source separator
  position and colour. The row/column selectors themselves remain unchanged.
- Inventory: exact GameCube Items, Letters, and Bells textures and positions.
  The vertical native Items texture load becomes the correct horizontal load,
  with the donor heading colour. The redundant Japanese Bells unit and town
  suffix become transparent, matching the donor's separate actual-name drawing.
- All other asset bytes, palettes, CPU code, selection, state, allocation,
  saved data, and prior English resources remain unchanged. No texture, vertex,
  display-list, or DMA range grows.

[Map artwork](../../specs/MAP_ARTWORK.md) and
[inventory artwork](../../specs/INVENTORY_ARTWORK.md) record the exact bindings,
native commands, source positions, and live suffix caller.

## Checks and limits

All twelve focused artwork tests pass together in 21.641 seconds: five shop,
four map, and three inventory checks. The combined run covers the shared helper
changes as well as both new batches. It independently compiles the native GBI
commands in Docker, checks actual donor texture pointers, exact converted
pixels, coordinate scale/corners/winding, original vertex flags/colours,
palette equivalence, unchanged selectors and callers, complete cartridge
retention, and UPS reconstruction. Negative source, dimensions, pointers,
coordinates, and command cases reject. Scripts compile and the diff passes
whitespace checks.

These are host, binary-format, and compilation checks, not ordinary in-game
renders or original-hardware acceptance. No new full tutorial/menu harness is
constructed, and no user save is touched. The existing critical-fix native
evidence applies to the retained, unchanged conversation code. Normal screen
appearance/navigation remains an ordinary emulator/hardware check to combine
with the next completed screen batch.

## Time-setting source investigation

The [clock checkpoint](TIME_SETTING.md) records its implemented English display,
combined candidate, passing focused checks, and remaining collection headings.
The native boundaries below are retained as the source record.

The native time-setting owner is submenu index three, VROM `0078AE30`, linked
RAM `808831A0`, 4,272 bytes, SHA-256
`3aebd5b023d62567ff78fa5e808ced29740a0e2e569fa19f16896848c1b779cd`.
Its relocation is `0078BEE0`, 208 bytes, SHA-256
`3d4b0b08f913207dcaf8c20c1e8f5a24aea1cd10886d87def56dbc25e8ca969d`.
Sections are 4,128 code bytes, 144 data bytes, no rodata, 32 BSS bytes, and
46 relocation entries. Native disassembly is `build/disassembly/timein/code.asm`.

Its artwork file is `00A8E000..00A93EF0`, 24,304 bytes, SHA-256
`bab36b3c007b36412f6d8588c2c961afdfdcf655c34dd8e112561559cf312e7f`.
The owner stores those bounds at `80884248`. Clock and speech-bubble art match
known supplied GameCube textures; the remaining words below are plain glyph
bytes in the owner, not baked textures:

| Address | Length | Native text |
| --- | --- | --- |
| `808841E0` | 9 | `じかんをあわせてね` |
| `808841EC` | 14 | `20  ねん  がつ  にち` |
| `808841FC` | 5 | `じ  ふん` |
| `80884204` | 3 | `おわり` |

The text-drawing function is `80883B40..80883E74`. It calls `80090E98` for
these four strings and the five two-digit editable values; native formatting
is at `8009264C`. Values live through submenu offset `2C`, overlay offset
`106F4`; its selection index is `0C`. Field positions at `80884220` are
year `(104,115)`, month `(146,115)`, day `(188,115)`, hour `(93,137)`, and
minute `(124.5,137)`. Native string lengths and manual spacing cannot simply
be reused with halfwidth English labels. Retain actual time changes, selection,
save/RTC logic, and clock animation; change only display/translation routes.

The supplied GameCube `m_timeIn_ovl.c` and `tim_win.c` describe the English
layout. Its month and weekday artwork is separate and is not automatically
available to the native reader. Finish the display implementation before
claiming those resources as applied. Add these newly identified embedded
Japanese records to the combined progress inventory with installed-route
checks when applying their English replacements. The quick progress question
still uses the single existing counter, never an improvised bank-only figure.

Other pending artwork includes inventory collection tabs, bags/signs, more
buildings, the title integration, and the GameCube-style keyboard. Keep the
human playthrough and actual gameplay bug corrections ahead of exhaustive
visual combinations.
