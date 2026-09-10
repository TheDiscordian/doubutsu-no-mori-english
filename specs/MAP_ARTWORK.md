# English map artwork and acre coordinates

## Native and donor resources

The native map asset file is VROM `00AAD000`, 51,856 bytes, SHA-256
`f7c6357e60fb53825f58ecf2fc494c34642365bb0225791a07c3fc0024c1f66b`.
The map renderer installs it as segment twelve. This is not the map CPU overlay;
the full-name cache, English landmark labels, and corrected Shrine label remain
unchanged in their existing owner.

The native heading `ごあんない` is I4, 64 by 16, at `00AB4B60`.
Its supplied English donor is `kan_win_map_tex`, `.data:004B45C0`, used by the
actual model at `.data:004B9AF0`. The English `Acre` label is I4, 32 by 16, at
`.data:004B7EC0`, with model `.data:004B9B20`. Verify both actual REL texture
fixups and texture command dimensions against the pinned GameCube input.

## Layout

The native selected acre is displayed on two lines: row letter plus `ちょうめ`,
then column number plus `ばんち`. The GameCube layout places `Acre` above one
row-letter, separator, column-number line. Port the source positions, not just
the words, and do not swap the live row/column selectors.

The original N64 renderer scales these model coordinates by 0.1 at `8088F400`,
using the verified constant at `808900DC`; GameCube positions are already in
screen units. Multiply the source positions by ten when constructing native
vertices. Retain each native quad's vertex order, triangle winding, flags,
and vertex colour bytes. Match the source corners by geometry, then copy the
corresponding texture coordinates. The five affected quads are:

| Role | Native vertex VROM | GameCube vertex index |
| --- | --- | --- |
| TOWN MAP heading | `00AB3A90` | 0 |
| Acre label | `00AB3ED0` | 4 |
| Separator | `00AB3F10` | 8 |
| Selected column number, segment 8 | `00AB3B50` | 75 |
| Selected row letter, segment 9 | `00AB3E50` | 123 |

The GameCube vertex array starts at `.data:004B92C0`. The label sits at
X -98..-70, Y 8..22. The selected letter uses X -94..-74; the number uses
X -64..-44; both use Y -13..7. The separator is the source solid brown rectangle
at X -73..-65, Y -4..-1. Preserve its source colour `(85, 55, 55, 255)`.

## Native commands and bounds

Replace the former `ばんち` texture slot at `00AB8460` with the 256-byte Acre
texture and zero-fill the remainder of its 512-byte slot. Compile a 32-by-16
native I4 load in the existing 56-byte command space at `00AB48F8`; do not
stretch the 32-pixel donor over the former 64-pixel stride.

The former `ちょうめ` texture at `00AB8260` is no longer drawn and becomes
zero-filled. Its second label command area `00AB4940..00AB4998` contains a
48-byte native solid-rectangle display list, followed by unreachable zero
padding. `overlays/map/artwork.c` uses the pinned native GBI macros to generate
the commands; no GameCube extended display list is executable on the N64.
The separator's combiner and colour are explicitly set. The next dynamic
coordinate draw already sets its own combiner, texture, and colour.

No resource grows, and no CPU instruction, map selection, saved field, glyph,
map icon, resident name, landmark label, or memory reservation changes. Build
on the complete shop-artwork/hardware-fix image and check every retained DMA
resource and UPS reconstruction.

## Verification

Use focused source, palette-free texture, actual pointer, native GBI, corner/
winding, unchanged-data, and complete cartridge checks. Imported I4 pixels must
be exact, including all edges. Native command targets and load sizes must fit
their existing asset file. Ordinary appearance/navigation and hardware remain
separate checks; do not create another full tutorial or per-acre test matrix.
