# Complete fire runtime

## Result

ABI 70 installs both complete camping fires. Campfire `335C` retains its full
8,000-byte model and one-cell footprint. Bonfire `3360` retains its complete
6,032-byte model and four-cell footprint. Both include the full three-joint rig,
half-speed repeating animation, camera-facing flame, both scrolling I4 textures,
and per-actor positional refresh of their actual installed two-layer loop sounds.

English names/prices, native profiles, catalogue entries, HRA/feng data, and
selected save dependencies are installed. Bonfire's catalogue framing is
`0.86/−3`; the donor's mode 19 is not copied as a native mode. Neither fire is
orderable or placed into ordinary shop stock. Both remain summer-camper rewards;
their actual acquisition adapter is unfinished.

The offline composer provides 59 experimental options: 20 villagers, 36 furniture
items, and three shirts. Both fires can be selected individually or together
without unrelated dependencies. Select-all reproduces the complete current
cartridge, and an empty selection reproduces stable V2 exactly. Both served
patchers remain V2 pending user testing and explicit approval.

## Artifacts

Complete output: `build/v3-fire-runtime-02/`.

- ROM SHA-256: `e2a8ddfb41b7ad7d111cf666dc4b4706046d6edff1fe88968e925603a9345ad5`.
- UPS SHA-256: `6f2e4fb3fb8df2143c46a8d21223477716f21fc6bb4b4f9d39b3a94c3d1eedbf`.
- Build-report SHA-256: `ecf0b223d51609e004a369ad2b4a2d817c9e192edff4fe2213ac9092c2e3aa7c`.
- Package SHA-256: `e4a88170e171d8bed30a9b3e10844e3b36bf53f4e3c117f2004667ea0512539a`.
- Callbacks: `build/v3-fire-callbacks-05/`, code SHA-256
  `172bdb4e01ea1061c31bfec1c2017a8fa3eb253d790a1163eac1056c5413da9b`.
- Callback-report SHA-256: `fd4c5741b54f83795c5e29a90ce0c5ae5ca870f60430a8fb31dd056070bcafab`.
- Native evidence: `build/v3-fire-native-02/results.json`, SHA-256
  `18db36a5a125c9c5ccfb4bc25e26bac02c90c5e7329555cec0402a2e567b78b0`.
- Two-fire offline subset: `build/v3-optional-fires-02/`.
  ROM SHA-256: `596bfd38b9d3b1a854e83cffa9236194677b262f7f23307c3db164ab5036c958`.

The input is the pinned ABI-69 fire-sound runtime, not an older content chain.
Complete native function/caller windows, donor profiles/rigs, all converted
assets, compiled code, free destination slots, and resource checksums are
verified before installation. The complete UPS reconstructs the output from
the verified original Japanese ROM.

## Runtime and memory

The shared fire callbacks use 1,240 bytes at `80483800`. Their two 20-byte
tables occupy `80483FC0` and `80483FD8`; the guard at `80483FF0` stays intact.
An initial preflight rejected a proposed table that touched that existing
guard. The corrected tables fit without moving it. No affected ROM was built
with that overlap.

The four-cell reader occupies 1,020 bytes at `80483000`, ending before the
unchanged tent callbacks. All five item bridges are rebound and the saved
resource CRC is refreshed. The complete-object loader admits the exact two
fire index/item/vtable combinations, retaining the tent, speed bag, ordinary
objects, and clothing routes. All eight public helper bridges remain bound to
the actual compiled entries. Its 1,828-byte code leaves 220 bytes spare.

Full model slots are `02468000` and `0246A000`. The resident package, ordinary
heaps, dedicated model banks, and menu allocations do not grow. The directory
retains all 3,389 entries and its sole terminator. The import resource has
2,603,056 bytes, with 1,525,712 VROM bytes remaining. Catalogue code uses 3,504
of 3,664 reserved bytes. Its 472 furniture and 248 clothing entries require
280,448 of the existing 280,704 menu bytes. Further batches must account for
those remaining limits.

The room/catalogue callback argument selects the correct frame counter without
reading unused native actor padding. Full native rig traversal supplies the
flame anchor; the after-draw callback applies the camera billboard, 90-degree
Y rotation, and actor scale times 0.01. Both display heads retain their native
segment-D matrix bank.

Each draw checks both command heads, reserves 176 frame-owned bytes plus at
most 15 alignment bytes, and emits five commands on each head. Previously
submitted scroll lists and flame matrices are immutable. Unaligned arena tails
are accepted safely; exhaustion produces no partial write. Native writeback
covers frame resources and both used actor matrices. The original draw review
identified an unnecessarily strict aligned-tail condition; the final callback
aligns its own reservation instead, and the native check explicitly supplies
eight-byte-offset arena tails.

The GC-to-N64 scroll conversion preserves actual speed, unsigned wrapping, and
phase without drift. Bonfire's odd vertical frames quantise downward by 1/8
texel because native tile origins have quarter-texel precision. Textures and
vertex coordinates remain complete and unchanged.

## Verification

`python3 -m unittest tests.test_v3_fire tests.test_v3_fire_runtime tests.test_v3_optional_composition -v`
passes **21 tests in 21.338 seconds** on the final cartridge. Tests include
complete source/profile/asset checks, actual C callbacks under address/undefined
behaviour sanitizers, sound identity and state exclusions, full billboard call
order, scrolling across wrap boundaries, all byte alignments near exhaustion,
immutable frame data, complete DMA gates, catalogue framing/order restrictions,
all/empty/individual composition, and save dependency checks.

The current silent native run passes **110 records, 24 calls, and 90 assertions**.
It cold-boots ABI 70, loads both complete models through the installed native
DMA gate, constructs and advances both actual rigs, and executes the installed
draw callbacks through the native matrix/keyframe engine. Catalogue and room
frame selection, full opaque/translucent commands, two scrolling tiles,
unaligned arena consumption, matrix-stack balance, unused matrices, English
names/prices, and one/four-cell placement all pass.

Private allocation, stack, resident-code/table, save-runtime, prefix, and fault
checks pass. The fixture restores bank contents, indices, segment bases, matrix
ownership, and the room descriptor, frees its allocation, restores the emulator
checkpoint, and shuts down cleanly. No hardware audio is emitted. The retained
initial integration also passed; the final run targets the changed aligned
allocation logic, not an old cartridge replay. Neither native run needs a
testing-setup retry; new harness work stays within the 30-minute batch budget.

This verifies generated native draw commands, not GPU appearance or listening
quality. The separate unchanged audio resource/sample evidence remains in
[Fire sound runtime](V3_FIRE_SOUND_RUNTIME.md). Ordinary acquisition, placement,
appearance, interaction, persistence, and original-hardware acceptance remain
unverified; this is not a complete-import playtest handoff.

## Continuation and saves

Complete the real summer-camper reward route for all ten items. The collectible
lantern and sleeping bag correctly retain their donor's null callbacks and
contact/interaction flags; the separate scene lantern is not that furniture.
Continue the other requested donor content,
ordinary villager/item gameplay and persistence, browser composition, and later
e/e+ donor assessment. None of that work is replaced by this actor milestone.

Saved structures remain format 2. Saves referencing either fire require a
matching/superset selected-import profile and must not be loaded by V2 or a
profile lacking that import. The actual codec checks remain passing; ordinary
cross-build reload is not newly established. Both web patchers remain V2 until
user testing and explicit approval.
