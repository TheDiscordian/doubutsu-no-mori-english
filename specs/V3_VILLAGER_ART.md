# V3 villager artwork conversion

## Implemented scope

`tools/v3_villager_art.py` converts the actual GAFE01 revision 0 artwork for
Punchy (`00EB`, `cat_15`) and Cheri (`00E8`, `cbr_11`) into N64 texture objects.
It retains the native cat/cub geometry and animation skeleton after verifying
their correspondence with the donor. This is an artwork component, not a
complete playable villager or an enabled browser option.

Explicit `--villager` selections also convert Pigleg (`00E9`, `pig_11`) and
Dobie (`00E0`, `wol_6`). These two islanders are artwork components only;
the default two-pilot conversion and current development ROM do not change.
Pigleg includes a separate converted model, not an overwrite of the native pig
model. With verified `--accessories` and `--models` directories, `--all-supported`
converts all twenty donor-only villagers. The sixteen accessory-bearing
entries include their actual separate accessory objects and attachment metadata.
Town behaviour, dependencies, and runtime installation remain required.

The donor disc/resources and symbol file use the pins in
`V3_OPTIONAL_IMPORTS.md` and `v3_import_catalog.py`. Actual REL relocations bind
the selected draw-table row to its skeleton, body, palette, all eight eye
textures, and all six mouth textures. Asset filenames alone are not identity
evidence. Unknown or missing pointer fields, external references, unsupported
palette alpha, or missing/unverified accessory objects fail construction.

## Native object layout

Cat, cub, and pig texture outputs are 5,664 bytes (`0x1620`):

- `0000–001F`: sixteen N64 RGBA5551 palette entries.
- `0020–0E1F`: fourteen 256-byte, row-major CI4 expression frames.
- `0E20–161F`: the 2,048-byte native body texture-memory image.

Cats store eight eyes followed by six mouths. Cubs store six mouths followed by
eight eyes. The existing native draw-record pointers determine that ordering;
changing it without matching pointers would animate the wrong facial features.
Wolves have eight eye frames and six null mouth pointers in both actual games.
Their complete object is 4,128 bytes (`0x1020`), with body data at `0820`.
Do not invent mouth frames or retain cat-sized expression offsets for wolves.

The GameCube CI4 data uses 8×8 tiled blocks. Expression frames untile to 32×16
row-major CI4. Body parts also untile, then swap the two 32-bit words in every
odd row, matching the N64 preloaded texture-memory representation. Apply this
row rearrangement separately to each tile, not across the whole body image.

The body image includes current-eye, current-mouth, and current-shirt areas.
Initialise eyes/mouths from the imported neutral frames. Initialise the shirt
area to zero; the native constructor/draw path must fill it from the new
villager's actual current clothing. Do not copy another villager's shirt.

| Species | GC body offset | N64 texture-memory byte offset | Dimensions |
| --- | --- | --- | --- |
| Cat | `000` | `200` | 32×32 |
| Cat | `200` | `600` | 16×16 |
| Cat | `280` | `680` | 16×16 |
| Cat | `300` | `700` | 16×32 |
| Cub | `000` | `000` | 16×8 |
| Cub | `040` | `140` | 16×8 |
| Cub | `080` | `180` | 16×8 |
| Cub | `0C0` | `1C0` | 32×32 |
| Cub | `2C0` | `3C0` | 16×8 |
| Cub | `300` | `500` | 16×16 |
| Cub | `380` | `780` | 16×8 |
| Cub | `3C0` | `7C0` | 16×8 |

Cat eye/mouth/shirt offsets are `000`/`100`/`400`. Cub offsets are
`400`/`040`/`580`. Every donor body byte and every output atlas byte is accounted
for exactly once, including the mutable areas. Bounds and overlap checks are
mandatory.

Pigs use 896 donor body bytes, not 1,024. Their source/native placements are
`000→000` (32×32), `200→300` (16×16), `280→480` (16×16), and `300→700` (32×8).
Eye/mouth/shirt offsets are `200`/`380`/`500`; native `780..7FF` is verified zero
padding. Wolves use all 1,024 body bytes: `000→000` (16×16), `080→080` (32×32),
`280→380`, `300→400`, and `380→480` (each 16×16). Their eye/shirt offsets are
`280`/`500`, and `700..7FF` is verified zero padding. The unused mouth offset
is zero, not a request to overwrite the first body tile.

Complete shared-pig and shared-wolf texture conversions reproduce their actual
native objects outside the mutable shirt: 5,152 and 3,616 bytes respectively.
These comparisons include every expression, palette entry, body placement, and
padding byte. Native model tile commands independently identify the listed body
dimensions and texture-memory destinations.

Palette conversion preserves opaque RGB555 values. RGB5A3 entries with binary
alpha convert to native RGBA5551; partial alpha requires another rendering path
and is rejected, not silently flattened.

## Additional species layouts

The converter supplies duck, rabbit, squirrel, frog, lion, penguin, elephant,
bird, mouse, horse, chicken, koala, and tiger layouts. Exact source offsets,
native destinations, dimensions, and expression order are in `LAYOUTS` in
`tools/v3_villager_art.py`, checked against both games' actual draw records and
model commands. Duck and lion, like cub, store mouths before eyes. Penguin,
bird, horse, chicken, and tiger, like wolf, have no mouth frames. Chicken has
64 bytes of native zero padding at `07C0`; it is not another source tile.

