# Fishing-tournament artwork

Match the English GameCube fishing-prop design while keeping the N64 event and
remaining models. The English source removes the printed `魚政` name from the
barrel and removes the small `本部` headquarters placard from the model. The GC
T3 atlas still contains `本部`, but no GC triangle uses that rectangle. Merely
copying the atlas leaves a Japanese sign visible in N64.

## Bound sources and readers

Native left/right structure types are `25`/`26`, with object slices
`8C7A8..8E828`/`8A738..8C798` in `D5E000`. Both seasons select the same two
resources, not four separate originals. Their palettes are `D5C168`/`D5C188`.
The actual current loader reads the matching prefix at `03D00000`.

The GC source T1/T3 images are `.data:5B69E0`/`5B79E0`, both 128×32 CI4, palette
`5B69C0`. The native targets are `DEB028`/`DEC028` on the left and
`DE8F98`/`DE9F98` on the right. All visible colours match. T1 texture consumers
have 48/46 native vertex uses matching the supplied GC arrays. Preserve every
native vertex, flag, normal, triangle, and the T2 atlas unless explicitly below.

The GC left/right T3 vertex fixups at `5B888C`/`5B8F34` resolve to
`5B8690`/`5B8D38`. Each contains sixteen vertices: native T3 vertices 0–11 and
16–19, with unchanged positions, UVs, and lighting. The six GC triangles are
`0,1,2; 3,4,5; 6,7,8; 9,10,11; 12,13,14; 12,14,15`. The four omitted native
vertices 12–15 are exclusively the Japanese headquarters placard.

Replace only each native placard triangle-pair command at object offset
`8CFF0`/`8AF60` (`06181A1C00181C1E`) with the independently compiled native
`gsSPNoOp()` (`E000000000000000`). Keep the original twenty-vertex load and
remaining triangle indices; the four unused vertices need not be erased or
relocated. Every retained triangle must match the source geometry, UVs, and
lighting. This changes two draw commands, not CPU/event/collision/save code.

## Installation and accounting

Install both T1/T3 atlases and the two no-op commands in `D5E000` and the active
prefix at `03D00000`. Preserve both extended Nookington slices, all other 92
building-range reads, native slot sizes, allocations, and every prior resource.
Reconstruct the complete UPS, retaining the English title separately.

Inventory `魚政` and `本部` for each original left/right resource: eight source
characters across four records. Seasons and duplicate storage add no source
IDs. Their verified language-neutral GC replacements receive explicit
source-bound artwork-omission credit, not fabricated English string bytes.
The still-present but unreferenced `本部` pixels are not a player-facing reader.
Credit requires both actual texture copies, removal of only the designated
placard triangles, current seasonal/palette/structure readers, and retained
native event code. Older builds retain these source records without credit.

Use a focused source/command/geometry/retention/counter batch and one title
combination check. Do not repeat ordinary fishing gameplay or create another
native harness for the unchanged event/asset-loading code. The human playtest
still verifies ordinary scene appearance and the fishing event.
