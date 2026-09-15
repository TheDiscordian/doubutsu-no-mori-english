# V3 school-desk conversion

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

## Next installation

Keep ABI 83 and the current composer pinned until the complete new integration
build is verified. Add fixed registry entries for donor `3200`, `3204`, and
`3220`, checked model storage/profile rows, and all existing shared consumers.
Connect actual A/B stock, packed selected catalogue rows, school-series counts,
native scoring, and format-2 profile bits. Record source attribution for the
three added item names in the single provenance catalogue.

Verify the native directional-chair reader and teacher's two-cell placement;
null custom callbacks are not evidence that contact behaviour needs no review.
Then perform one combined changed-path check and retain ordinary acquisition/
interaction/persistence for the broader gameplay pass. Do not replay the
exhausted river-navigation batch merely to test unrelated desk assets.

No ROM, saved format, profile, or served patcher changes in this conversion
batch. The three desks are not yet selectable or installed. GitHub development
source may be pushed; patcher changes still require user testing and approval.
