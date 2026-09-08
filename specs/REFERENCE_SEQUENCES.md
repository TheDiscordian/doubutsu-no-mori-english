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

## House purchase confirmation

The one-record `nook_house_purchase` approval retains the complete English
`07E9`: purchase confirmation, the unsold-radio gift, and the introduction to
the home explanation. The GameCube repeats the two existing native emotion
argument tuples at its added page boundaries. Its small-print aside uses native
line anchor 2 and line scale 20/32; the Japanese version uses a Y offset and
repeated per-character scaling. Those native formatting controls have verified
consumers and parameter guards. Neither presentation is automatically reflowed.

The exact approved payload keeps the native BGM operations, player field,
outgoing `0E 07EA`, and continuing terminator. One-member approvals need the same
source/reference/payload hashes and structural checks as larger sequences.
An external continuation is permitted only in the final member and must match
the original root's complete outgoing-link list and gameplay-command order.
No new target or omitted original link is accepted.

## Planting-job completion

The one-record `nook_planting_complete` approval retains the complete English
`07F9`. Both games acknowledge the planting, give the same eighty-Bell wage
toward the mortgage, and continue to the next task with native end `01`. Normal
N64 progression reaches the source record after all ten supplied plants are used.
The GameCube repeats the already-present emotion tuples `000015` and `0000FF`
during its mortgage aside; no new actor argument or gameplay action is introduced.
Retain its entire text, manual line/page breaks, and pauses. Its 644 encoded bytes
fit the native message buffer with the normal expansion reserve.

## Introductory-job coverage

Six one-record approvals retain the complete GameCube letter wage (`080B`),
delivery/reporting reminders (`080E`, `0815`), package-wait instruction (`0827`),
Happy Room Academy invitation (`082A`), and work reminder (`0836`). Their expanded
bounds are 317, 273, 299, 465, 774, and 109 bytes. The invitation retains choices
`0065/0045/004E` and branches `082E/082B/082C` without changing their selection
indices. Its second-page width warning remains queued for presentation review;
the importer does not reflow the reference to suppress that warning.

The complete employment-ending explanation uses
`081A → 083B → 083C → 083D`. The first two GameCube records remain complete;
the long final GameCube `083C` is split into `[0,574)` and `[579,1047)` at its
existing wait/newline/page-clear boundary after the tax-purpose aside. Expanded
bounds are 357, 466, 597, and 484 bytes. The native opening-reserve slots are
source-hash checked and have no incoming native message-script branches. The
final end remains `00`. Wages, remaining debt, weekly-payment suggestion, earning
money, post-office payments, remodelling, and the farewell remain complete.

The HRA explanation uses `082E → 2AEA`. The complete GameCube `082E` contributes
`[0,598)` and `[603,1200)`, split at its existing wait/page boundary after the
important-matters passage. Expanded bounds are 621 and 643 bytes. The train-demo
reserve is source-hash checked and has no incoming native message-script branch.
The final choices `0045/004E`, branches `082B/082C`, and end `01` remain intact.
Each reference in a mixed complete/sliced sequence contributes one complete
record or one contiguous group of fully covering slices; repeated references
outside that group, omitted text, and arbitrary separator gaps are rejected.

These Nook approvals also identify exact native supporting speaker emotions:
`0801` supplies `15`, `16`, and `FF`; `0829` supplies `17`; and `07EC` supplies
`03`. Each use lists only the required command tuples and binds the supporting
native record's hash. These are Nook's own mortgage/work dialogue contexts, not
an automatic cross-actor search. Only opcode `09`, speaker index `0000`, and an
explicit existing emotion are eligible. Actor handoffs, other demo operations,
gameplay controls, and dynamic fields are never inherited through this mechanism.

## Late-night resident introduction

The complete GameCube `04F7` is 798 encoded bytes but has a conservative expanded
bound of 1,174 bytes after reserving space for speaker/catchphrase and clock
fields. This is a build-time capacity rejection, not an observed in-game crash.
Adding page-clear commands within that same record would not lower its bound.

Use `04F7 → 083E`, replacing the existing wait/newline/page-clear span `[480,485)`
after the clock aside with one continuing-record boundary. Part one contains
reference bytes `[0,480)` plus `0E 083E`, newline, and end `01`. Part two contains
`[485,798)`, including the original final end `00`. Expanded bounds are 773 and
419 bytes. Every English text byte, manual line break, pause, clock read, and
other page boundary remains unchanged. The complete clock joke stays in part
one; part two begins the friendship exchange.

Native `083E` is a source-hash-bound opening-reserve placeholder without an
incoming message-script target. Scanning the pinned executable sections finds
no arithmetic/comparison/logical immediate `083E`; the sole aligned halfword
match in their non-executable sections belongs to the arctangent data table at
`8010F664`. This is slot-specific supporting evidence, not a general permission
to reuse seemingly empty records.

