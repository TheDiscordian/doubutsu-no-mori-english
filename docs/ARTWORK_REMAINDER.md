# Remaining artwork

## Police and post-office interiors

The [civic-interior batch](checkpoints/CIVIC_INTERIOR_ARTWORK.md) installs exact
English GC wanted/recruitment posters and the MAIL bag in two native rooms.
All visible pixels, alpha, UVs, lighting, and triangles match the donor; native
palettes, geometry, commands, allocations, gameplay, and saves stay unchanged.
Source, reconstruction, installed-counter, and title-retention checks pass.
Ordinary room appearance remains unverified. The Japanese postal symbol on
this bag is unrelated to the intentionally retained lucky-bag decoration.

The inspected native post-office textures `012C0158`, `012BFA58`, `012BFED8`,
`012BFFD8`, and `012C00D8`, using palette `012BDAB8`, are wood/counter surfaces,
not Japanese signs. Retain them. The GC card/card2/mat images at `.data:6138E0`,
`6140E0`, and `613CE0` belong to the GC device/floor design, not interchangeable
native counter labels. Other unreviewed room/furniture images remain in scope.

## Nookington interior signs

The [seven-sign batch](checkpoints/SHOP_INTERIOR_ARTWORK.md) installs the matching
GC second-floor, information, welcome/hours, clearance-sale, raffle-day, and
thank-you images in three native room resources. It preserves room vertices,
UVs, lighting, commands, allocations, shop rules, and saves. Source/pixel,
retention, title-combination, patch, and counter checks pass. Ordinary room
appearance remains unverified. The two tiny original information notices lack
reliable complete transcriptions; their English images are installed, but no
character weight is invented for that wording. Other shop/interior textures
are not declared reviewed by this focused batch.

## Festival stall

The [shared GC-style candidate](checkpoints/STALL_ARTWORK.md) replaces the native
stand's Japanese lettering using one complete GC mesh and a reflected second
placement. Its focused and title-combination checks pass. Ordinary appearance,
lighting, both placements, and event acceptance remain; tiny source-label
transcriptions are still an explicit character-inventory gap.
Its type `1D` slice is `92A98..95478` within object `D5E000`, SHA-256
`608bf509e44565573def8b38d3cc79eff8ccca42a9711da5093ed1f464fd7900`.
The three 128×32 CI4 atlases are `DF1380`, `DF1B80`, and `DF2380`;
the shared native palette is `D5C088`. The two model roots are `06093348` and
`06095440`, selected by the actor's existing two-entry table at `80A7753C`.
The actor is `937120`, RAM `80A76E80`, 1792 bytes, SHA-256
`e5687d71cf30895cfc7166391a1ffb99756de9a7ae3211b07a9633108aaa6395`;
relocation `937820` has SHA-256
`70f07bcfc2b227a4b44be2cd2c10266ff4f6f19df62719f31b50994ef5c6f671`.

The English GC counterpart uses language-neutral striped awnings, balloons,
and pinwheels, with different geometry. It has no interchangeable English
versions of the native tiny sign lettering. Its four textures are
`.data:5B8FC0` (64×32), `5B93C0` (128×32), `5B9BC0` (32×16), and `5B9CC0`
(64×64), with palettes `5B8F60`, `5B8F80`, and `5B8FA0`. Its two 226-vertex
arrays start at `5BA4C0`/`5BB540`, and models at `5BB2E8`/`5BC368`.

There are 430 distinct complete GC vertices across both variants, with no shared
vertices between them. Even deduplicated vertices (6880 bytes), textures (5376),
and palettes (96) exceed the native `2E00` slot before adding any N64 display
lists. A direct whole-model import does not fit. Both GC variants have bounds
X `−6000..6000`, Y `0..9500`, Z `−2000..10000`; the native combined model has
X `−6173..6046`, Y `0..9000`, Z `−2173..10046`.

The shared adaptation fits the original slice with a 1392-byte native model,
without loader or allocation changes. The reflected source surface boundaries
match on all shared planes; the meshes differ in triangulation and one small
non-coplanar detail. Do not claim an exact import of both GC meshes. Do not invent
source words or counter weights from the small raw atlas. Native goods, purchase
behaviour, collision, and both placements remain. The finished stall-choice text
adapter also remains unchanged.

## Lucky bags

Keep the Japanese decorative lucky-bag artwork, as requested by the user, to
match the supplied English GC release. This choice is resolved: the native menu
icons and world-bag writing remain unchanged. Retained decoration is not new
English translation credit.

Exact GC-to-native menu-image matches are `445500 → A58240`,
`445700 → A58460`, and `452300 → A63BC0`, all 32×32 CI4 in native owner `A58000`.
GC palettes are `4454C0`, `4454E0`, and `4520C0`. These images are not newly
translated merely by copying the identical GC resource. Local reference images
are in `build/artwork-inspection/`.

