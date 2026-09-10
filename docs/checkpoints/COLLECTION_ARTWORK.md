# English collection heading checkpoint

## Combined candidate

`build/collection-artwork-01/animal-forest-halfwidth.z64` contains the full
GameCube Insects/Fish heading images, English clock, map and ordinary inventory
artwork, twelve shop textures, the Shrine correction, both native first-job
conversation corrections, and all earlier English resources.
ROM SHA-256:
`27f840aaea2693ac96fbbc084981dd978f8e376cbf8d7a1259666160d29f5f7d`.
UPS SHA-256:
`908545eb8699b3e5c122d2e974cdf4414aacdb926820e02d67fd033b5d6ffa41`.
Cartridge size remains 32 MiB and RAM use remains four MiB. The corrected v0
handoff and separate Expansion Pak title preview are untouched.

## Verification

Three focused tests pass in 8.169 seconds. These cover independent native GBI
compilation (including the non-power-of-two 80-pixel heading), actual GC REL
texture references, complete lossless pixels and transparent padding, source
UVs and dimensions with the native frame anchor, retained vertex order/flags/
colours and unchanged icons, original display-list continuation, rejection of
wrong sources/assets/commands, all prior cartridge resources, and UPS recovery.
The reviewed ROM/report pair is registered for the existing combined progress
tool. These are not new text-bank rows or duplicated collection-name credit.

The [specification](../../specs/COLLECTION_ARTWORK.md) gives exact bindings and
native-frame placement. Ordinary page display/navigation and original-hardware
acceptance remain unverified. No new native harness, game-state change, or save
mutation is performed for this data-only batch.

## Remaining artwork findings

Some supplied English GameCube artwork itself retains Japanese writing. Its
grab-bag icons at `.data:00445500` (palette `004454C0`) and `00452300`
(palette `004520C0`) still show the Japanese lucky-bag design. Copying those
icons cannot translate their writing. Keep this as an explicit asset-design
task, not a presumed completed English port. The unrelated ground item bag at
`008908E0` is a Bell bag, not a drop-in replacement for the grab-bag icon.

Continue remaining buildings/signs, the title integration, and the GameCube-style
keyboard. Ordinary screen appearance/navigation should be checked together,
without repeating the already verified conversation scenarios or complete suite.
