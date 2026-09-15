# V3 aloha garments and islander outfits

## Source and identities

The pinned GAFE01-r0 disc supplies `241A`, red aloha shirt, and `241B`, blue
aloha shirt. Both have a donor price of zero. They are exclusive garments;
this stage does not insert them into ordinary shop stock or invent a price.
Neither complete converted image matches any of the 256 original N64 garments.
All 1,024 pixels and the complete converted palette are retained for each shirt.

| Donor item | Pocket ID | Resource index | Resource VROM |
| --- | --- | --- | --- |
| `24BF`, cherry shirt | `34BF` | `10BF` | `0220F000` |
| `241A`, red aloha shirt | `341A` | `101A` | `022E2000` |
| `241B`, blue aloha shirt | `341B` | `101B` | `022E2400` |

The fixed registry never assigns identities by selection order. Each resource
contains 512 bytes of CI4 texture followed by 32 bytes of RGBA16 palette.
Three 32-byte metadata rows occupy `80462820..8046287F`; adjacent NPC rows and
the other reserved data remain intact. Original clothing keeps its own IDs,
textures, palettes, and resource mapping.

The existing eighteen islander records receive the appropriate `341A` or `341B`
at their applied-outfit field. Names, phrases, personalities, donor clothing
references, umbrellas, and donor growth permission 2 remain unchanged. Cheri
and Punchy's complete initial defaults remain intact. The complete experimental
cartridge uses the [explicit town policy](V3_TOWN_RESIDENTS.md) for eligibility;
outfits alone do not supply houses or town-compatible behaviour.

## Shared runtime and compiled callers

`overlays/v3/clothing_roster.c` validates the exact item/index/VROM tuple,
enabled/reserved fields, and the individual selected-profile bit. Unknown,
disabled, or malformed records cannot supply a resource. Invalid NPC clothing
uses the retained native `2400` fallback. Missing outfits produce no partial
villager initialisation.

The helper and four assembly bridges occupy 1,076 bytes at `80473A00` within
the existing shared package. This grows neither its allocation nor the ordinary
heap. Each bridge uses 144 stack bytes; nested C helpers use at most 24 more.
The bridges preserve the complete 64-bit values of `v1`, `a0..a3`, `t0..t9`,
and `ra`. The C helpers do not modify HI/LO or floating-point state.

This preservation is required by the existing compiler's whole-unit knowledge:
the old shared loader retains its destination in `t1` across clothing lookups.
An ordinary C calling-convention replacement alone can overwrite that live
destination and cause the native DMA error handler to stop the game. The checked
bridges preserve the existing callers without changing their public addresses.

The existing item-name and price functions also contain a folded constant for
the former single clothing record. Five guarded instruction edits make those
readers use the selected record returned by the new predicate. Category handling,
native fallbacks, all save-code instructions, and the rest of the separate
save/item resource remain unchanged.

## Construction and compatibility

`tools/v3_aloha_runtime.py` builds ABI 55 on the pinned complete-text cartridge.
It extends only the last physical allocation into verified empty padding,
retains all existing file positions, updates the package/save-item/prefix
checksums, and verifies complete UPS reconstruction. The cartridge remains
32 MiB and requires the Expansion Pak. Original audio positions and all new
audio resources are retained without another playback claim.

The selected profile adds clothing bits `1A` and `1B`, independently of `BF`.
Saved format 2 and ownership encoding are unchanged. The codec accepts the
preceding subset profile; older builds missing these new dependencies reject
new saves. V2 must not load imported saves. Ordinary cross-build reload is not
newly verified; preserve existing saves and use disposable copies for testing.

The [checkpoint](../docs/checkpoints/V3_ALOHA_OUTFITS.md) records the corrected
cartridge, confirmed boot defect and fix, host checks, and combined native run.
The [islander arrival houses](V3_ISLANDER_HOUSES.md) supply the eighteen source
rooms. The [complete display adapter](V3_ALOHA_DISPLAY.md) supplies mannequin
identities, catalogue listing, and all shared display consumers. Ordinary
acquisition/persistence, house visits, and ordinary move-ins remain work.
Both served patchers remain V2 pending user testing and explicit approval.
