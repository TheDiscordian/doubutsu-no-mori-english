# Remaining artwork

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

The supplied English GC release retains Japanese decorative lucky-bag artwork.
The user-facing choice between retaining that design and replacing its writing
is pending. Continue other work without waiting for that choice.

Exact GC-to-native menu-image matches are `445500 → A58240`,
`445700 → A58460`, and `452300 → A63BC0`, all 32×32 CI4 in native owner `A58000`.
GC palettes are `4454C0`, `4454E0`, and `4520C0`. These images are not newly
translated merely by copying the identical GC resource. GC world-bag texture
`38F140`, palette `38F120`, needs separate binding; native `8908E0` is a Bell
bag, not the lucky bag. Local reference images are in `build/artwork-inspection/`.

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
