# Full-sized Western furniture

## Installed content

ABI 66 adds watering trough, covered wagon, and storefront to the seven
[Western furnishings](V3_WESTERN_ITEMS.md). These are additive identities from
the pinned GAFE01-r0 donor, with complete models, two-cell footprints, English
readers, stock, catalogue previews, scoring, and selected save dependencies.
Neither served patcher changes. Ordinary gameplay and hardware appearance
remain unverified; installation is not complete-import certification.

| ID | Index | Name | Bells | Acquisition | Model bytes |
| --- | ---: | --- | ---: | --- | ---: |
| `32C4` | 1201 | watering trough | 1,100 | ordinary B | 3,808 |
| `32D4` | 1205 | covered wagon | 3,800 | lottery | 4,320 |
| `32D8` | 1206 | storefront | 3,680 | ordinary C | 4,400 |

`v3_western_items.py --large` verifies complete source profiles, both quality
tables, unique acquisition membership, prices, catalogue positions, and HRA/feng
properties. The pinned identity worksheet corroborates the absence of native
AF identities/artwork. Fixed registry VROMs are `023C4000`, `023C6000`, and
`023C8000`; each has an independent 8-KiB slot. Checkbox order never assigns IDs.

## Graphics conversion

Converter revision 5 retains all 293 vertices, 128 triangles, 11,136 texels,
and 48 palette entries. The texels comprise 10,624 CI4 and 512 I4 samples.
Total converted size is 12,528 bytes. All objects fit the existing 9,216-byte
dedicated furniture banks and independent catalogue buffers.

The trough has an opaque body and a separate translucent water list. Its I4
water uses no palette, texture scale 4000/4000, wrapping and shift 1 on both
axes, primitive/environment colours, its exact combiner/render mode, and the
reviewed geometry state. Neither flatten the water into the opaque list nor
apply the body palette to it. Its two triangles retain the source 32×16 image.

The wagon's explicit model symbol is `int_wagon_body_model`; it does not follow
the profile/texture stem. Its 24×24 CI4 texture has twelve source bytes per row
but sixteen TMEM bytes per row. Use native `gsDPLoadTextureTile_4b` for widths
not divisible by sixteen, preserving distinct source and TMEM pitches. A block
load would pack these rows incorrectly. Preserve the 8×8 and 48×32 images too;
do not stretch or crop textures to power-of-two sizes. Non-power-of-two clamped
axes have mask zero.

Storefront retains its wrapped-S/clamped-T materials, standalone mirrored-S/
wrapped-T update, and explicit tile extents. Wider sampling extents do not imply
wider source images. Source descriptor, scale, combiner, colour, and extent
checks reject unknown values instead of copying arbitrary donor commands.

## Native placement and catalogue presentation

All three profiles use scale 0.01, height 42.43, shape 3, and collision type 1.
Trough lighting is 2; the other lighting flags are zero. There are no callbacks,
interactions, skeletons, or texture animations to replace with placeholders.

Shape 3 is native/GC type B0: one anchor and a second occupied cell. Size query
returns 1, not the shape number. The complete 12-byte native placement records
follow the actual tables in both games:

| Facing | Second cell relative to anchor |
| --- | --- |
| South | `(+1, 0)` |
| East | `(0, -1)` |
| North | `(-1, 0)` |
| West | `(0, +1)` |

Both unused cells retain the anchor coordinates. Missing, disabled, or unsupported
size-2 records reject placement with return 3 and four cleared records. Arithmetic
retains MIPS wrapping without signed-overflow assumptions. Existing 1×1 items and
original-game fallbacks remain intact. Garments retain non-furniture rejection.

GC catalogue modes are not interchangeable with N64 mode numbers. The trough's
mode 0 matches native scale 0.90/Y −3. The wagon's GC mode 29 lies beyond the
native preset table; storefront GC mode 6 also has different native values.
Both use verified native mode 0 during original construction, followed by a
selected-ID override of final scale/Y: wagon 0.87/−5, storefront 0.82/−5.
All other preview fields, geometry loading, lighting, animation, and price stay
with the original initializer. The builder refuses these records without the
compiled and installed override. The wagon is orderable through lottery list 5,
not ordinary A/B/C or event list 3.

HRA retains Western theme 55 with ten installed members. The new native words
are `DC050200`, `DC050E00`, and `DC050400`; the donor's birth fields are shifted
into the native format. All three feng words are zero. The existing English
Western score-letter name and category evaluator remain unchanged.

## Checked memory and public entry points

The resident package moves in VROM, not in RAM. Its descriptor at prefix `F0`
loads `023CA000..023DAFFF` into `80473000..80483FFF`, checks the full CRC, and
checks the updated size/header/end guard. Old accessory, melody, and roster
code/data retain their original RAM addresses. This adds 8,192 resident bytes.

| Region | RAM | Bytes/capacity |
| --- | --- | ---: |
| Static furniture records | `80482000` | 25 × 80 |
| Shared item records | `80482800` | 26 × 32 |
| New shared item code | `80483000` | 988; limit 4,080 |
| Package end guard | `80483FF0` | 16 |
| Dedicated model pool | `80500000` | unchanged |

Each original shared-item entry in the separate clothing/save resource jumps
to the checked package code. Existing display wrappers still call those same
entry addresses. The save codec, save entry points, and saved format 2 remain
unchanged. New item code calls the actual three-shirt roster lookup, avoiding
the original compiler's single-shirt constant folding. Startup writes back
the complete package and invalidates the new item's full code reservation.

The catalogue has 462 furniture and 248 clothing rows. Its complete image is
62,528 bytes and relocation data is 752 bytes. Its 3,280-byte suffix fits an
explicit 3,664-byte limit; the complete menu requirement is 280,128 of 280,704
already reserved bytes. No extra menu pool or model-bank allocation is needed.
Shared catalogue source checks still enforce the smaller limit for older builds.

The import VROM file uses 2,049,264 of its 2,097,152 reserved bytes. Only 47,888
bytes remain before the existing resource at `02400000`; do not extend across
that boundary. Further families need a reviewed storage allocation, not a larger
unchecked constant. The physical cartridge remains 64 MiB.

## Optional profiles and acceptance

The [offline composer](V3_OPTIONAL_COMPOSITION.md) exposes 49 experimental
options. Clear-all preserves exact V2-11; select-all reproduces the full ABI-66
cartridge. Disabled new items retain inert scoring and reject runtime readers.
The two-cell metadata and compiled framing do not change between subsets.

New profile bits are required saved dependencies. Equal/larger profiles are
accepted by the codec; older/smaller selections reject missing dependencies.
Do not load imported saves in V2. Unchanged save-code instructions do not prove
ordinary cross-profile restart/reload. Preserve existing saves and builds.

The [checkpoint](../docs/checkpoints/V3_WESTERN_LARGE_ITEMS.md) records exact
artifacts and executed checks. Ordinary acquisition, placement, catalogue
appearance, water rendering, and persistence remain player-facing validation.
The earlier unfinished bank-DMA/teardown check is not repeated by this batch.
