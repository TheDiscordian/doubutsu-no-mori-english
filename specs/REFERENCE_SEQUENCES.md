# Reviewed multi-message reference sequences

## Purpose

Some English GameCube dialogue splits one long N64 message into several records.
Treating each record as an unrelated same-ID translation loses most of the text.
Concatenating the English records can exceed the unchanged 1,024-byte message
buffer. An explicitly reviewed sequence preserves the GameCube record boundaries,
line breaks, pages, emphasis, and timing while retaining N64 gameplay decisions.

## Home explanation

N64 message `07EA` contains the complete house/gyroid/save explanation and its
repeat-or-continue question. The GameCube sequence is `07EA → 0838 → 0839 → 083A`.
The three continuation slots already exist in the N64 bank and contain identical
opening-reserve placeholders. The final choices remain `0010` and `0036`; branch
zero goes to `081E`, and branch one goes to `081D`. Their token ordering differs,
but the choice-index mapping is the same. `081D` repeats from `07EA`.

Each English record fits separately: conservative expanded bounds are 523, 496,
530, and 347 bytes. No message-buffer or bank-entry-count increase is needed.
The native Nook guide's talk table enters through `07E6`; the explanation is
reached by message branches. Its code contains no direct reference to `07EA` or
the three continuation IDs. Broader reference and runtime checks still apply.

## Work offer

N64 `07EC` and the supplied GameCube `07EC` both describe the insufficient house
payment, the part-time-work arrangement, and the shop location. The complete
English record is 1,051 bytes, exceeding the N64 loader limit before substitution.
Use the existing train-demo reserve slot `2AE9` as its second part. The legacy
translation independently uses that same split; its presence is supporting
evidence, not permission to bypass native-source guards.

The split replaces the reference's existing button-wait/newline/page-clear span
at encoded offsets `472..476` with a continuing-message boundary. The first part
retains reference bytes `[0,472)`, then appends `0E 2AE9`, newline, and end `01`.
The second retains `[477,1051)`, including the original end `00`. This replaces
one page transition with one message transition; it does not add a second wait,
remove English text, or reflow lines. Expanded bounds are 495 and 650 bytes.

Slice-based approvals require the same complete source-reference hash, valid
token boundaries, complete ordered coverage of the reference, and only the
explicit native `04`/newline/`02` gap between parts. Each resulting payload has
its own approved hash. Final termination matches the native root; intermediate
parts continue. Native message scripts do not target `2AE9`, and the Nook guide
code contains no direct `07EC` or `2AE9` reference. Actor traversal still needs
runtime verification.

## Guarded approval

A sequence record binds every original slot hash and exact approved English
encoded hash, with reference provenance and an explanation of the adaptation.
Every member must be installed together. Unknown sequences, partial installation,
changed source slots, changed translated bytes, new external branches, new actor
arguments, unavailable dynamic fields, and overlong parts fail the build.

Only reviewed presentation differences are permitted. Gameplay commands remain
ordered after removing the explicitly declared internal continuation links.
Adjacent conditional-branch assignments are compared by branch opcode rather
than textual order. The original choice labels and exit mapping remain intact.
Actor-animation commands may reuse only argument tuples present in the source
message; their placement follows the approved GameCube text. Display colour spans,
page divisions, and pauses follow the approved reference exactly.

Reserved continuation slots require their expected placeholder hashes and no
incoming native message-script branches. This does not grant general permission
to reuse arbitrary message IDs. New sequence approvals require their own review.

## Acceptance

Tests reject mutated members, missing members, stale placeholders, new branches,
and incompatible command/data requests. Runtime tests must traverse every link,
exercise both final choices, preserve actor progress, and retain memory guards.
Passing a sequence's static checks does not mark its visual or gameplay review
complete. A test build may inject its entry through an isolated checkpoint only;
normal progression is tested separately.

`tools/sequence_test_scenario.py` generates a local-only native regression from
the built ROM. It checks all four actual cartridge loads, all three continuation
assignments, both phases of the native continuing terminator, both final branch
indices, and the native repeat response back to `07EA`. Scratch-buffer and module
guards remain intact, and the emulator checkpoint is restored after injected
calls. This test does not replace normal actor progression or presentation review.
