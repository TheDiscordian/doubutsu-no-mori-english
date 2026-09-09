# Snowman gift letters

## Verified source scope

Twelve native templates `0202..020D` correspond to the twelve Snowman gifts.
The complete English catalogue has all 36 parts, with only item field zero in
each body. The existing sixteen-byte item resource contains every complete name,
including the sixteen-character wardrobe name. `tools/audit_snowman_letters.py`
binds the exact native actor, relocation, functions, gift table, supplied English
executable/functions/gift table, all name mappings, banks, decoder, parts, and
field sets. Source approval alone is not installed translation credit.

Native actor VROM `00862870`, linked RAM `8096DC30`, has 16,912 file bytes.
Its separate relocation at `00866A80` has 1,104 bytes, with sections
`(16400,208,304,0,269)`. The creator `8096E1A4..8096E274` is 208 bytes and
its allocating owner `8096E274..8096E2EC` is 120 bytes. The gift table at
`80971C88` contains `1EA4/1EA8/1EAC/1EB0/1EB4/1EB8/1EBC/1EC0/1EC4/1EC8/2619/2719`.
The GameCube table's ten furniture IDs are `1F54..1F78` in steps of four;
flooring and wallpaper IDs agree. The GameCube name table divides furniture IDs
by four; the native wider resource retains its orientation-indexed slots.

## Creation and delivery requirements

Keep native selection: one random draw selects one of twelve gifts. GameCube's
collection-aware reroll is not present in this N64 function and must not be
introduced by a text port. The current private player pointer is `80136FD8`.
Preserve paper twelve, font zero, mail type eight, native cleared sender identity,
recipient identity/type, gift, and complete supplied wording/manual breaks.
The twelve selected gifts and their full names are fixed. At build time,
`tools/snowman_snapshots.py` captures each complete sixteen-byte name, packs its
catalogue-four record, and reconstructs the full English letter for both initial
capitalization states. Every supplied word, manual break, and field is retained.
Twenty-four immutable rows contain gift, final capitalization, and the first
32 bytes of the packed record. Its used length is 29 bytes; the remaining saved
record bytes are zero. Each 36-byte row is validated against the registered
catalogue, full native/donor source approvals, and the complete reader model.
The full table occupies 864 bytes.

The owner allocates 164 bytes, excludes non-local players, checks queue capacity,
clears the letter, creates it, submits native mode-zero receipt, and frees it.
The original owner ignores creation/receipt failure. The snowman-combination caller
at `809712BC` invokes that owner only for the perfect-build result and continues
to register the snowman. It has no verified durable pending-letter state.
The replacement initializes all 164 mail bytes, copies the current recipient,
selects the immutable row, and updates capitalization only after validating all
inputs and rejecting overlaps. Once writing starts, there is no fallible runtime
operation. The wrapper preserves the original single random draw. A gate uses
the words freed by removing the separate native clear call to skip receipt when
creation rejects a request. Allocation, foreign-player and queue checks, receipt
mode zero, and unconditional free remain in the original owner.

There is no additional per-letter allocation, item lookup, catalogue DMA, or
runtime formatter/reader call. Translation preparation therefore introduces no
new resource-failure point after the actor has loaded. The native 164-byte
allocation can still fail, and native receipt can still reject a full mailbox or
queue. The original perfect-build caller has no durable reward retry for those
conditions; this integration preserves that existing policy rather than claiming
that rejection retains a pending gift. No saved Snowman bits are repurposed.
Normal gameplay and full-mailbox behaviour remain in the acceptance queue.

## Actor ownership and installation

`tools/build_snowman_actor.py` appends 608 code bytes and the 864-byte immutable
table to the original actor. Its file is 18,384 bytes, with a 1,104-byte merged
relocation table containing 270 entries. BSS remains zero. The original prefix
changes only in the 208-byte creator and the 28-byte receipt gate. The C creator
has no stack frame or external calls; the wrapper uses 32 stack bytes.

The original adjacent DMA rows move to VROM `03900000` and `03908000`.
Ownership metadata at `80100FF0` retains the profile pointer, allocation policy,
and native actor lifetime while updating the file and RAM-end bounds. The actor
instance and saved structures do not grow. Code/data load through the native
overlay loader, not the resident mail creator. The 24,576-byte actor-image limit
is checked together with relocation targets, source hashes, exact approved
snapshots, and installed reader/font/catalogue resources. The resident image,
four-MiB layout, and museum creator remain unchanged.

`--english-snowman-letters build/snowman-actor` installs the completed actor
after validating a prospective ROM, before changing caller-owned build mappings.
The verifier round-trips the saved JSON manifest; source-function hash records
use JSON-compatible lists. Independent assembly checks the wrapper and gate.
The combined translation counter credits all 36 source parts only after actual
actor, relocation, metadata, reader, font, and catalogue verification.

## Acceptance

Complete native creation and reader comparisons must cover all twelve gifts,
both capitalization states, native RNG and metadata, exact full item fields,
build-time wrong-gift/template/resource rejection, runtime input/overlap
rejection, actual receipt, preserved native capacity policy, actor
relocation/ownership, restored live state and checkpoint, and blank isolated
saves. Disabled creation-time catalogue configuration must not prevent the
already-complete fixed snapshot from being queued; restored reader configuration
must reconstruct it fully. Normal gameplay, saving/reloading, and original
hardware remain explicit acceptance work. See the
[integration checkpoint](../docs/checkpoints/SNOWMAN_LETTERS.md) for measured
artifacts and test scope.
