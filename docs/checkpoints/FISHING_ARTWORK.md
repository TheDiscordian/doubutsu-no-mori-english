# English GameCube fishing-prop adaptation

The separate `build/fishing-artwork-01` candidate removes the Japanese barrel
name and headquarters placard exactly as the English GC design does. It ports
the matching barrel and Chip-portrait atlases for both left/right configurations.
Both seasons reuse those same resources. The six remaining triangles in each
T3 model preserve native geometry, UVs, normals, and flags; two independently
compiled no-op commands suppress only the original placard triangle pairs.
The original twenty-vertex loads, CPU/event/collision/save code, and allocation
remain unchanged.

Untitled ROM SHA-256:
`ec2917b38e47e936b69b203ffa99913e7fedad9d4ae29e8c368db5441b64ed13`.
UPS SHA-256:
`a8f2aa39dfde503ad8114a23e0b0196230b7e3e55e97e64de44ef7f75c6b66c8`.
The title combination is
`build/title-fishing-combined-01/animal-forest-title-preview.z64`, SHA-256
`e33f2ead92de74a45a45db22cd8675ea271950d52ed6901f949acc4efbeb7f1e`;
its UPS SHA-256 is `e658d3f8a69270f74402dde226f19efaf386448b74d6b5ae54f0fa2bca018433`.
The combination requires an Expansion Pak and retains all previous translation,
conversation, menu, keyboard, title, Nookington, and dump work. The private
packaged handoff remains separate while remaining artwork continues.

Three focused tests pass in 8.035 seconds. They cover independent native macro
compilation, exact source textures/palettes/fixups, 94 barrel vertex uses, the
actual GC T3 vertex/triangle bindings, removal of only the designated placard,
every retained vertex and triangle, all 92 bounded streams, all other resources,
negative command/installation checks, prior artwork accounting, and complete UPS
reconstruction. The title combination check passes in 8.315 seconds. These are
not ordinary fishing-event gameplay or original-hardware acceptance.

The full counter successfully verifies the cartridge. The four original records
contribute eight source characters, with explicit verified language-neutral GC
artwork-omission credit. No English string is fabricated for omitted artwork;
the unused `本部` pixels are retained in the source atlas but no active triangle
draws them. The measure is 752,010 replaced source characters out of 752,032,
with the same twenty-two structural-tail characters remaining.

Continue the fortune booth and festival stall. The GC fortune-booth model has
51 vertices, two small textures, and thirty triangles; its visible bounds fit
inside the native booth's bounds. Its complete design appears small enough to
adapt within the unchanged native streamed slice, but no such adaptation or
acceptance is claimed here. The [fishing specification](../../specs/FISHING_ARTWORK.md)
records this completed batch's exact source and native limits.
