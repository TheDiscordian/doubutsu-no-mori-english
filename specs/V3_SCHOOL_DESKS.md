# V3 school desks

## Converted source and boundary

The pinned GAFE01-r0 donor supplies three complete school desks. Converter
version 8 adds them as an explicit batch without changing prior material modes.
`tools/v3_school_desks.py` verifies both actual profile tables, all profile/model
relocations, English names, the pinned identity worksheet, all 23 stock lists,
prices, catalogue rows, and complete HRA/feng-shui resources.

| Donor item | Name | Native asset bytes | Vertices | Triangles | Contact |
| --- | --- | ---: | ---: | ---: | --- |
| `3200` | lefty desk | 3,920 | 89 | 40 | front-only chair |
| `3204` | righty desk | 4,064 | 97 | 40 | front-only chair |
| `3220` | teacher's desk | 2,864 | 32 | 16 | none |

These are converted assets and reviewed donor identities, not installed or
playable imports. Their fixed runtime registry, native seating readers, shared
item/name/model loading, stock/catalogue/scoring/profile integration, and
ordinary acquisition/persistence remain required. Both patchers remain V2.

## Profiles and materials

Profiles `iam_hos_deskL`, `iam_hos_deskR`, and `iam_hos_Tdesk` have one complete
opaque model and no rig, texture animation, or custom callback table. Null
callbacks do not mean every contact field is zero: both pupil desks use donor
`aFTR_CONTACT_ACTION_CHAIR_UNIDIRECTIONAL`, value 1. Preserve that field and
verify its native consumer before claiming usable seating. Their height is 18,
scale 0.01, shape 4, collision 0, and lighting-map flag 0. The teacher's desk
has height 30.5, scale 0.01, shape 3, collision 1, and no contact action.

Both pupil desks retain a complete 64×64 CI4 texture, sixteen-entry palette,
all source vertices/triangles, and grey primitive colour `B2B2B2FF`. All lit/
unlit geometry transitions remain. Their apparent handedness is model geometry,
not a horizontal flip applied to a single shared model.

The teacher's desk retains four CI4 textures (three 32×32, one 16×32), white
primitive colour, mirrored S/clamped T materials, and explicit tile extents
`000FC07C` for 32×32 and `0007C07C` for 16×32. The school material mode permits
only these reviewed extents and white/grey colours; unrelated parser modes
retain their existing restrictions. No geometry, texture tail, or material
is removed to fit. All three assets fit an individual 4,096-byte storage slot
and the existing larger runtime model banks.

## Gameplay metadata for installation

The worksheet identifies no original N64 item/name/artwork counterpart in its
reviewed columns. Source rows are 2541, 2542, and 2549. The actual donor names
and profile-table identities must also match; names alone do not establish
equivalent content.

| Item | Price | Stock | Donor catalogue row | Donor HRA | Native HRA encoding | Footprint |
| --- | ---: | --- | ---: | --- | --- | --- |
| `3200` | 1,240 | A | 237 | `4C058000` | `4C058000` | 1×1 |
| `3204` | 1,240 | B | 238 | `4C058100` | `4C058200` | 1×1 |
| `3220` | 1,580 | B | 243 | `4C050140` | `4C050280` | 2×1 |

All donor preview modes are zero; feng-shui words are `0000`. Series 19 is the
official `school` group, with source descriptor `020006`. Update actual selected
group membership and catalogue counts during integration; an unselected desk
must not become required for completion. The teacher's two-cell surface and
both directional seats require their genuine native placement/contact paths.

English wording comes directly from the donor's `ftrName2_table`. Add its
per-text records to the single `translations/provenance.json` catalogue when
installing these new strings; do not create a parallel text-credit list.

## Verification

The [desk checkpoint](../docs/checkpoints/V3_SCHOOL_DESKS.md) records complete
native asset hashes, source/metadata receipts, and focused checks. Converter
tests compare every texel, palette entry, vertex, triangle, material command,
texture extent, model bound, and profile flag. They do not establish live
seating, transactions, scene rendering, or saved-item persistence.
