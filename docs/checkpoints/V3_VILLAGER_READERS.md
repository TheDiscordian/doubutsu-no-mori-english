# V3 secondary villager reader checkpoint

## Installed work

The [reader specification](../../specs/V3_VILLAGER_READERS.md) records ten bound
changes, two generated-name entry adapters, their retained allocations and
relocations, and both updated loader checksums. The 912-byte helper fits the
unused gap before the furniture profile table; there is no resident growth.

Current experimental cartridge:
`build/v3-villager-readers-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `bcdea083182abc071c2327401b803756a8f9edd52455c5d8c88d2cf1b11c041f`.
- UPS SHA-256: `4c0e3e1bf48cc8c3cd51de0606a8000a8b810947f8180910e3d91227fe0802bd`.
- Resident prefix SHA-256: `18be0574af4492a65e6f1056152caa5c4cf879301b44ca4801fb1a410ca5a249`.
- Reader helper SHA-256: `2712811dc8fbe14ee5ba9634ac371de35b91d93d682bca5d8c6c6b477cac84f1`.
- Persistent text CRC: `04BEC7BB`; generated-letter CRC: `2E146009`.

The original 394 alias records cover all 216 native villagers and agree with
the complete display-name resource. Neither installed pilot's six-byte name
collides with a native alias. Runtime alias search still gives native aliases
precedence and rejects multiple matching imports.

## Focused verification

All six host/cartridge checks pass in 4.510 seconds. Three early logic tests pass
while the cartridge builds; the three cartridge checks are skipped until its
report exists, then all six pass together. Coverage includes complete fields,
native aliases, both imported names, unknown/test/disabled identities, ambiguous
spelling, overlap/null/source-ready guards, exact restored owner hashes, unchanged
relocations and dependency resources, both loader CRCs, startup ABI/prefix,
patch reconstruction, and exact import-free V2 composition.

The first native attempt, `build/v3-villager-readers-native-01`, verifies the
current startup prefix and allocates the fixture, but its creator load faults
inside the relocator. The fixture incorrectly uses `ovlmgr_LoadImpl`, which
obtains relocation data from the next DMA-directory entry. Generated mail instead
embeds its relocation data in its own file. The trace shows the unrelated
`03400000` font resource being used as relocation data. No name reader runs.

The single setup correction uses explicit native DMA, relocation, and cache
maintenance for that combined resource, matching the real generated-mail loader.
The corrected run, `build/v3-villager-readers-native-02`, passes all 101 recorded
steps. Both generated-name/alias entries and four complete display paths execute
with an original villager, Cheri, and Punchy. Tests confirm full eighteen-byte
capture fields, full eight-byte displays, native six-byte map destinations,
retained saved address records, rejected unknown/test identities, and disabled
name/alias rejection. The live startup-owned conversation adapter executes,
establishing that the changed text checksum passes actual boot loading.

Complete current creator/address/inventory/map loading and relocation pass.
The resident prefix, fixture boundaries, stack guards, and translation guard
remain intact. The allocation is freed, the emulator checkpoint is restored,
and shutdown is clean. No cartridge implementation change is required for the
test-loader correction. Full letter/header drawing and complete generated-letter
delivery are not inferred from these name-consumer calls.

## Remaining work

Move-ins remain disabled. The display/name-capture checks do not by themselves
establish full generated-letter delivery, ordinary conversations/house visits,
or imported villager persistence. Continue the native ID/table and selection
integration, source-complete Punchy dependencies, full furniture lifecycle,
profile composition, Controller Pak transport, and broader donor imports.
Neither public nor local web patcher changes. V3 saves still require a compatible
V3 import profile and must not be loaded by V2.