The group requires the verified resident runtime. Its existing English hour
formatter prepares AM/PM (`76`) after hour field `21`. The sequence audit allows
this derived field only when the native root supplies an hour, and requires a
preceding hour within the same replacement record. A previous record's hour
cannot satisfy that requirement. Basic builds omit the whole group; manually
requesting any member without its runtime or other members fails. All actor
argument tuples already occur in native `04F7`; no extra actor approval is used.

All sixteen sequence tests pass, including exact reconstruction of the complete
English record, both capacity bounds, runtime requirements, same-record clock
preparation, unchanged reserve identity, and rejection of partial installation.
The native batch in `build/smoke-late-intro-01/` passes both complete cartridge
loads, the `083E` continuation target, both phases of continuing/final
termination, adjacent/module guards, and checkpoint restoration: seven native
calls and fifteen assertions across forty recorded steps. It does not exercise
normal resident progression, clock insertion during rendered playback, or final
visual review. These remain in the combined gameplay/playthrough pass.

## Complete phone, furniture, and letter advice

Five further [complete reference sequences](LONG_ADVICE_SEQUENCES.md) cover
Rover's repeated phone call, three residents' furniture advice, and a cranky
resident's letter-sharing explanation. Each uses one existing English page
transition and an individually checked native reserve. Full English text remains.
The phone-mode pair stays together; the existing external `046F` continuation
remains. The letter explanation retains `75` with its following catchphrase and
requires the resident runtime. Only that verified capitalization command gains
runtime-conditional presentation treatment; unrelated controls remain guarded.

The snooty furniture reference explicitly removes redundant `74` before its
already-native item field. An individual member flag enables the established
adjacent-string-only adaptation. The unmodified full reference hash is checked
before adaptation; slice coverage applies to the complete adapted result, and
every final payload retains its own hash. All members using that reference must
agree on adaptation. Unknown commands and unavailable native fields still fail.

## Native invoice prices

The [first-renovation invoice](NOOK_RENOVATIONS.md) uses `107E → 083F` and a
separate numeric-only `native_price` approval. It retains the complete supplied
English with the native 49,800-Bell amount. The original reference hash, corrected
complete reference hash, native numeric text, fully covering slices, and each
final payload are checked. This does not relax ordinary wording or command rules.

## Original native translations

The [complete native travel sequence](NATIVE_TRAVEL_ADVICE.md) uses the same
all-or-nothing and existing-page-boundary mechanism with an explicit
`native_original` source kind. Its full original English text and hash are
stored in the approval, not borrowed from an unrelated GameCube record.
Both candidate generation and the independent builder check its complete
native command sequence, permitting only indexed colour-length corrections.
No added field, actor permission, lost pause, changed page, or altered gameplay
command is allowed. Output provenance identifies original work and draft
slices; the default GameCube source kind retains its existing rules.

## Guarded approval

A sequence record binds every original slot hash and exact approved English
encoded hash, with reference provenance and an explanation of the adaptation.
Every member must be installed together. Unknown sequences, partial installation,
changed source slots, changed translated bytes, new external branches, unapproved
actor arguments, unavailable dynamic fields, and overlong parts fail the build.

Only reviewed presentation differences are permitted. Gameplay commands remain
ordered after removing the explicitly declared internal continuation links.
Adjacent conditional-branch assignments are compared by branch opcode rather
than textual order. The original choice labels and exit mapping remain intact.
Actor-animation commands reuse argument tuples present in the source message or
the exact hash-bound supporting speaker-emotion approvals described above.
Their placement follows the approved GameCube text. Display colour spans,
page divisions, and pauses follow the approved reference exactly.

Only `09`, speaker index zero, is eligible for expression repetition/repositioning.
Every other actor request retains its complete native order and multiplicity
across the entire sequence. This includes quests, persistent mood/duration,
handoffs, and slot-nine requests. A tuple occurring in the native source is not
permission to repeat or omit that action. All existing approved groups meet this
stricter independent guard without changing their payloads.

Eleven [special-actor conversations](SPECIAL_ACTOR_SEQUENCES.md) retain complete
English Gracie, Redd, Jingle, Gulliver, Rover, and sound-setting text. Three use
existing English page boundaries and individually checked generic reserves;
the other eight remain complete single records. All expression tuples occur
in each conversation's own native source, without supporting actor approvals.

Five [contextual-expression conversations](CONTEXTUAL_ACTOR_SEQUENCES.md) retain
complete Booker, Gulliver, and Rover references. They use the same individually
hash-bound supporting-expression mechanism as Nook's job dialogue, restricted
to exact messages from each character's own native conversation context. All
five fit complete single records, preserve non-expression actions, and allocate
no continuation slots. The train name-entry request and ending remain native.

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
the built ROM. Repeated `--sequence` options batch supported groups in one
checkpoint. The home-explanation case checks all four actual cartridge loads, all three continuation
assignments, both phases of the native continuing terminator, both final branch
indices, and the native repeat response back to `07EA`. Scratch-buffer and module
guards remain intact, and the emulator checkpoint is restored after injected
calls. This test does not replace normal actor progression or presentation review.
