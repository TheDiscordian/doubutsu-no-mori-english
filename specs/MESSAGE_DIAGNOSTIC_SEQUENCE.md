# Complete native message-system diagnostic

`native_message_diagnostic` installs the complete original English translation
of `0004` as `0004 → 2AEB`. The independent whole-source record is
`translations/n64-message-diagnostic.json`; the sequence approval must match it.
There is no GameCube translation attribution. The native diagnostic exercises
letter display, item/free/country fields, random numbers, player-variable
assignments, cancellation, clock/name fields, colours, and display delays.

Keep all 62 native commands and arguments in order, every manual line/page
boundary, repeated sample, and instruction. The 961-byte English source expands
conservatively to 1,581 bytes. The ordinary 1,024-byte buffer check must reject
it as one record. Additional page commands would not fix that storage limit.

Only the existing wait/newline/clear separator `[416,421)` changes. The first
part retains `[0,416)`, then adds `7F0E2AEB CD 7F01`; the second retains
`[421,961)`, including the final native `00`. Replacing that separator on
reconstruction must recover the complete original English without any text or
control change. Stored lengths are 423/540 bytes; expansion bounds are 713/886.
Do not add a second wait, move a command, or shorten an explanation.

## Reserve and retained state

`2AEB` is a native train-demo reserve with source hash
`0727aac8e3f598400dccbb8e9a23f39c10b3bc13e0dc1c168b93d03c0aa95609`.
It belongs to no other sequence or explicit reference-identity override.
Scan every native script target and the pinned executable arithmetic/comparison/
logical immediates and aligned non-executable data halfwords before acceptance.
Require zero hits. This does not prove the absence of computed callers.
The translated reserve label becomes continuation content; that is not another
newly translated source record. Removing this ordinary alias donor leaves one
unanimous complete reference for reserve labels `0487..0489`: GameCube `0485`,
"Train Demo / Extra Space", in place of the original draft "Extra Area".
Only these three existing reserve labels also change, without any command or
accounting credit change. Every other previous English edit remains exact.

Native `07` disables cancellation, and `06` enables it. Both occur in the first
part, before the split, leaving cancellation enabled. `8009E658` loads the next
record, resets the cursor/line state, and sets the native timer to 10.0; it does
not clear cancellation-enabled state. Regular page setup `800A04E4` clears the
active cancellation flag at `2BC`, retaining the enabled flag at `2C0`.

Prepared free fields occupy twenty ten-byte rows at window `38`; five ten-byte
item mirrors follow at `100`, and the 68-byte mail field follows at `132`.
Neither transition may alter these prepared fields. Preserve the native window,
resident full-name storage, save layout, font, and actual memory requirement.
Both records require the existing resident-runtime build and all-or-nothing
sequence validation; no new runtime command or buffer allocation is introduced.

## Acceptance

Check source/payload hashes, all commands, full reconstruction, capacity,
rejection of partial/stale/changed/runtime-less requests, the reserve scan,
actual ROM entries, all prior resources, and the original-ROM UPS reconstruction.
Combined accounting adds only the complete diagnostic root, never extra credit
for reusing an already-English reserve. Check remaining Japanese message-bank
records separately; a complete message bank does not finish other text resources.

The silent native scenario loads both complete records, dispatches their link
and both phases of their terminators, and executes the actual message-change and
ordinary page-setup routines for both active-cancellation states. A private
window holds distinct complete free/item/mail fixtures. Require complete output,
retained fields and cancellation-enabled state, cursor/timer resets, adjacent
guards, restored stack/checkpoint, blank isolated saves, and graceful shutdown.
Do not execute the player's variable-assignment, RNG, mail-display, or sound
diagnostics on the real singleton. This does not prove rendered diagnostic
playback, ordinary actor traversal, field expansion during rendering, save/reload,
or hardware. Those remain gameplay and playthrough requirements.
