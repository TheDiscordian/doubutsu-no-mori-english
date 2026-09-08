# Complete snooty resident letter-sharing explanation

Native `0912` explains the resident's habit of keeping received letters, showing
them to friends, taking them when moving, and accepting another letter to replace
an embarrassing one. The complete supplied GameCube localisation adds its own
writing criticism and calming aside without changing those gameplay claims.

The complete English record has 1,226 encoded bytes and a conservative expanded
bound of 1,362. `0912 → 2B47` replaces only the existing reference page transition
`[659,664)`, exactly `7F04 CD 7F02`, after the warning against embarrassing letters.
The two parts contain 666 and 562 encoded bytes, with expanded bounds 742 and
638. The intermediate link ends with `01`; the second part retains native `00`.
No message buffer, bank count, saved format, or production runtime changes.

Every English word, manual newline, other page boundary, pause, and catchphrase
remains. The original reference's dash byte `90` is preserved as punctuation;
the import does not invent substitute wording or adjust the approved font.

## Source and expression guards

The full native root, full supplied reference, both resulting payloads, and
reserve each have independent hashes in `translations/reference_sequences.json`.
Native `2B47` is a generic reserve with no incoming native message-script target,
relevant arithmetic/comparison/logical code immediate, or aligned data halfword
reference in the pinned section scan. Nearby slots with data hits are not used.

The calming aside uses speaker-zero expression `13`. Supporting native `0541`
is the same snooty personality's standing morning greeting and already uses
`13`, followed by the ordinary `FF` talk reset. The existing shared resident
selector accepts this expression in its six held-item tables; no sleeping-state,
mood, timer, quest, or other actor request is inherited. Only this exact additional
expression is approved. All other expressions already occur in native `0912`.
See the [shared resident consumer](RESIDENT_ANIMATIONS.md).

Complete reference reconstruction and all-member installation are mandatory.
Missing parts, altered wording, stale supporting sources, changed continuation
targets, and new actor or field requests fail. Both basic and full configurations
use the same two complete payloads.

## Acceptance

Host tests cover full reconstruction, both bounds, exact field and action scope,
partial/mutated rejection, the supporting expression, and the reserve scan.
The bounded sequence scenario checks actual cartridge loading, the native
continuation assignment, both phases of each terminator, and memory guards in
one restored checkpoint with silent audio and isolated blank saves.

Normal first-job progression, letter viewing/sharing, expression rendering,
final wording/layout, and original hardware remain gameplay/playthrough checks.

The four focused tests and eleven placeholder tests pass. The 74-test sequence
batch passes after its basic-generation allocation expectation is brought to
62 parts; all seventeen reference-sequence tests pass in the confirming run.
Full generation has seventy sequence parts and 25 allocated native labels.

`build/smoke-snooty-letter-01/` passes forty recorded steps, seven native calls,
and fifteen memory assertions. Both complete loads, the continuation target,
both ending phases, stack/buffer/module guards, checkpoint restoration, graceful
shutdown, and blank FlashRAM/Pak pass. Independent scenario regeneration checks
all call arguments/returns, complete reads, and fixture writes. The installed
candidate audit checks all 12,602 edits and complete original-ROM UPS recovery.
Only the main text, cumulative message table, and ROM DMA metadata differ from
the previous cartridge-font pilot; production code and all other assets remain.
