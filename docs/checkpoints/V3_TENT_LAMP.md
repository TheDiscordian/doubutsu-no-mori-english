# V3 timed tent lamp

## Deliverable

- Full ROM: `build/v3-tent-lamp-runtime-02/animal-forest-v3-asset-loader.z64`.
  SHA-256 `ff4e5ebafcb15d8ef777d569e0b2f4d29d848223d8e44ef15653c539796279d0`.
- UPS SHA-256 `a0ac540ccac286c1f595661e9f15bb2009ce499cde10e8d3ce637d923e112e6b`.
- Build report SHA-256
  `90a463751b63876534df9bcc0f1e49cdbf500f468dd175056155fcbda7a51413`.
- Offline kayak/propane-stove subset: `build/v3-optional-tent-lamp-01/`.
  ROM SHA-256 `ae6ea5220dbfe9e646ff5b7bae729b203dcfdd209676ece7514e6d7e54d6ba2b`.

ABI 83 installs the complete timed lamp while retaining prior import work.
The composer pins this full cartridge/report and retains all 59 experimental
choices, with exact full/V2 all/empty output. Neither web patcher changes.
No player-facing text is introduced; no new attribution record is needed.

## Implementation

The original effect controller owns the lamp lifecycle without replacing any
effect. Its complete native callbacks execute before the tent-only additions;
the destructor frees the lamp first. The native actor/owner/BSS dimensions and
DMA directory slots remain. Four resident profile pointers replace exactly
their original relocations; every other relocated instruction/data byte is
checked against the complete original owner at two lower-heap addresses.

The donor's 05:00/18:00 schedule drives the two-texture primitive-LOD fade and
point/diffuse/room-light transitions. The full original native environment body
still executes. The complete converted model retains both textures/palettes,
all geometry, and a private frame-owned matrix. Failed allocation/DMA retries
safely; model guards and display-list bounds prevent unchecked drawing.

Resident code uses an existing gap; no permanent reservation or heap limit grows.
The extended 12,288-byte startup load preserves the complete existing save code
and ends before the furniture tables. A live lamp needs 3,280 heap bytes and
releases them on destruction. See [exact bindings](../../specs/V3_CAMPSITE.md).
Entry initializes from the current time without adding a saved light-switch
field; it does not emulate a saved GameCube tent-switch transition.

## Verification

Seven focused lamp tests and twelve current composition tests pass. Actual C
runs with AddressSanitizer and UndefinedBehaviorSanitizer. Cases cover schedule
boundaries, fades, light colours, complete matrix/commands, ownership/cleanup,
allocation/DMA failures, bounded retry, damaged guards, exhausted arenas,
startup CRC/cache/bounds/rejection, and the four-MiB warning path. Cartridge
checks preserve all unrelated resources and original physical owners and verify
checksums/UPS reconstruction. The initial host-only layout assertion is made
MIPS-specific because host pointers are 64-bit; the native ROM is unchanged.

First native run: `build/v3-tent-lamp-native-01/results.json`, SHA-256
`2c62d97e88cfb840637cb872984646fa0b533d2e194ffa1e0ab189ee0f95c199`.
All 65 records complete with 36 passing assertions and no failures:

- Cold boot loads all extra code, original save code, zero state, and guards.
- The real overlay loader relocates the complete owner/BSS and resident hooks.
- Native environment initialization and the full effect constructor allocate
  the guarded full model through actual cartridge DMA.
- The full draw callback emits the correct model binding, LOD, and scale matrix.
- Full native movement at dawn changes target/fade. The complete environment
  update changes strength and point RGB; both native room drawing arenas receive
  the donor primitive-colour formula. Dusk movement restores the night target.
- The full destructor clears lamp ownership and the original effect clip.
  All saved town data, code, allocation/stack guards, and fault checks pass.
  Checkpoint restoration and graceful silent shutdown complete.

The fixture has a private game, object-exchange arena, player, and graphics
arenas. No native callback is stubbed in the emulator. This proves executed
native behaviour on controlled inputs, not ordinary scene entry or GPU output.
Source saves and both web patchers remain untouched; no older ROM is replayed.

## Continue

Combine ordinary tent/NPC construction, entry/exit, conversations, selected
reward handovers, and persistence. Classify the earlier exterior allocation
result through current integration; it remains unresolved, not assumed to be
a harness issue. Continue remaining masked readers and the rest of the V3 queue.

Saved format 2 and selected identities remain unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2. Ordinary cross-profile
reload remains unverified. This is not a complete-import playtest handoff.
Neither patcher changes until the user tests V3 and explicitly approves it.