Some donor tiles include four extra rows for GX block alignment. These are
explicit mirrored or clamped edge extensions, not unique image content to
discard. `native_body_piece` regenerates every extension row from its visible
rows and rejects any differing pixel. Only then does it store the native height,
which is independently bound by the native tile commands. The full nineteen-body
batch accounts for 704 such repeated source bytes. All other source pixels are
stored directly; every native atlas byte remains assigned once.

`tools/v3_villager_mesh.py` decodes each real joint's two display lists, including
partial vertex-cache loads and matrix changes. It compares every face in order,
allowing only a cyclic permutation of a triangle's corners, never reversed
winding. Each corner retains its actual source vertex index and joint matrix.
Every body-material reference must match the declared source offset, dimensions,
native destination, and stride; mutable eye/mouth/shirt references are checked
separately. This establishes shared topology and texture bindings, not hardware
appearance or equivalence of every graphics-state command.

The [body checkpoint](../docs/checkpoints/V3_ISLANDER_BODIES.md) records complete
conversion and focused verification for the shared species. Yodel uses a
[separate complete gorilla conversion](V3_GORILLA_MODEL.md): all 429 donor
vertices, 284 triangles, matrix assignments, and 26 joints fit in 10,112 bytes.
Do not weaken the pig-only coordinate adapter or reuse the unrelated native
gorilla model for Yodel. His converted skeleton pointer is `06002770`.

## Shared model evidence

The N64 model banks are `0085` (cat, VROM `00EC5000`) and `009D` (cub, VROM
`00EF6000`). Their skeleton pointers are `06001CE8` and `06001EE8` respectively.
The donor binds Punchy to `cKF_bs_r_cat_1`, and Cheri to `cKF_bs_r_cbr_1`.

All 323 cat vertices and all 346 cub vertices match in position, texture
coordinates, normal/colour, and alpha. The sole vertex representation difference
is GameCube's shared/nonshared matrix flag at bytes 6–7; the retained native
vertices use zero there. The donor's emu64 vertex-loading implementation uses
that flag for its own matrix handling. The converter permits only observed
values zero/one and compares after normalisation; it does not import GC matrix
commands into the N64 renderer.

All 26 joint records match in child counts, draw flags, and translations. The
visible-joint patterns match: thirteen cat parts and twelve cub parts. Actual
REL pointers bind the donor joint table, and native segmented pointers remain
within the model object. Scale, talk type, and collision dimensions also match
the existing native species records.

Converting shared Bob artwork reproduces all 5,152 non-shirt bytes of his native
texture object, including the palette, every expression, and body placements.
The 512 mutable shirt bytes are deliberately excluded. Cheri's GC artwork is
not required to match another cub's differently coloured N64 textures.

Dobie's model retains all 374 native wolf vertices and 26 joints, with fourteen
visible joints; donor matrix flags are the only vertex representation change.
Pigleg needs different head coordinates: donor vertices 0–66 differ from the
native pig, while vertices 67–318 retain their coordinates. All 319 UVs,
normals/colours, alpha values, and vertex order agree after matrix-flag
normalisation. The converter imports those 67 coordinate triples into a
separate 7,360-byte copy of the native model. Every command, pointer, skeleton
byte, and non-position vertex field stays native. All 26 joints and twelve
visible-joint records match. The output report distinguishes comparison against
this converted model from comparison against an unchanged native model.

This coordinate adaptation does not globally resize existing N64 pigs. Its
model-bank assignment, actual runtime drawing, and appearance verification are
pending; texture conversion alone must not silently reuse the larger native
head. Accessory-bearing villagers fail conversion without the verified separate
geometry dependency. The separate
[accessory converter](V3_VILLAGER_ACCESSORIES.md) supplies all sixteen actual
accessory models, textures, and palettes. The body bundle includes all sixteen
dependencies for its supported bodies and records their exact consumer joints.
Runtime attachment still needs implementation before those villagers are playable.

## Native integration still required

The native draw table is DMA `00E05000`, with an eight-byte header and 100-byte
records. The GC table uses 108-byte records. Do not copy a complete GC record
into the smaller native destination or truncate its fields.

Original `ovl_Npc` is VROM `008681F0`, linked at `809735B0`. The draw-copy
function at `809809FC` calls index resolver `80980014`, reads
`00E05008 + index * 100`, then copies 100 bytes. Special-character records use
index `218 + special_id`; the two native test records precede them. Merely
inserting new ordinary villagers would redirect special characters to the wrong
data. Keep original special identities intact with an explicit extended lookup.
These are original link addresses, not assumed live addresses after relocation.
The [V3 native draw adapter](V3_NPC_DRAW.md) implements equivalent routes in
both NPC overlays and preserves the original special-character identities.

The native object table has 410 entries. The [V3 asset loader](V3_ASSET_LOADER.md)
preserves those entries and installs additional texture banks for Cheri/Punchy.
Use those assigned banks, not unchecked GC bank indices. Punchy/Cheri's donor
voice IDs are 286/285, while the native draw record holds a one-byte voice ID.
The draw adapter transfers these full IDs into the existing actor word; the
audio sequence engine still needs the corresponding wider lookup and sequences.

Roster/default/name/catchphrase/house readers, selection bounds, moves, dialogue,
mail, acquisition, and persistence remain part of the complete pilot. Verify
that clothing and animated expressions are populated through ordinary native
construction and drawing. No ROM, save, public recipe, or web option changes in
the artwork-only batch.
