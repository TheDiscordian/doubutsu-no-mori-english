# Pelly and Phyllis receipt failure handling

Both reason-indexed message lookups and the real action-initializer checks pass
native validation. Normal post-office gameplay remains unverified.

## Ownership and behaviour

The native inventory send handler at `808725C8..80872684` sets the selected
letter's font/status to **zero**, copies all 164 bytes to submenu offset `38`,
clears the player pocket, and records its index at submenu offset `DF`.
The GameCube source uses a named status constant; the N64 instruction is the
authority for its numeric value. The verified native range has SHA-256
`7145ad292f25dcaf9e67d4c8f26368eda658627dd747e52f5f1cfc9e8110f47b`.
The original slot is available for the existing refusal path to restore.

`tools/pelly_receipt.py` installs only with the complete-record NPC send and
lower-level post-office guard. At `809C47C8`, a resident shim checks the public
receipt return. Success retains the native receipt message, action three,
next action five, and common staged-letter clear. Failure enters the original
refusal copy path at `809C47DC` with reason four and status one. That native
path restores the entire letter to the selected pocket, including its gift,
paper, split marker, identities, and complete text, before clearing the staged
copy. The new index shim maps reason four to the neutral `08E1/08E2` introduction
and action six. Existing reasons retain their original indices.

The original hand-back and later state handlers remain in the overlay. The
state-eight initializer's second reason-indexed introduction lookup maps reason
four to reason one's neutral introduction. This requires its own shim: the
receive-menu index alone does not protect the later table, where index four
would select the unrelated following table's message. All three direct accesses
to the reason byte in the original overlay are inventoried and guarded. The
refusal explanation selector at `809C3F30` adds reason four while preserving
reason two's full-mailbox message, reason three's delivery-limit message, and
the default unknown-recipient message. New receipt failures do not falsely
report either a full mailbox or a missing recipient.

## Original English errors

The main bank gains two original port-error records at `2DE8` and `2DE9`.
Pelly apologizes and says the letter could not be sent and has been returned.
Phyllis says it could not be sent and tells the player to take it back.
Both retain native order-nine and continue controls for the existing
after-refusal state. These are new errors, not edits to GameCube dialogue.

All 11,752 existing records remain unchanged by this installer, including
their explicit lines, pages, pauses, and other controls. The table retains its
original length: two unused cumulative-offset words hold the new ends, and a
third remains zero as the terminator. The data bank is padded to sixteen bytes.
The native main-message bounds at `8009E3A4` and `8009E668` become 11,754.
A scan of the pinned executable sections finds only these two immediate bounds
at the old count or its adjacent values; this is not a general computed-value
proof. Both new records pass complete native DMA loading through the actor.

## Installation and memory

Installation verifies the original receive and pocket-removal functions,
message selector, lower-level receipt guard, both message-count instructions,
unused table words, linked resident bytes, and all patch overlaps. It validates
every planned replacement before publishing changes. Pelly's overlay length
and relocation file remain unchanged; none of the changed instructions has an
original relocation. The new calls/table address point into resident memory.

The module occupies 24,352 bytes of its unchanged 32 KiB reservation. The
24 KiB linked-code limit leaves 224 bytes before the separate 8 KiB test area.
All three short shims use the original caller's stack and add no stack frames.
The font atlas, approved advance metrics, original save layout, and existing
GameCube candidate text are unchanged. Snapshot generation remains disabled.

## Validation and limitations

The native handler run passes 48 receipt cases: eight accepted classic/composite
letter cases at the first and last pocket for both sisters, and forty rejected
classic/composite cases across all ten pockets for both sisters. Complete player
state, NPC population, delivery counters, returned records, staged clearing,
actor decisions, all loaded message bytes, stack guards, allocation guards, and
the module guard pass. Successful actor outcomes are compared with the already
tested public receipt function from the same controlled pre-send state.
Sixteen selector cases cover both sisters, all normal refusal reasons, the new
reason, and unsigned default boundaries.
Eight hand-back initializer cases cover every supported reason for both sisters;
every rejected receipt also passes through the actual state-eight initializer.
Ten additional native index-shim boundaries confirm that the result in `v1`
retains `reason+1` except for the new reason-four mapping to index two.

The original overlay loader performs DMA, relocation, and cache maintenance.
The test independently models the pinned Pelly relocation list, including data
pointers and signed high/low instruction pairs, and checks the complete loaded
overlay. Explicit expected-code proofs permit injected calls into that verified
heap allocation and boot loader. Ordinary JSON calls retain their original
target restrictions and graph-thread requirement.

The fixture uses a synthetic actor and calls the real native setup function and
the action-three, six, eight, and ten initializers, including the second
introduction lookup. It explicitly invokes state eight instead of advancing a
normal actor animation, so these checks do **not** establish the
normal post-office hand-back animation, subsequent player input, or rendered
error-message progression. All touched state and then the complete machine
checkpoint are restored; FlashRAM remains blank. Ordinary post-office gameplay,
normal saving/reloading, complete snapshot metadata/reader coverage, lossless
editing, and original hardware remain required. Exact run hashes and counts
are recorded in the work log.
