# V3 static furniture conversion

## Implemented boundary

`tools/v3_furniture_art.py` converts the supplied GAFE01 revision 0 haz-mat barrel
and oil drum into complete, self-contained native texture/model objects. Both
are furniture dependencies of Cheri's donor house. Output remains in ignored
local build directories; no game images, extracted assets, or executable donor
code are committed or published.

These are converted assets, **not playable or selectable imports**. Runtime item
identity, profile loading, acquisition, placement, collision, prices, catalogue
flags, rewards, scoring, and saved-item handling still need integration. Native
profile construction preserves the donor scalar fields, but those fields do not
by themselves verify ordinary collision or interaction behaviour.

The source build does not alter a cartridge, existing furniture, the V2 baseline,
or either web patcher. The user's V3 testing and explicit approval remain required
before switching the patcher.

## Source identity and dependency binding

The converter checks the complete decoded REL and pinned symbol-file SHA-256
from [the import catalogue](V3_OPTIONAL_IMPORTS.md). The command-line path reads
the actual supplied disc through the existing revision/resource checks. It does
not use unchecked asset caches or a different revision's exported C arrays.

| Donor item | English name | Donor profile | House dependency |
| --- | --- | --- | --- |
| `3224`–`3227` | haz-mat barrel | `iam_iku_hazardous_top` | Cheri main layer `0202` |
| `32B8`–`32BB` | oil drum | `iam_iku_orange` | Cheri main layer `0202` |

These are **donor** item IDs, not assigned N64 destination IDs. Both donor
`furniture_quality` tables at `.data:00039FB4` and `.data:0007B5B0` must resolve
the actual item index to its reviewed profile through the REL relocation stream.
The second furniture-name table must contain the corresponding English name.
The two reviewed profiles have an opaque and a translucent model, height 18,
scale 0.01, shape 4, collision kind 0, no extra rotation/contact/interaction
behaviour, and no callback, rig, or texture-animation pointers. The haz-mat
barrel's lighting-map flag is 1; the oil drum's is 0. Preserve that difference.

Every palette, texture, vertex array, model span, profile pointer, and display-list
pointer is resolved against its unique symbol and actual REL relocation. Reject
missing, external, duplicate, extra, or out-of-range dependencies. Texels and
vertices must have no relocations. A changed profile does not become a generic
decorative item by dropping its callbacks.

Punchy's main layer `01EA` contains a speed bag (`3352`, a rotation of `3350`).
`iam_ike_prores_punch01` uses a custom animation/interaction table. It is outside
this static converter and remains an explicit behaviour-port dependency.

## Native asset layout

Both current objects use segment 6 and contain 3,216 bytes, aligned to 16 bytes.
Resource allocations are aligned to 32 bytes; display lists are aligned to 8.

| Offset | Bytes | Content |
| --- | --- | --- |
| `0000` | 32 | Sixteen-entry RGBA16 palette |
| `0020` | 512 | 32×32 CI4 decal |
| `0220` | 512 | 32×32 CI4 top texture |
| `0420` | 1,024 | 64×32 CI4 side texture |
| `0820` | 576 | All 36 native vertices |
| `0A60` | 336 | Opaque display list, 18 triangles |
| `0BB0` | 224 | Translucent display list, 8 triangles |

Convert GX CI4 8×8 blocks into native row-major texels. These textures use
ordinary native texture-block loading, not the pre-swapped TMEM atlas format
used for villager faces. Convert RGB5A3 colours to RGBA16 and reject partial
alpha requiring a different rendering path. Preserve positions, UV coordinates,
normals, and vertex alpha; clear only recognised GameCube vertex matrix flags.

Decode packed five-bit donor triangle commands using the existing checked mesh
decoder. Preserve every triangle's vertex order and material boundaries. Vertex
loads must stay within the complete array and the 32-entry native vertex cache.
Reject unknown graphics commands rather than passing them to the N64.

Compile native graphics macros in the existing pinned Docker MIPS toolchain:

- Convert the donor's zero texture scale to native `FFFF,FFFF`.
- Replace Dolphin palette commands with a native sixteen-colour TLUT load.
- Replace Dolphin texture/tile pairs with native CI4 texture-block loads,
  palette 15, clamp in both directions, and the verified width/height masks.
- Emit pipeline synchronisation and RGBA16 TLUT mode explicitly.
- Replace packed donor triangles with native one/two-triangle commands.
- Retain only explicitly recognised compatible colour, geometry, render-mode,
  primitive-colour, and end commands. Keep opaque and translucent layers separate.

`native_profile` constructs the native 68-byte furniture profile for a supplied,
checked VROM allocation: resource start/end, segment start/end, both model
pointers, original scalar fields, and null unsupported callbacks. Bounds and
alignment are mandatory. The future installer must additionally verify that
the VROM allocation is unclaimed and present in the composed DMA table.

## Verification and remaining integration

Seven focused tests cover source rejection, graphics parsing, dependency/vertex
bounds, native compiler input, profile layout, complete real donor conversion,
and actual compiled display lists. Independent GX block addressing compares all
4,096 texels per object; palette checks and complete vertex comparisons retain
their colours and geometry. The compiled N64 lists are decoded independently
to compare every face, material load, texture extent, rendering state, and end.

The [batch checkpoint](../docs/checkpoints/V3_FURNITURE_ART.md) records hashes and
the exact local outputs. No native renderer, ordinary acquisition/placement,
house visit, save cycle, or original-hardware test is claimed for these objects.
The existing cartridge is unchanged, so unchanged V2/V3 code is not re-tested.

The native `ovl_My_Room` loader owns separate furniture profile/code allocations,
resolved profile pointers, per-item bank indices, and per-bank addresses. It
does not load furniture through the new villager texture-bank slots. Expand
its table readers and initialization/cleanup paths together, retaining native
ownership and safe rejection of absent imports. Shared item readers also need
the selected stable registry before these assets can enter gameplay.
