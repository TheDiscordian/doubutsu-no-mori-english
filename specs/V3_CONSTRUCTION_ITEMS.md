# V3 construction furniture batch

## Scope

Seven additional GAFE01 revision 0 furnishings have complete native graphics
conversion and source-verified item, shop, and scoring metadata. They are not
installed in a cartridge or enabled by the optional composer yet. Neither the
local nor public web patcher changes. The user's testing and explicit approval
remain required before either patcher receives V3.

`tools/v3_furniture_art.py --batch construction` converts the models and textures.
The default `pilots` batch remains the two original static house dependencies.
`tools/v3_construction_items.py` prepares seven 32-byte native item records and
their provenance. The shared shop, HRA, and feng shui builders accept these
explicitly reviewed identities when given them as selected imports; their
default callers do not select the new items.

## Identity and properties

All rows come from the supplied disc, pinned decoded REL, and pinned symbols.
The converter verifies both actual `furniture_quality` relocation tables, the
English name table, complete profile values, and every asset relocation.
The cached identity sheet corroborates that these entries have no AF item/name/
indoor-image mapping. It is supporting identity evidence, not executable source
or a substitute for verifying the donor models.

The item/rotation mapping uses the original donor base ID and the existing
type-3 formula `1024 + (base - 3000) / 4`. These are reviewed integration
candidates, not registrations in the active runtime registry. Keep the seven
identities fixed when installing them; selection order must not assign IDs.

| Base ID | Index | English name | Price | Ordinary stock | Native HRA | Feng shui |
| --- | --- | --- | --- | --- | --- | --- |
| `31F4` | 1149 | wet roadway sign | 850 | B | `40050200` | orange |
| `31F8` | 1150 | detour sign | 830 | B | `40050200` | orange |
| `31FC` | 1151 | men at work sign | 850 | C | `40050400` | orange |
| `320C` | 1155 | flagman sign | 850 | B | `40050200` | orange |
| `3214` | 1157 | jersey barrier | 1050 | B | `40050200` | none |
| `3218` | 1158 | speed sign | 870 | B | `40050200` | none |
| `322C` | 1163 | saw horse | 900 | C | `40050400` | none |

Every profile has height 18, scale 0.01, shape 4, collision kind 0, and one
opaque model. Unsupported callback, animation, and secondary model pointers are
all null. The detour sign's lighting-map flag is 1; all other rows have 0.
Preserve the donor's complete geometry and lighting flags, not just its texture.
The donor and native 1×1 placement arrays agree; each item occupies one cell.

## Complete model conversion

| Item | Vertices | Triangles | Native object bytes |
| --- | --- | --- | --- |
| wet roadway sign | 94 | 40 | 2,944 |
| detour sign | 94 | 40 | 2,944 |
| men at work sign | 94 | 40 | 2,944 |
| flagman sign | 94 | 40 | 2,944 |
| jersey barrier | 44 | 26 | 1,888 |
| speed sign | 77 | 40 | 2,672 |
| saw horse | 103 | 51 | 3,856 |

The batch contains 14,848 CI4 texels, 112 palette entries, 600 vertices, and 277
triangles. Objects total 20,192 bytes. Each fits the existing 5,120-byte furniture
bank; the largest has 1,264 bytes spare. This establishes model-buffer capacity,
not the RAM allocation for future resident metadata or scene/hardware acceptance.

All materials use the established CI4/TLUT conversion. Most clamp both axes.
The jersey barrier's `yoko` and saw horse's `c` material use a mirrored S axis
with clamped T, each on a 16×32 texture. Their following explicit tile command
extends the displayed tile to 32×32. Preserve that command after the texture
load: a 16-wide texture with a 32-wide mirrored tile is intentional.

The additional parser mode accepts only `D2F0F800` for this mirror operation,
and only `F2000000 0007C07C` following an actual mirrored 16×32 material. It
does not enable the accessory parser's other states or relax the default static
parser. Native texture descriptors use S mirror, T clamp, masks 4/5, and zero
coordinate shifts. Independent compiled-command checks verify those fields.

Profile generation requires the chosen model's exact layer set. These seven
profiles have only an opaque pointer; the original two pilots still require
their separate opaque and translucent pointers. All profile bounds, alignment,
scalar fields, and null callback checks remain mandatory.

## Gameplay data conversion

The metadata reader checks actual price/name/profile bytes and searches all 23
donor furniture goods lists. Each reviewed item occurs exactly once, in the
ordinary B or C list above, with no event-only membership. Shared shop generation
appends canonical item order while retaining all original lists, terminators,
pointer alignment, event contents, rarity code, and random selection.

HRA's private `mMkRm_ftr_info` is `.data:0004FAFC`, not the earlier feng shui
table at `.data:0004EBF0`. The builder converts donor birth bits `[13:8]` to
native `[13:9]`, preserves construction theme 16 and the other reviewed flags,
and retains native point rules. Donor `40050100` becomes native `40050200`;
donor `40050200` becomes native `40050400`. Feng shui's orange/none rows retain
their zero facing penalty and the native game's weights.

The original game has 19 construction-theme records. The barrel and drum bring
that to 21; this batch brings it to 28. The native completion mask supports 32.
Further construction imports must retain this capacity guard rather than assume
the remaining rows fit. The speed bag belongs to another theme.

## Required runtime integration

- Add fixed registry records and safe ROM allocations for all seven objects.
- Install profiles and names/prices/footprints in a larger static-item table;
  connect the existing loader and item readers without disturbing current rows.
- Include selected items in shop stock, catalogue/ownership, rewards, scoring,
  saved profiles, and deterministic optional composition.
- Preserve the native acquisition, placement, rotation, and persistence paths;
  perform a bounded combined check of the changed readers and representative
  actual model loading/gameplay.

The [checkpoint](../docs/checkpoints/V3_CONSTRUCTION_ITEMS.md) contains the exact
converted artifacts and focused results. No emulator, gameplay, save-format,
cartridge, or original-hardware change is claimed by the conversion batch.
