# V3 villager artwork conversion

## Implemented scope

`tools/v3_villager_art.py` converts the actual GAFE01 revision 0 artwork for
Punchy (`00EB`, `cat_15`) and Cheri (`00E8`, `cbr_11`) into N64 texture objects.
It retains the native cat/cub geometry and animation skeleton after verifying
their correspondence with the donor. This is an artwork component, not a
complete playable villager or an enabled browser option.

The donor disc/resources and symbol file use the pins in
`V3_OPTIONAL_IMPORTS.md` and `v3_import_catalog.py`. Actual REL relocations bind
the selected draw-table row to its skeleton, body, palette, all eight eye
textures, and all six mouth textures. Asset filenames alone are not identity
evidence. Unknown or missing pointer fields, external references, unsupported
palette alpha, or accessories that need separate geometry fail construction.

## Native object layout

Each output is 5,664 bytes (`0x1620`):

- `0000–001F`: sixteen N64 RGBA5551 palette entries.
- `0020–0E1F`: fourteen 256-byte, row-major CI4 expression frames.
- `0E20–161F`: the 2,048-byte native body texture-memory image.

Cats store eight eyes followed by six mouths. Cubs store six mouths followed by
eight eyes. The existing native draw-record pointers determine that ordering;
changing it without matching pointers would animate the wrong facial features.

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

Palette conversion preserves opaque RGB555 values. RGB5A3 entries with binary
alpha convert to native RGBA5551; partial alpha requires another rendering path
and is rejected, not silently flattened.

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
The second NPC overlay also needs its equivalent path reviewed.

The native object table has 410 entries. Added texture banks need a verified
extension or lookup route, not an unchecked GC bank index. Punchy/Cheri's donor
voice IDs are 286/285, while the native draw record holds a one-byte voice ID.
Investigate and port the appropriate voice mapping instead of truncating it.

Roster/default/name/catchphrase/house readers, selection bounds, moves, dialogue,
mail, acquisition, and persistence remain part of the complete pilot. Verify
that clothing and animated expressions are populated through ordinary native
construction and drawing. No ROM, save, public recipe, or web option changes in
the artwork-only batch.
