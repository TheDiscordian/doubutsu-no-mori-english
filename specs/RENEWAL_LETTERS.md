# Complete renewal mailbox publication

The optional `--english-renewal-letters` ROM build installs all three complete
English shop-renovation letters through the native mailbox destination. It
requires the complete leaflet creator, catalogue two, snapshot reader, and
leaflet date patch. No ordinary dialogue, font metric, saved layout, or resident
module size changes.

## Native ownership and publication

`af_renewal_deliver` retains the original four-home selection, player-to-home
mapping, free mailbox slot search, unowned-home exclusion, and working-player
exclusion. The original missing-map fallback and shop-level mask are preserved.
No eligible recipients counts as a successful no-op, matching the native caller.

One complete letter is staged before any home copy. Its timestamp is the original
planned reopening date; the full English template describes the preceding closed
day. Each selected recipient receives the same complete snapshot with that
player's native identity. Original clear/copy/free-slot helpers remain installed.
The synchronous main-thread operation has no fallible generation step after its
first mailbox write. Complete preparation and reader validation must succeed
before publication.

Temporary work requires 5,471 allocated bytes including alignment allowance.
The MIPS adapter frame is 96 bytes. Allocation is freed on every completed path;
no pending heap pointer escapes. Failed allocation, invalid inputs, or failed
catalogue restoration retain every mailbox and the capitalization state.

The native call at `809586A8` remains. The patched gate at `809586B0` clears the
saved notification bit at `80135C12` only after success; failure returns through
the original epilogue without clearing it. The original no-notification path
prevents duplicate letters. Original date-selection and schedule branches remain.

## Loaded image and guards

The general-actor image keeps its complete native 3,712-byte prefix and unchanged
profile at `80959040`. The 3,100-byte creator and 660-byte delivery adapter follow.
The installed image is 7,472 bytes with a 208-byte merged relocation file. It uses
the general actor heap, not the distinct fortune-NPC pool. Its 12 KiB image budget
is an installer bound, not a claim about the original allocator's pool size.

Native DMA rows `0084D180` and `0084E000` retain their indices and adjacency while
moving to `03700000` and `03708000`. Ownership metadata at `801011B0` receives
matching loaded bounds. Native data/profile references, creator internal jumps,
adapter imports, and the entry trampoline all have checked relocations. Unknown
instructions, sources, imports, overlaps, helper changes, or dependencies reject
the entire install without publishing partial replacement maps.

## Verification and limits

Nine host adapter/installer tests pass. They exercise all 24 home permutations,
four shop levels, ten mailbox positions, every owner/working mask, alignment,
allocation failure, every selected cartridge-read failure, retries, source and
relocation mutations, unchanged ownership/profile data, and atomic installation.
Independent Docker builds produce identical code, relocation, and manifest files.

The silent native batch passes 24 level/capitalization/calendar combinations,
five eligibility cases, complete mailbox-to-reader restoration, actual caller
failure retention and retry, and the original duplicate-prevention branch.
It checks 532 memory assertions across 165 calls, followed by successful
checkpoint restoration. The live save and globals are restored; RNG, handbill
fields, heap accounting, guards, blank cartridge/Pak saves, and shutdown pass.

The native test enters the actual delivery call and gate through an owned frame
shim; it does not traverse the scheduling/date-selection prefix. Normal shop
progression, scheduled delivery, broader gameplay/save validation, and physical
hardware remain unverified. No result here completes those requirements.

See [the work record](../docs/checkpoints/RENEWAL_LETTERS.md) for exact artifact
identities. Event-manager sale and Redd letters remain the next integration.
