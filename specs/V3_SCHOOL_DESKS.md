# V3 school desks

## Installed scope and source

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

ABI 84 installs all three with fixed identities, complete model/name readers,
stock, catalogue, scoring, and format-2 profile bits. The local composer enables
each independently or together with other imports. All three retain their donor
IDs and do not replace native furniture. Both patchers remain V2.

The current native check passes full item readers, model DMA, all four teacher's
desk rotations, actual stock membership, catalogue eligibility, pocket
acquisition, and saved ownership. Ordinary room appearance, sitting, and
save/restart remain unverified; these are experimental imports.

## Profiles and materials

Profiles `iam_hos_deskL`, `iam_hos_deskR`, and `iam_hos_Tdesk` have one complete
opaque model and no rig, texture animation, or custom callback table. Null
callbacks do not mean every contact field is zero: both pupil desks use donor
`aFTR_CONTACT_ACTION_CHAIR_UNIDIRECTIONAL`, value 1. Preserve that field and
retain the native seating flow. Their height is 18,
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

## Installed gameplay metadata

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
official `school` group, with the unchanged native/donor descriptor `020006`.
The full profile adds three metadata members to its existing fourteen; the
composer removes unselected desks from grouping and packs selected catalogue
rows. Selecting only the righty desk yields fifteen school metadata members,
and 437 catalogue entries. The teacher's footprint uses genuine native direction
tables, with its second cell south +x, east −z, north −x, or west +z.

English wording comes directly from the donor's `ftrName2_table`. The single
`translations/provenance.json` catalogue records source indices 128, 129, and
136, exact English-name hashes, and Nintendo's localization-team credit.

## Native seating and storage contract

The complete native seating function `8093FF64..80940304` reads the expanded
profile table at `80470010`, then contact byte `3C` at `809401E4`. It scans the
first three bits. Bit zero resolves through table `8094D01C` to the one-entry
direction list `8094CFF8`, value 2/front. The donor's corresponding front-only
list also contains 2. The complete contact query `80940378..80940498` reads the
same byte and the interaction halfword at `3E`. Current-owner hashes and actual
native relocation bind both functions and the complete direction tables.
No contact instruction is replaced by this import. This establishes the native
contract, not an ordinary sitting test.

Assets occupy VROM `024A8000`, `024A9000`, and `024AA000`, each in a checked
4,096-byte slot. Canonical 80-byte profile and 32-byte item rows already have
space at `80484000` and `80498000`. The complete source lamp/save code at
`024A1080` remains unchanged, including its 12-KiB resident reservation.
Startup remains 912 bytes; neither permanent memory nor the model-bank pool
grows. Source ROMs, saves, and both patchers stay untouched.

## Verification

The [desk checkpoint](../docs/checkpoints/V3_SCHOOL_DESKS.md) records complete
native asset hashes, source/metadata receipts, and focused checks. Converter
tests compare every texel, palette entry, vertex, triangle, material command,
texture extent, model bound, and profile flag. Eight cartridge checks and twelve
composer checks pass; the first native run passes 88 records with 74 assertions.
These checks do not establish ordinary seating, scene rendering, shop
transactions, or save/restart persistence.
