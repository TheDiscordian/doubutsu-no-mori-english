# English collection headings

Use the supplied GameCube Insects and Fish textures, preserving every pixel.
Keep the native collection pages, icons, capture records, selectors, and names.
The live headings are the larger `とったムシ` / `とったサカナ` images, not the
butterfly and fish tab icons. Those icons remain unchanged.

Both headings live in asset owner `00A30000`, 64,544 bytes. Require the complete
installed ordinary-inventory artwork profile before modifying this shared file.

| Label | Native slot | Capacity | Native load | Native quad | GC texture | GC model | GC quad |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Insects | `00A31D28` | 2048 | `00A31508` | `00A30980` | `004362C0` | `00438590` | `00437C80` |
| Fish | `00A3E438` | 2560 | `00A3D818` | `00A3CC40` | `00441080` | `00443AF0` | `004431C0` |

GC addresses are offsets in `.data`. Verify complete donor/symbol hashes and
each actual REL texture pointer. Insects is 80x16 I4 (640 bytes); Fish is 64x16
I4 (512 bytes). Untile without resampling and clear each slot's unused tail.
Replace only each existing 56-byte native texture load; use clamp with no S mask
for the non-power-of-two 80-pixel width, and preserve the native display-list
continuation. Independent Docker GBI compilation verifies the load commands.

Copy donor heading X positions, dimensions, and UVs, retaining native vertex
order, flags, and colours. Offset donor Y by -10 so its top remains at the native
heading's Y 64 inside the unchanged page frame. Both headings become 13 pixels
tall, matching the donor glyph scale. Copy the donor primitive colour. This is
an explicit native-frame placement adaptation, not a port of the full GC page.
No texture slot, display list, vertex range, DMA allocation, or CPU code grows.

Verify exact source conversion, transparent tail padding, non-power-of-two
texture-load dimensions, all quad corners and UVs, retained icons/other data,
complete prior cartridge contents, and UPS reconstruction. Normal collection
navigation and hardware appearance remain gameplay checks; unchanged loaders
do not need another standalone native harness for these two data-only headings.
