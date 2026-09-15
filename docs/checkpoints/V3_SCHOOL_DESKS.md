# V3 school desks

## Current integration image

`build/v3-school-desks-runtime-01/animal-forest-v3-asset-loader.z64`, ABI 84.

- ROM SHA-256: `179c19fb2b3846c77c2ca202dd15b96a268a7f172873b95f69d95da0635440f3`.
- UPS SHA-256: `b60567d54e66fc91bf6f0d48f91e498c22762c6d4a7165acfdbfdd12bff6e0fb`.
- Report SHA-256: `6344b8aa7a4a9c7305a688e4413f9ca9f5d8381e22465f63b10d55eaa353ddd4`.

All three desks have complete model/profile/name/item readers, original prices,
A/B stock, donor catalogue ordering, and native scoring. The full catalogue
has 475 furniture rows; its 280,448-byte conservative requirement fits the
existing 280,704-byte allocation. New artwork uses three fixed 4-KiB slots;
total blob size is 2,862,144 bytes, ending at `024BAC40`, with 1,266,624 bytes
remaining before the next reserved resource. Shared item, furniture, lamp,
save, and environment code remains unchanged. Startup remains 912 bytes.

The local composer now has 62 installed development options: twenty villagers,
thirty-nine furniture items, and three shirts. Select-all reproduces the full
current image; empty selection reproduces V2. These counts do not describe all
donor content or imply completed gameplay. Both patchers remain V2.

`build/v3-optional-school-desks-01/` selects only righty and teacher's desks.
ROM SHA-256 `0f92d40d789957dbce7bf3d360366e4e568b7c1106c2131d4110247f1ae6603a`;
UPS SHA-256 `f9740a04928a8d8639028b084d693c9b84e789040fb32a3b956f72ffaa410d7c`.
Its receipt has correct independent enable fields, catalogue counts, and
selected room-scoring members. The three English names have official source
credits in the single provenance catalogue.

Saved format 2 is unchanged, but the full profile gains three furniture bits.
The decoder accepts equal/superset profiles and rejects missing dependencies;
older full builds cannot accept saves requiring these desks. Do not load
imported saves in V2. Ordinary cross-profile loading remains unverified.

## Complete local outputs

Artwork: `build/v3-school-desks-art-04/`, report SHA-256
`0d83eba785650fba5d1cc8760649f1e8a3e928893e09ae807fbb398fac43d474`.

- Lefty desk: 3,920 bytes, SHA-256
  `2bbb242ee2997768f7cfbc36680e55d0bdeaef72b378cad138c6b2937d44df16`.
- Righty desk: 4,064 bytes, SHA-256
  `f59eb8fc7b0f58f789a867cd0efff46175a5d8e103fb1861ccc5dbe79d8a15ca`.
- Teacher's desk: 2,864 bytes, SHA-256
  `cbbe0a4aae4e5e7663f501e38914f6cd21ded278a90d306be881907ad9d72705`.

Metadata: `build/v3-school-desks-items-01/`, report SHA-256
`0e968bedba6b41a77d8015f793ea035301b982da097aae5015a6f9e24bec2a04`.
The three 32-byte records have SHA-256
`c56f158549b89b7ff5df3e0c27d709d8ccc256504af8b6f9201649f485540167`.

All 218 vertices, 96 triangles, six textures, and three palettes remain. The
complete donor profile/relocation check retains front-only seat flags for both
pupil desks; the teacher's desk retains its two-cell footprint. Native assets
preserve grey tint, lighting transitions, and all mirrored texture extents.
The [specification](../../specs/V3_SCHOOL_DESKS.md) records source identities,
stock, prices, scoring, model bindings, and remaining runtime requirements.

## Bounded verification

Five school-desk checks and five existing synthetic converter checks pass.
The complete-asset checks use the new desk output, not an older cartridge.
They independently compare all texels, palettes, geometry, command state,
triangle indices, native vertex/texture bounds, exact profile flags, and
metadata. Changed seat flags, unreviewed colours, conflicting material modes,
and altered source identities are rejected.

The first test run expects the wrong exception wording for a changed seat
flag: the reviewed-pilot check rejects it before the profile check. Correcting
that expectation and rerunning only the affected test passes. No runtime or
converter assertion is removed. Earlier incomplete conversion directories
retain the failures that identified the nonzero contact field, grey tint,
and teacher's extra mirrored extent; those source features are now preserved.

## Integration verification

Eight current cartridge tests and twelve composer tests pass. They bind every
changed asset/profile/item row, preserve the complete prior package except
those six rows, preserve the full lamp resource and descriptor, verify all
stock lists and native school members, bind native chair/contact functions and
all rotated two-cell tables, check individual selection/report fields, and
verify the exact limited ROM changes. Tests use the new current image; no
historical emulator run is repeated.

The initial builder catches stale inherited package-hash fields in the ABI-83
report. Its actual ROM, installed CRC descriptor, and complete blob are correct.
The new builder explicitly pins that actual package and refreshes all package
receipt fields; no runtime validation is removed.

The first silent native run, `build/v3-school-desks-native-01/results.json`,
passes all 88 records, including 74 assertions. SHA-256:
`c3274cd018f18f89dd60ef0968aa2ea71199b51e3b7bb8cd8960f03f4d8f495d`.
The complete room and catalogue owners load and relocate through the real
native loader. All three full names, prices, classifications, native footprint
results, complete upper-memory model DMAs, untouched bank tails, and bank
indices pass. The teacher's desk passes all four rotated placements. Actual
native stock membership, catalogue eligibility, pocket acquisition, and per-item
saved ownership pass for each desk. No callback is stubbed.

Temporary owner/bank/player/save fixtures are restored, allocation and runtime
guards pass, the matching checkpoint is restored, and ares exits cleanly.
No FlashRAM write is requested during the fixture. Ordinary seating, GPU room
appearance, transactions, and save/restart remain unverified. Continue bulk
donor implementation; do not repeat the exhausted river-navigation batch or
unchanged native prefixes. Patcher publication still requires user testing
and explicit approval.
