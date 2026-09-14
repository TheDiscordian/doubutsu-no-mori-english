# V3 complete gorilla model conversion

## Scope and identity

`tools/v3_gorilla_art.py` converts the actual GAFE01-r0 gorilla model used by
Yodel, donor index 229. The donor draw-row relocation must bind
`cKF_bs_r_gor_1`, whose relocation binds all 26 records in
`cKF_je_r_gor_1_tbl`. Twelve records draw models. Source ROM, REL, and symbol
hashes use the existing V3 pins. No original N64 model is overwritten.

The donor has 429 vertices; the native gorilla has 431. Their vertex order,
positions, UVs, and normals differ. The pig-only coordinate adaptation is not
applicable. All 429 donor vertices are imported, changing only the recognised
matrix-transport flags to native zero flags. All 284 donor triangles, including
their partial vertex-cache loads and matrix assignments, are converted.

Joint child counts, flags, and translations match the actual native gorilla.
The converted object retains the full donor hierarchy and can use that native
animation rig. This is source correspondence, not an executed animation test.

## Native graphics and storage

Every joint display list is generated as native F3DEX2 graphics and compiled
with the existing pinned Docker MIPS toolchain. No Dolphin texture command,
packed GameCube triangle command, or PowerPC pointer is copied into the output.

The full body atlas retains all 1,024 donor body bytes at verified native
destinations. Dynamic eyes, mouth, and shirt use `0280`, `0380`, and `04C0`.
Body/expressions use palette 15; clothing uses palette 14. Native tiles retain
actual clamp, repeat, or mirrored wrapping, coordinate masks, zero shifts, and
explicit extents. Converted display lists select preloaded native texture memory;
they do not load the donor's segmented texture addresses directly.

GX texture scale zero becomes native `FFFF/FFFF`. The exact donor opaque
render mode, colour combiner, white primitive colour, and lighting/geometry
state are retained. Unknown state values fail. Every joint establishes its own
state and starts with a pipeline sync; texture changes also sync. Identical
repeated settings within the same joint are omitted. An explicit tile extent
replaces the generated default extent rather than issuing both.

The complete object is 10,112 bytes, leaving 128 bytes in the verified
`2800`-byte native NPC model reservation. Its layout is:

| Region | Offset | Bytes |
| --- | --- | --- |
| 429 vertices | `0000` | 6,864 |
| Twelve native joint display lists | `1AD0` | 2,920 |
| 26 relocated joint records | `2638` | 312 |
| Skeleton header | `2770` | 8 |
| Zero alignment padding | `2778` | 8 |

All model/joint/skeleton pointers remain in segment 6. Matrix pointers remain
in segment 13 and within the twelve visible-joint matrices. The separate
`06002770` skeleton pointer must be used when assigning Yodel's new model bank;
the old native gorilla pointer `06002610` is not its replacement.

## Bundle and remaining integration

The body builder accepts `--models` pointing to this converter's verified
output. Its complete manifest and model hash are pinned. A missing, edited, or
corrupted model fails rather than falling back to the native gorilla. Yodel's
body entry includes this model, all fourteen expression frames, his actual body
and palette, and the already-converted `bag1` dependency at joint 13.

The complete component bundle contains all twenty added villagers and all
sixteen required accessories. Runtime bank assignment, accessory attachment,
voices/defaults/houses, town-compatible behaviour, and persistence remain work.
No move-in flag or browser option is enabled by conversion. The
[checkpoint](../docs/checkpoints/V3_GORILLA_ART.md) records actual outputs and tests.
