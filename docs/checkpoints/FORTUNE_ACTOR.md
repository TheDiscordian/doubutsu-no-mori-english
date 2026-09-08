# Complete fortune actor work record

This checkpoint connects the complete fortune snapshot creator to the native
Miko hand-off. Original price, luck assignment, outcome initializer, surrounding
messages, and other callbacks remain intact. The new callback stores a complete
letter before issuing the original five hand-off orders. Selected values belong
to the actor and survive failed synchronous attempts, without a retained heap
allocation. Cancellation across actor removal is not solved by this checkpoint.

## Implementation and ownership

Four source files define the adapter, state ABI, original-actor prefix, and
link layout. The native actor grows from 2,992 file bytes plus sixteen BSS bytes
to 7,248 loaded bytes, within its existing 8,192-byte slot. Its 2,376-byte instance
grows to the existing 2,400-byte maximum. Native allocator and profile-sized clear
instructions are guarded. Original BSS addresses remain materialised zeros.

Only profile size and two native callback-table words change in the original
actor. Its 51 relocation records retain their order, with adjusted section
offsets; the linked ELF supplies all additional internal/import records. The
complete relocation file is 288 bytes. The native loader independently produces
the exact relocated image expected by the host model. Actor/relocation DMA rows
retain their indices and adjacency at new VROM `03600000`/`03608000`.

Native give work occupies 5,456 aligned bytes, allocated with fifteen bytes of
alignment slack and freed within the same callback. Native stack frames are
zero bytes for the init wrapper, 88 for give, 64 for the complete fortune
creator, and 216 for general generation before nested reader calls. No resident
module or saved layout grows. Complete words are not shortened for the native
ten-byte handbill table; that shared table is no longer used or modified here.

## Executed evidence

Eleven focused tests pass in 6.518 seconds:
`build/tests-fortune-actor-focused.log`. Tests cover full formatter transactions,
original RNG progression, all heap alignments, every selected read failure,
owner/order changes, invalid states, full pockets, repeated delivery, two actor
instances, source mutations, import/relocation checks, and atomic install failure.
The initial mutation fixture incorrectly used an uncompressed main-code offset
inside compressed physical ROM storage. It now changes the extracted code and
reinserts that file before testing the guard; no production check was removed.

`build/smoke-fortune-actor-01` passes 24 complete outcome/template/capitalization
cases and all ten pocket positions, with native metadata and the real get/set,
clear, recipient, copy, allocator, and action helpers. Its 88 native calls and
578 memory assertions include the full relocated image, complete saved envelopes,
full pocket-to-reader text, full-pocket rejection, four disabled-resource attempts,
successful same-choice retry, duplicate prevention, and unchanged heap accounting.
The fixture allocation is freed; full live save, handbill fields, memory guards,
checkpoint restoration, blank FlashRAM/Pak, and graceful shutdown pass.
The result file has 675 rows and 579 total assertions including post-restore state.

Evidence hashes:

- Scenario: `ca1225df61f6fcc552e19970d536184435e0ad60fa2930745d0568e91887f4f7`.
- Results: `283cca9c8b5c82b1f880d8ec08f9e83225eb40a6a3a5a8f2b7f5c5ebf7606612`.
- Native helper: `7e954208d42c9625e8efde73cb32e5ddd13da3037227d57c772c607bfae4d8ef`.
- Runner: `f412d9d85678fc85a15490a993c46614843df0f03109f237568a3b33a73365b2`.

The full regression suite passes all 881 tests in 332.633 seconds:
`build/tests-fortune-actor-full.log`. A second independent build in
`build/fortune-actor-repro` produces identical actor and relocation files.
Independent extraction reconstructs all 13,383 applied ordinary edits; applying
the UPS to the verified original ROM reproduces the new cartridge. Current
module verification and unchanged font/module/catalogue resource checks pass.

## Cartridge artifacts

`build/fortune-actor-pilot/animal-forest-halfwidth.z64` is 32 MiB, SHA-256
`8daa366285e587fde2e53fcc748645d53849742c04643b7458c926d143a66869`.
Its 4,038,937-byte UPS has SHA-256
`ed36738260f1155a8cef4ab15b98ca53f645289c5363e494276e5f3219d9df00`.

The extended actor SHA-256 is
`20af6197fe1280c2d127975f4318ccd1ca2ec07f1da1cac705e3bb1b29e3a426`;
relocations are
`407effa34d7a9fc4e3feb66271f707f7680ed8a9655462ec30929d8d2ef101ec`.
Compared with the foundation pilot, the only changed shared DMA files are
the main code and DMA table; the native Miko actor/relocation pair is replaced
at its new virtual addresses. All ordinary text banks, catalogues, resident
module, and font resources remain unchanged. There is no ordinary text-coverage
increase for this actor integration.

## Required continuation

The give callback's retry state is not persistent recovery: a forced initializer
resets it, and removing the actor discards it. Trace the native talk cancellation
and removal routes; either prove that these cannot abandon an already paid slip
or implement recovery without double charging, rerolling, or duplicate delivery.
Do not claim that check is complete from synchronous failure/heap tests.

Normal paid reading, subsequent player input/animation, visible letter-window
rendering, remaining mail/save paths, semantic review, and hardware acceptance
remain. Continue bulk general strings and their consumers alongside that audit;
the unrelated ordinary NPC-letter failure remains deferred. Title-first GC image
replacement, GC-style keyboard, final review, and patch-only release preparation
remain part of the complete goal. The repository stays private, and ROMs, donor
assets/text, generated patches, and isolated saves stay ignored.