The native world bag uses a different flat image, not the GC three-dimensional
mesh. Native shop-goods table row `858864` binds item range `2E00..2E02` to
material `06001300` and geometry `060013A8`, both variants. Object ID `1E` is
`140C000`. Its material loads palette `140D3C0` and 32×32 CI4 texture `140D3E0`;
its geometry loads four vertices at `140D2C0` and draws two triangles. The texture
SHA-256 is `412bc588478c5c742dc87eca1c47d014bd687523f200f90e1fd67fc63b9a3f7c`;
palette SHA-256 is `d5af0032c0bfa9e6f5cff66560b93f49d7b9f4e6572c435428333592e5330fcb`.
The entire 16144-byte object has SHA-256
`e0e87769178c5593175d0d69a395190693dc1cd6481ae9fc1a327de82dd84f06`.
The table row, both lists, vertices, texture, and palette remain unchanged in
the current shared-stall candidate.

The matching English GC shop-goods row binds its bag/present types to
`obj_fukuT_mat_model` at `.data:38F5A0` and `obj_fukuT_gfx_model` at `38F5E8`.
The source uses texture `38F140`, palette `38F120`, and 38 vertices at `38F340`.
Both the native flat image and the decoded English GC world texture retain
the decorative Japanese `大` character. Copying that texture cannot translate
the writing, and it is not a direct substitute for the native flat picture.
Native `8908E0` is a Bell bag, not this lucky-bag asset. Preserve the native world
picture, all three menu icons, the existing world model, and item behaviour.

## Inspected neutral seasonal props

These specific native texture sets contain no readable Japanese lettering in
the direct decoded inspection. Preserve the native designs; this inspection
adds no translation credit and is not ordinary scene or event acceptance.
Addresses are native VROM; the palette column identifies the inspection palette.
This is a scoped texture inventory, not an assertion that every image in the
entire game has been reviewed.

| Prop | Textures | Palette |
| --- | --- | --- |
| Igloo | `D79A58`, `D79258`, `D7A258` | `D5BFE8` |
| Picnic mat/food | `D73A38`, `D73238`, `D74238` | `D5C048` |
| Radio | `DB2690`, `DB2E90` | `D5C068` |
| Moon viewing, first placement | `DE6D78`, `DE7578`, `DE7D78` | `D5C0A8` |
| Moon viewing, second placement | `DE4700`, `DE5700`, `DE4F00` | `D5C0A8` |
| Red sports basket | `D74EC0`, `D756C0`, `D76230` | `D5C128` |
| White sports basket | `D76EB8`, `D776B8`, `D781F0` | `D5C148` |
| Carp streamer | `D7C960`, `D7C160` | `D5C1A8` |
| Windmill | `DEE0D8`, `DED8D8`, `DED0D8` | `D5C288` |
| Lotus | `D7E6D8`, `D7E8D8` | `D5C328` |
| Crate | `D7F258` | `D5C348` |
| Statue | `D69DE8` | `D5C368` |
| Lighthouse | `DDCD48`, `DDC528`, `DDC728`, `DDCB28`, `DDCBA8`, `DDCC28`, `DDCCA8`, `DDC4A8` | `D5C3A8` |

The shrine's six inspected seasonal atlases and the eighteen station atlases
also remain native, as recorded in their existing artwork work. Preserve the
shrine identity rather than substituting the GameCube wishing well.

## Other inspected structures and warning

The [bounded structure inspection](checkpoints/NEUTRAL_STRUCTURE_ARTWORK.md)
covers seventeen distinct train, vacant-lot-sign, Katrina-tent, and Gracie-car
textures in twenty-three seasonal views. No readable Japanese wording is found.
The small reserve-sign papers contain abstract marks without reliable wording;
do not invent a transcription. All selected model sections, palette selections,
and streamed copies remain native in the current candidate. The separate
region-warning image is already English. These findings add no translation
credit and do not declare furniture, clothing, other images, or ordinary scene
acceptance complete. Preserve the inspected native artwork.

## Resolved regional donors and shop drapes

The [regional review](checkpoints/REGIONAL_ARTWORK_REVIEW.md) binds the
US-labelled `obj_s_house_i_3_us_tex_txt` panel to the GameCube-only island NPC
cottage, not an N64 player-house sign. No cottage is added to the native game.
The native gloom effect is traced through effect ID `0B`, its actual code,
model table, streaming loader, and 64×32 IA8 image at `0141D020`. It contains
vertical lines without Japanese wording. The complete native effect remains
unchanged; the GC scrolling-mask redesign is not a required translation.

The unmatched shop-room images `013B4B88`, `013CA410`, and `013DAB30` contain
red-and-white drapes and rosettes, not Japanese signs. Preserve all three native
textures and palettes. These scoped reviews add no English text credit and do
not establish ordinary scene acceptance or a full native-house artwork review.

## Source-matching inventory

`tools/artwork_matches.py` creates a new read-only candidate report in `build/`.
The [specification](../specs/ARTWORK_MATCH_INVENTORY.md) defines its supported
formats, actual GC source bindings, and explicit exclusions. The recorded run
finds 1170 native material candidates, of which 942 match named GC texels and
228 do not. This is not a translation percentage: matching does not establish
English wording or colour equivalence, and unmatched does not imply Japanese.
Some unmatched originals already have installed English replacements.

Use the report's addresses and neighbouring source names for further review.
Prioritise unreviewed room owner `012B2000` and remaining screen/item images,
checking the current candidate first so completed replacements are not repeated.
Dynamic/cross-segment textures and unsupported formats still need separate
binding; the report records those exclusions instead of declaring them complete.
