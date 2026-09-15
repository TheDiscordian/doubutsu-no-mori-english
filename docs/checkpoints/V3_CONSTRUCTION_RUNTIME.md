# Seven construction items: native runtime integration

## Completed artifact

- Local cartridge: `build/v3-construction-runtime-02/animal-forest-v3-asset-loader.z64`.
- ABI: 61; 64-MiB cartridge; Expansion Pak required; no additional RAM allocation.
- Cartridge SHA-256:
  `d9d2c30034d0e53f54b22679974f9b3bfa3136ca174d918e0f1991e10c526964`.
- UPS SHA-256:
  `40106e2cf30e5e84fcd971ddd63a616c6735b2067fab1fd4305bab765a3dbbf7`.
- Build report SHA-256:
  `4d9fc75e007de3466228206146fb3b0011c4043b0f8755bc64c596bbb2c3f458`.
- Complete blob: 1,290,000 bytes, SHA-256
  `0a85a6c242712ce9833c5d93d78cfe3646dca61e17f9173804a31517d03bc2c4`.
- Selected profile SHA-256:
  `6c4bc91aacfdc1b8865a29421c971e401b3befc1e8529f3321806c3a7558a72e`.

This artifact installs the models and shared item readers, not the complete
ordinary acquisition/catalogue integration. It is not a playtest handoff.
Specification: [construction runtime](../../specs/V3_CONSTRUCTION_RUNTIME.md).

## Implementation

Nine static profile rows and ten furniture metadata rows use verified empty
space inside the already-loaded accessory/audio package. All seven complete
objects have fixed ROM slots and their own profile seeds. The source-bound
original barrel/drum rows move without changing their models or scalar values.
The larger loop is 36 bytes smaller than the previous two-row-unrolled helper.
The actual shared item reader changes only its three table-address/bound words;
the complete save codec and installed clothing adaptations are retained.

The first partial build stops on its source-code hash check because the complete
aloha name/price fixes must also be normalised when comparing the compiled base.
The completed build explicitly validates and reapplies all five fixes, plus the
complete-roster clothing bridge. It does not remove those prior game fixes.
Both partial and complete generated outputs remain ignored and preserved.

## Focused evidence

Risk: wrong profile ownership after moving rows, truncated models, stale item
readers, loss of applied clothing fixes, buffer corruption, and saved-profile
misinterpretation. Scope: four host/cartridge checks and one combined current
native run; no old candidate replay or broad navigation harness.

`python3 -m unittest tests.test_v3_construction_runtime -v`: four checks pass
in 1.582 seconds:

- All seven actual objects, complete native profiles, item metadata, and fixed
  profile seeds agree with the verified source conversion.
- Reverse-scoped comparisons preserve every other ROM byte and blob region;
  actual extra-code differences are exactly offsets `838`, `858`, and `860`.
  Applied clothing fixes, complete save code, descriptors, CRCs, and N64 checksums
  are retained or correctly updated.
- The actual C save codec accepts the preceding profile and the same profile,
  rejects the new profile in the preceding build with `-7`, and preserves input
  and rejection-output buffers. This is not ordinary save/reload evidence.
- The preceding local composer still exposes exactly its 26 installed entries,
  rejecting newly reserved construction IDs that are absent from that cartridge.

Native output: `build/v3-construction-native-01/`. Its initial run completes
145 records, 53 explicit memory assertions, and 83 native calls with no failure.
Result SHA-256:
`e4251319988cd85d01db61589802a0a92745ae1a3953adaea6a1978ffc6389a2`.

The check passes startup, all nine profile rows, all ten metadata rows, all seven
full English names/prices/categories, two complete placement-cell queries,
original barrel/drum/speed-bag item readers, all three garment categories,
disabled-import rejection, restored rows, saved state, and final guards.

The actual native room owner loads the detour sign and saw horse into separate
model banks, retaining every model byte and untouched buffer padding. Profile
selection, bank lookup, four orientations, reuse/release, original native model
allocation/DMA, and full cleanup pass. The test restores the checkpoint and
shuts down cleanly. It does not replay unchanged animated callbacks or mannequin
drawing, submit the models to the GPU, navigate a town, or write a game save.
Audio output remains disabled.

## Next work and release boundary

The seven items require 446 furniture catalogue slots; the current list has a
444-slot bound. Review and expand the actual native category-list storage and
its consumers, then install all seven catalogue rows, prepared stock/scoring
tables, and optional-profile toggles. The rows now live outside the main prefix,
so optional composition must also update the resident-package CRC.

Saved format 2 is unchanged, but these selected-profile saves require the seven
new imports. Older profiles reject them; V2 is not a valid imported-save target.
Keep original saves and disclose ordinary cross-profile reload as unverified.
Both web patchers remain V2 pending user testing and explicit approval.
