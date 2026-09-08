# Interrupted fortune-payment recovery work record

The optional complete fortune actor now recovers an intact unfinished payment
on talk end, profile save/destruction, or reinitialization. It refunds exactly
the original wallet and any consumed Bell bag, once. Normal successful readings
retain the original fifty-Bell price and charge/luck timing. This is not persistent
letter recovery and does not undo an already revealed fortune.

## Native contract and implementation

The existing 24-byte pending extension uses its final word as a tagged payment
descriptor: original seventeen-bit wallet, consumed pocket plus one, and native
denomination index. All four native bags and fifteen pockets are represented.
The charge wrapper captures those values before calling the original native
helper. Native type assignment in the original call's delay slot stays intact.

Recovery requires the same current player, the exact expected post-charge balance,
and an empty normal-condition pocket when a bag was consumed. It clears payment
and marks cancellation after restoring those values. Reused pockets, changed
balances/owners, malformed descriptors, and unavailable current players cause no
writes. Delivered letters cannot be refunded or duplicated. An unsafe recovery
also prevents reinitialization from silently discarding the pending descriptor.
The original callbacks still run on end/save/destruction.

Native conversation `1915` can finish without a successful new creator attempt.
The end wrapper lets the original callback attempt delivery before testing its
end result. `Actor_dt` calls the profile save callback before the destructor;
`Actor_info_save_actor` also uses that save callback. Original currency lookup,
count, possession, collection, talk-end, and actor-cleanup functions have guarded
hashes in both source and installed main code. Conflicting patches are rejected
before installation publishes any replacement maps.

Eight original actor words change: profile size, five callback pointers, charge
argument, and charge call. The unchanged original payment helper, original luck
store, native outcome initializer, and surrounding message order remain.
The actor occupies 8,032 of its native 8,192 resident bytes, with a 2,400-byte
instance. The 336 relocation bytes use separate loader scratch. Native
`ovlmgr_Load` supplies no relocation buffer; its implementation allocates and
frees that scratch independently of the NPC resident slot. No shared pool grows.
The native batch directly tests relocation with caller-owned separate scratch;
implicit loader allocation is established by source, not that specific call.

MIPS frames: init 32, give 88, charge 48, refund zero, end/save/destructor 24,
fortune creator 64, and general generation 216 bytes before nested reader calls.
The 5,471-byte synchronous give allocation remains fully freed on each attempt.

## Executed evidence

All 886 regression tests pass in 382.541 seconds:
`build/tests-fortune-recovery-full.log`. This includes sixteen adapter/installer
tests: complete formatter transactions, 180 bag/refund combinations plus wallet
boundaries, all cleanup wrappers, completed-letter retention, duplicate charging
rejection, owner/balance/pocket/descriptor mutations, native helper guards,
complete relocations, and atomic install rollback. Host native helpers are mocks;
the real formatter, snapshots, and catalogue code execute in the host fixtures.

The silent four-MiB native batch in `build/smoke-fortune-recovery-01` passes:

- 24 complete outcome/template/capitalization hand-offs and pocket-to-reader cases.
- Every letter pocket, full-pocket rejection, retained-choice retry, and no duplicate delivery.
- 64 exact refunds: every denomination/pocket combination and four wallet-only cases.
- Original payment/effect-tail execution through the installed charge call site.
- 374 native calls, 1,255 memory assertions, and one post-restore assertion.
- Complete live-save and handbill retention, heap accounting, allocation/stack/code guards,
  freed fixture allocation, restored checkpoint, blank FlashRAM/Pak, and graceful shutdown.

Eight bag cases first fail generation with the catalogue disabled, then recover
the selected pending payment. Other refunds cover the preselection state.
Real abort/payment routines execute in owned synthetic player/actor storage.
The new end/save/destructor wrappers are installed and host/source verified;
normal player-driven scene removal is not established by this native batch.

Evidence hashes:

- Scenario: `b043ad2c1b28e7e52a4d2aec332b521b3192a4d15529e65a3a7cf46ac0b8f60a`.
- Results: `1c5a0a7a9367cf1c75fba5853620293aef5ff26d589c2238623a1d5255889456`.
- Native helper: `e38dd6b030048e6a7e3459fbf3dcf995eb382fdcc79d4cfe641832c8494d2f84`.
- Runner: `f412d9d85678fc85a15490a993c46614843df0f03109f237568a3b33a73365b2`.

Independent builds in `build/fortune-recovery-actor` and
`build/fortune-recovery-repro` produce identical actor and relocation files.
The final rebuild changes report wording/host guards but reproduces the exact
ROM used by the native batch. `build/verify-fortune-recovery-install.log` records
independent reconstruction of all 13,383 ordinary applied edits, resident-module
verification, and an original-ROM UPS round trip. Its initial comparison expected
the wrong DMA-table virtual address; the corrected comparison checks `00019D40`.
No production output changed to satisfy that comparison.

## Local cartridge artifacts

`build/fortune-recovery-pilot/animal-forest-halfwidth.z64`, 32 MiB, SHA-256:
`047acf5f0bf53ebb2ce422d919297cf096187274b8a496c6e48ddda698c15001`.
The 4,039,904-byte UPS has SHA-256
`b5c7a0b68f99e6b805d61499ff4982520bcbc3bb17e75ff27674c1a3529ea95a`.

Actor: `7402a5d3305cfd2a81cbdd9745283833f594c8a24a8515778ca336d2470d52e1`.
Relocations: `81abbcfd68d80a30724458c2b508abcab0b27ed807cdd1846e131647722b5199`.
Compared with the preceding hand-off pilot, only DMA table `00019D40`, main code
`00675720`, actor `03600000`, and relocations `03608000` change. Every other DMA
file, including ordinary text, both catalogues, font, and resident module,
remains identical. This recovery checkpoint adds no ordinary translated records.

## Required continuation

Validate normal paid reading, interrupted talk/scene cleanup, subsequent player
input/animation, visible letter-window rendering, remaining mail/save paths, and
hardware. Safe refusal on externally changed payment state is not a promise to
recover such arbitrary states. The unrelated ordinary NPC creator rejection
remains deferred rather than claimed fixed by the fortune tests.

Continue the remaining general strings and their actual callers. Default
catchphrases, wider special names, dates, and fortune words already have scoped
display resources; remaining ordinary-bank Japanese counts do not establish
which other readers are complete. The 200 name-like rows `009C..0163` also remain
Japanese in the supplied English disc; do not treat its Western glyph decoding
as valid English names. Trace their native consumers before translating them.

Title-first GameCube artwork, the GameCube-style keyboard, complete semantic and
layout review, stability/save checks, and patch-only release preparation remain
in the full goal. Inputs, donor text/assets, ROMs, generated patches, and isolated
saves remain ignored; the repository remains private.
