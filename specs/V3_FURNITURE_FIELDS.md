# V3 shared furniture grids and shop eligibility

## Implemented boundary

`tools/v3_furniture_fields.py` connects selected imports to two complete native
room-grid functions and the native shop-eligibility entry. It uses the existing
full-width room query wrapper. Neither native grid traversal nor placement-data
generation is replaced. The [checkpoint](../docs/checkpoints/V3_FURNITURE_FIELDS.md)
owns exact build/test evidence.

| Native function | Change |
| --- | --- |
| `800BE844`, `mRmTp_AssignFtrFgIdx` | Accept selected imports at the range window `800BE910`; retain sequential actor indices across both layers |
| `800BEA50`, `mRmTp_MakeFtrNoTable` | Accept selected imports at `800BEACC`; retain complete item/rotation values in the occupied-cell map |
| `800BEE50`, `mRmTp_CheckShopFtr` | Return the verified shop eligibility for selected pilots; retain the original function for other item types |

The range windows preserve the original lower comparison, upper comparison,
branch conditions, and delay instructions. Direct returns target the fixed
main-code continuations. The complete source functions and displaced words are
hash-bound. The shared room query admits only an enabled, correctly bound
furniture profile; unsupported or disabled `3xxx` values do not enter the grid.

This integration does not implement inventory action dispatch, catalogue flags,
shop generation/order lists, outside field objects, or save/profile handling.
Shop eligibility is a predicate, not an acquisition route. A complete ordinary
placed-actor and save/reload check remains required. Neither web patcher changes.

## Donor rules

The actual pinned GAFE01 revision 0 `mRmTp_birth_type` and `mRmTp_ftr_se_type`
tables each contain 1,266 bytes. The converter verifies the complete donor REL
and symbols, then confirms the pilot values:

| Item | Runtime index | Birth/shop group | Action-sound type |
| --- | --- | --- | --- |
| haz-mat barrel | 1,161 | 2, group C | 0, none |
| oil drum | 1,198 | 0, group A | 0, none |

Both games' shop predicate accepts groups A, B, C, and event. The new entry
returns true only for the selected pilots. The native action-sound function at
`800BED5C` already returns `-1` for these extended indices, which matches their
verified no-sound requirement; it stays unchanged. Future interactive imports
must implement their actual sound and behaviour requirements.

## Layout and preservation

V3 ABI 8 retains the 48-KiB reservation, both resident guards, all existing
tables, and the ROM-only model tail. A sixteen-byte original-shop bridge uses
`8046A200`; the 252-byte helper and two detours start at `8046A400`. They fit
below `8046BFF0`. The build verifies that the reused full-width query remains at
`804680B8`, with no overlap between room code, the shop bridge, and field code.

The original shop prologue is copied to the bridge and resumes at `800BEE58`.
Original item types retain the native birth table and predicate logic. Imported
IDs and rotations are not replaced with native aliases. No saved field changes
or new DMA-directory entries are introduced by this component.

## Verification and limits

Four focused checks cover sanitized shop selection, donor tables, exact three
function patches with unchanged remaining instructions, the shop bridge,
resident bounds/CRC, deterministic composition, UPS reconstruction, and exact
import-free V2 retention.

The native fixture calls both complete grid functions on two mixed layers of
original furniture, both imports, and an unsupported `3xxx` value. It checks
complete output maps, sequential cross-layer indices, retained rotations,
disabled-profile omission, and unchanged source grids. It also exercises native
and imported shop predicates, the no-action-sound fallback, guards, and checkpoint
restoration. The native index-grid initializer only assigns its first output
entry before traversal; the fixture preserves and explicitly checks that existing
behaviour instead of silently changing unrelated room initialization.

The test uses isolated RAM and blank cartridge storage, not an existing town.
It establishes these complete native functions, not rendered placement,
inventory/menu behaviour, saving/loading imported items, or original hardware.
