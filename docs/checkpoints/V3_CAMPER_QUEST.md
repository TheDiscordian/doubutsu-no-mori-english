# Camper NPC profiles and quest lifecycle

## Implemented

ABI 78 adds explicit `D08F` handling to both native NPC controllers. Each
original special-NPC profile table has 110 entries; the camper index 143 is
outside that table. The pinned donor's two 144-entry tables both assign profile
`23` to the winter camper `D05E` and summer camper `D08F`. The installed adapters
use that actual shared camper actor, retain the full summer identity, and leave
every original table row and other profile lookup unchanged.

The two native loads keep their original HI/LO relocations. The former `lh`
becomes an address-producing `addiu`, followed by a resident call that chooses
the added profile or performs the original signed load. The original caller's
profile stack slot and following argument-setup delay slot remain intact.
Only eight bytes change in each complete current English NPC owner.

The current English quest manager distinguishes first and repeat summer talks.
Its existing preconditions, listen-state update, memory binding, and melody call
remain. Native modes 4/5 share the winter/summer common lifecycle: the donor's
normal-init functions perform the same setup for those two event families.
The session greeting flag is set at the first summer **talk start**, matching
the actual donor, not at greeting completion. Winter and ordinary talks do not
change the summer flag. Sharing this lifecycle does **not** install the summer
English messages, game choices, or rewards; those remain explicit next work.

The 112-byte resident helper occupies `804A2EC0..804A2F2F`, after the independent
camper registrar and before the package guard. No resident reservation, normal
heap, actor instance, saved format, or selected profile grows.

Quest routing replaces 72 bytes at `809550D8`, with four new HI/LO relocations
in place of eight old ones. All other current English owner instructions/data
and relocations remain. Its relocation file stays 800 bytes with 187 records.
Because the original physical file is compressed, a checked 800-byte raw alias
is appended to the existing trailing ROM resource. The same virtual file ID,
directory slot, runtime extent, and original compressed bytes are preserved.
Only that physical pointer and the enclosing ROM-resource end change.

## Artifacts

- Full: `build/v3-camper-quest-runtime-02/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `f0a34dfed22880ac012cae1ebc6be22d0c49cade56c9d4b08a2e24bfc3d0c001`.
- UPS SHA-256: `672bc6997f47f12f9651f90179e41e7514e101d437a89799c38b6ad4ee10bf18`.
- Report SHA-256: `b1404f8d40ca28d68bda4f4319aa24d250779f432f66d9c3e17265cf4c57f93d`.
- Helper SHA-256: `386f90260f4188986370b2d26c1d2cfb0ab96798563bb1d683140cd514b8b32e`.
- Ten-item subset: `build/v3-optional-camper-quest-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `e91f663803a82123d9c79958a9eecfea51afc4c600b5e82c61c701ded4fc39a9`.

## Verification and limits

Seventeen focused/composition tests pass:
`python3 -m unittest tests.test_v3_camper_quest tests.test_v3_optional_composition -v`.
They verify both actual donor profile tables, complete current English owner
preservation, complete relocation at two bases, bounded ROM aliasing, package
and prefix checksums, and unchanged saved profiles. All 59 experimental choices
remain; all-selected and empty profiles return exact full/V2 cartridges.

The initial native probe cannot allocate a second complete NPC controller in
the title's normal heap and returns null before loading any controller. Its
corrected fixture borrows checked model-pool storage while the game thread is
paused, snapshots it, and restores it before resuming. This tests the actual
native loader and changed instructions, not ordinary actor allocation.
The corrected silent run `build/v3-camper-quest-native-02/results.json` passes
68 records, five calls, and 55 assertions, with zero failures. Result SHA-256:
`85271a19598bf7319f75d984373ebf3e5713c19659b0ec6e929053251b46c340`.
It loads/relocates all three complete actual owners, including BSS, with the
native loader. Twelve native instruction windows cover each NPC controller's
ordinary, winter, and summer profile lookup, first/repeat summer quest modes,
both winter modes, ordinary mode, and a repeat that must not set the greeting
flag. Register preservation, delay slots, exact profile stack writes, session
state, guards, unchanged saved town, and restored borrowed storage pass.
The runner restores its checkpoint, resumes without a fault, and exits gracefully.
It does not request an ordinary FlashRAM save/reload or complete conversation.

The initial compile-only directory contains no ROM: the builder rejects the
compressed relocation slot before output. The accepted build uses the explicit
ROM alias described above. One focused-test expectation is corrected to include
the DMA-directory resource's own changed contents; the cartridge is unchanged.

## Next work and boundary

Implement the actual summer English greeting selector, normal conversation
commands, and selected camping rewards. Continue remaining masked-reader review,
scene lighting/floor sounds, ordinary construction/entry/exit, acquisition,
and persistence. Full conversations, GPU appearance, and hardware play are not
established by these component checks.

Saved format 2 and selected identities are unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2. Ordinary cross-profile
save/reload remains unverified. Development source may be pushed on
`v3/optional-imports`; both served patchers remain V2 until user testing and
explicit approval. This is not a complete-import playtest handoff.
