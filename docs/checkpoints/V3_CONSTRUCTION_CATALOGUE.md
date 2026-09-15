# Construction catalogue, stock, and scoring integration

## Artifact

- Local cartridge: `build/v3-construction-catalogue-03/animal-forest-v3-asset-loader.z64`.
- ABI 62; 64-MiB cartridge; Expansion Pak required.
- Cartridge SHA-256:
  `5d6e3abdb2b67f33b99264dd2a4a0069c542c34c60b397fcf9df97121237fbc7`.
- UPS SHA-256:
  `4979240c45b4a1725b6e62553ab976c9757e0191494a3b568f88948409b52309`.
- Build report SHA-256:
  `0f33275f8f62d65ef0f3de7e4e8da038d2ca630f58ffad4d83fb53954f6b11d6`.
- Complete blob: 1,393,200 bytes, SHA-256
  `7fad7bb52580c57a322647e8c168c16141efd4559fe83f18dc93dd3b3d652bd0`.

Specification: [catalogue capacity](../../specs/V3_CATALOGUE_CAPACITY.md).
This is integration work, not a playable handoff or a web-patcher update.

## Implementation

The actual native catalogue uses static overlay state. All nine pages grow to
753 item slots. The four address multiplications, three initializer strides,
three name-field offsets, seventeen frame/navigation accesses, translated name
cache, suffix, and complete relocation records are updated together. Existing
preview structures, external buffers, and constructor/destructor ownership stay.
The shared menu reservation grows by 6,144 bytes to 280,704, against a conservative
279,872-byte requirement. Native heap bounds and the eight-MiB requirement stay.

All 436 original furniture entries and ten imports produce 446 rows. The
independent 248-row clothing list stays intact. Seven new source-verified B/C
stock memberships and HRA/feng shui records are installed without changing
ordinary selection/rarity, existing scoring code, or prior metadata.

The first partial build rejected an over-specified clothing metadata record:
the source-bound scoring converter requires the exact canonical mannequin
identity, not its enriched report record. The corrected builder binds that
canonical identity and retains the complete existing table. Output 02 completes;
output 03 corrects inherited installation-status fields in its report and
reproduces the same cartridge and UPS hashes. Neither partial nor older build
is a handoff. Native results below apply to that identical current cartridge;
the metadata-only output is not given another redundant native replay.

## Focused verification

Risk: state/name overlap, wrong category arithmetic, stale relocated cache
pointers, insufficient menu memory, malformed stock pointers, and altered scores
or save state. Scope: four focused current checks and two bounded native checks.
No old candidate replay or navigation loop is needed for this batch.

Four focused tests pass in 0.711 seconds:

- Execute the four actual seven-instruction MIPS arithmetic sequences for all
  eight-bit category inputs, checking the result and unchanged other registers.
  Check all category/name/tail storage boundaries.
- Verify the complete 446-row table, original ordering, 248 garment rows, and
  precisely seven changed scoring records. Construction has 28 mask members.
- Check relocated name-load/draw/init targets at three RAM destinations, clear
  owned state, actual signed allocator endpoint, VROM separation, and alignment.
- Check actual stock membership/descriptors, complete saved-profile retention,
  startup/N64 checksums, and a reverse-scoped whole-cartridge comparison.

One initial assertion mistook the unchanged cache initializer's tail jump for
a JAL. Correcting its expected opcode passes the affected check. The game code
does not change for that test correction. The final four-check run targets the
current metadata-complete output.

## Native catalogue evidence

`build/v3-construction-catalogue-native-01/` passes its initial run: 103 records,
61 explicit memory assertions, and 34 native calls, with no error.
Result SHA-256:
`2dfc218a9961a9205b4823899349feac078f2784e66e909ea9887405794ff51e`.

The actual native loader relocates the complete expanded image. Actual list
initialization handles uncollected/collected imports and all 446 furniture rows.
Full names occupy the moved cache; unused slots do not overwrite name fields.
The navigation tail initializes all nine categories. Native selection loads the
complete detour-sign and saw-horse models and switches preview buffers. All 248
garments retain their order; selecting and scrolling to the last garment on
category three preserves its full English name and identity. Original furniture
fallback, executable/suffix retention, guards, and checkpoint restoration pass.

This does not submit previews to the GPU, execute ordinary controller-driven
catalogue payment/delivery, or establish town-menu heap headroom.

## Native stock evidence

`build/v3-construction-stock-native-01/` passes its initial run: 36 records,
16 explicit memory assertions, and 12 native calls, with no error.
Result SHA-256:
`8c2edbf7c15888b0a4d3470d1b22ebb67a58d9cc2225aad015083fffda0b3a50`.

Actual native rarity queries retain A/B/C priorities. With a deterministic RNG
seed, the native stock selector returns the added speed sign from B and saw horse
from C, advancing once for each selection. Actual pocket insertion retains both
full IDs and records both ownership bits in the expanded catalogue. The entire
private record and 864-byte import state are restored; guards, checkpoint reload,
and graceful shutdown pass. Both emulator runs use no physical audio output.

This is actual function-level selection/acquisition, not ordinary shopkeeper
payment, room placement, or a save/restart cycle. Newly installed scoring rows
have complete source/construction checks, not a fresh native room-evaluation run.

## Remaining work

Connect the local optional composer to this 33-entry installed set. Package RAM
`80481500` is backed by blob offset `7E500`, not `21500`; update only the reviewed
enable words and package CRC before calculating the prefix CRC. Keep empty
selection identical to V2 and selected IDs independent of order.

Continue ordinary acquisition/placement/persistence, village arrival/voice/travel
work, and remaining donor-content conversions. The report also retains existing
clothing scoring coverage: cherry's mannequin is present, but additional aloha
display scoring has no recorded installed row and needs a concrete follow-up.

Saved format 2 and the selected profile match ABI 61. Earlier profiles still
reject dependencies they do not contain. Preserve saves; ordinary cross-build
reload is unverified. No served patcher receives V3 without user testing and
explicit approval. GitHub development-branch source is authorised.
