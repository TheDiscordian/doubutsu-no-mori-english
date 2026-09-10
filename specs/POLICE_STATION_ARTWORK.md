# English police-station artwork

## Scope and retained behaviour

Import the supplied GameCube POLICE doorway lettering and wanted poster in both
seasons. Match GameCube's removal of the small Japanese wall plaque and the
separate Japanese notice sign. Keep every remaining building triangle's native
position, winding, and lighting. Do not change the actor, collision, doors,
palettes, allocations, or seasonal loader.

## Source bindings

The GameCube summer T1/T2 textures are `.data:00571C40`/`005724C0`, with native
destinations `00DAACF8`/`00DAB578`. Winter uses `00573B20`/`005743A0`, targeting
`00DACDC8`/`00DAD648`. All four are 128×32 CI4. The actual native palette table's
police entry is index `3B`, selecting `00D5BF08`/`00D5BF28`; matching donor
palettes are `00501620`/`00501640`. Never replace a shared palette.

T1's thirty native vertex uses already match the donor. T2's packing differs.
Native summer T2 loads 27 vertices at object offset `4BF88`; winter loads 24
at `4E088`. GameCube uses 23 vertices, indices 48–70 of arrays at `00572CC0`
and `00574BA0`. The removed native notice sign occupies four vertices and two
triangles, freeing enough existing space to use the donor's layout in both
seasons. No extended winter allocation is needed.

Populate the first 23 existing T2 vertices using donor texture coordinates and
the corresponding native positions, flags, and lighting values. The winter
source shares three roof corners that GameCube duplicates; duplicate the native
corner values while retaining native winter lighting. Keep the original vertex
load count and the unused tail. Replace seven two-triangle commands with the
donor's twelve triangles and one native no-op. Preserve the terminating command.
Compare oriented triangles using native position/lighting attributes: the result
must equal the complete old mesh minus exactly the notice sign's two triangles.

## Current resource ownership

The structure loader reads the expanded Nookington building resource at
`03D00000`, not the older `00D5E000` resource. Apply the same police prefix
changes to both, retain the complete appended Nookington slices, and verify
actual seasonal table reads. Preserve every other resource, including the
corrected shared keyboard hints and English SOLD OUT sign.

Independent native GBI compilation, source/palette/model bindings, exact retained
geometry, resource bounds, and UPS reconstruction provide the focused checks.
Ordinary scene appearance, lighting, and hardware acceptance remain separate.
