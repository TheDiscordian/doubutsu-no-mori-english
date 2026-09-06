# Current progress

## Active work

Complete the main translation/runtime port, then the matching GameCube image
replacements and GameCube-style keyboard. Immediate work covers the remaining
introductory dialogue, normal gameplay/save validation, unsupported text controls,
and the general-string/name/mail destinations. Candidate review remains required.
The [completion queue](WORK_QUEUE.md) tracks all required work;
partial milestones do not complete the project.

GameCube line breaks, page breaks, emphasis, and pause timing are the presentation
reference. Do not automatically reflow text to fill a bubble. Deliberate layout
polish follows translation and command handling. The reported atlas-edge defect
in `font-halfwidth.png` remains unresolved; font investigation is paused at the
user's direction. The production build retains the approved spacing metrics.

## Implemented

- Private GitHub repository, pinned reference sources, and local-only inputs.
- Verified extraction of all 3,374 retail DMA entries; checksummed UPS generation
  and application directly to the original 16 MiB ROM.
- Lossless text codec and unchanged round trips for 29 banks, including dialogue,
  choices, strings, mail components, NPC names, and fixed-width item-name groups.
- Proportional Latin rendering for 81 glyphs, at most six pixels advance. Narrow
  `i`, `I`, `l`, and apostrophe advance four pixels. Japanese glyphs are preserved.
- Relocatable dialogue and choice banks, guarded loader patches, command checks,
  source hashes, and conservative runtime expansion bounds.
- GameCube CISO/FST/RARC/Yaz0 extraction and decoding of all 16,273 main messages.
  Fixed-width GameCube item and NPC names are also extracted as local references.
- Reference import retains GameCube presentation commands and restores matching
  N64 actor-demo arguments. Read-only text insertions may differ only when the
  N64 message already supplies the requested fields. Flow commands stay ordered.
- Dialogue-only reference delivery accepts the GameCube's own page and button-wait
  layout when gameplay commands still agree. It does not reflow or remove English
  pages. Manifests record native/reference counts and retain candidate review status.
- Native formatting consumers pass colour-span, line-offset, line-anchor, and
  character/line-scale tests. The reference-layout policy retains English
  formatting with argument checks; it does not modify the font atlas or reflow.
- English-first native keyboard, translated name-entry prompts and ten texture
  labels, with the original 6/6/4/10/10 input limits and unchanged overlay sizes.
- Silent isolated ares test runner, debugger memory assertions, controller input,
  repeated scenarios, and incremental message-state recording.
- 79 passing portable-C, synthetic, and retail-input tests. Retail tests require
  the local ROM; calendar-reference checks use the local English disc extraction.
- Keyboard UI inventory identifies six embedded text entries and ten graphical
  labels, with per-entry source hashes and verified texture formats/dimensions.
- English runtime removes the Japanese town suffix and supports sixteen
  plain choice bytes, including actor-specific staging buffers. Source guards,
  complete-capability checks, and independently assembled width code pass.
  Main-dialogue runtime regressions pass; actor-specific runtime tests remain.
- Resident twenty-byte choice capacity imports the thirteen longer reference
  choices without truncation. Native MIPS tests pass real DMA loading, all four
  rows, width calculation, overflow rejection, selection, insertion, and guards.
  Actor frames grow by forty bytes with their saved values and arguments adjusted.
- Reviewed multi-message reference sequences retain GameCube record boundaries
  within the native message buffer. Nook's house explanation uses four approved,
  hash-bound records. Partial installation, stale placeholders, incoming native
  script branches, altered gameplay controls, and changed payloads are rejected.
  Nook's work offer also has a reviewed split at an existing English page boundary;
  complete reference coverage and the native final terminator are checked.
  The purchase confirmation has a one-record approval preserving its small-print
  radio aside, repeated native emotions, and unchanged outgoing explanation link.
- Experimental resident runtime module with a verified new DMA entry, sixteen-KiB
  heap reservation, preserved watchdog, source/build guards, and linker bounds.
  Four-MiB boot and the complete train-to-town regression pass with intact guards.
- Seven English message date/time substitutions, including full month/weekday
  names, ordinal days, twelve-hour time, and zero-padded minutes/seconds. Portable
  exhaustive tests and native MIPS insertion calls pass. Other UI callers remain.
- GameCube AM/PM insertion, one-shot capitalization, and protected text pacing
  in the resident module. Targeted MIPS tests verify the latched meridiem,
  unchanged source strings, flag consumption, B-button/cancel gating, timer
  behaviour, and retained explicit pauses. Unsupported extension codes stay
  rejected. Whole-game command and actor coverage remains incomplete.
- GameCube choice cancellation (`62`), including native B-to-last selection,
  closing-sound decisions, duplicate-sound suppression, and flag resets. Targeted
  MIPS tests pass without host audio output. Four inventory prompts become
  candidates; storage/music menus with changed actions remain withheld.

## Current reference candidates

The generated pilot contains 9,127 edits. These are candidates, not a claim of
reviewed translation coverage. Accepted reference imports comprise 8,301 dialogue
entries, 446 choices, and 376 string/mail-component entries, plus four original
introductory drafts. Three draft IDs override reference selection.

Main dialogue still has 3,448 rejected entries. Principal reasons are unconfirmed
same-ID matching (1,854), flow/control mismatches (1,251), new text fields (143),
unsupported GameCube commands, and two expansion-bound failures. Another 996
accepted dialogue candidates have conservative layout warnings. Entry-level
rejection and adaptation reports are generated in `build/candidates/`.

Thirteen English reference choices exceed sixteen bytes and one lacks the
same-ID legacy match.
Those fourteen remain withheld. General strings, mail, saved names, dates, and
item names have separate restrictions. Unsafe legacy item-name mappings are withheld.

## Validation and release status

The separate resident-module experiment contains 9,944 edits, including
9,100 reference dialogue candidates, all 460 choices, and four N64-specific
exercise drafts alongside the three remaining introductory drafts. It retains the GameCube calendar wording in Rover's
opening question and admits reference capitalization and protected-pacing spans.
Its remaining main-dialogue count is 2,646; matching, actor fields, flow controls,
and review are still required. This experimental count does not replace the
ordinary pilot's coverage or establish translation completion.
The final choice identity is individually reviewed and hash-bound; complete
choice translation review and actor-runtime coverage still remain. The twenty-byte
build passes the complete train-to-town regression. Separate pacing-build gameplay
continues through Nook's escort, house entry, and the home-gyroid explanation.
Nook's introductory work offer also completes. The gyroid remains in its job-time
state and does not expose the normal save menu yet. A separate native test passes
all house-explanation loads, continuation links, both choice branches, the repeat
response, and memory guards. Normal actor traversal reaches all four English
records and the active final choice. Choosing repeat traverses all four records
again; choosing continue reaches the invoice and the native work-offer entry.
The sequence build passes name/town entry and a continuation to
arrival. The cancellation build passes the complete long-choice/train-to-town
regression and all ten acceptance checks, as does the delivery build. Its 366
page-delivery candidates still need broader gameplay review. The work-offer split
passes native DMA, continuation, final-termination, and guard tests; normal actor
progression through the English work-offer split remains open. The work-offer build
also passes all 225 full train-to-town steps and ten acceptance checks. The layout
build adds 264 formatting candidates with 1,308 total conservative layout warnings;
its broader gameplay regression remains open. The purchase build adds one guarded
record and has 1,309 total conservative layout warnings. The native formatting test passes
385 recorded steps without modifying the font assets.
The exercise drafts retain every native command; seasonal-event testing remains.
The [general-string audit](../specs/GENERAL_STRINGS.md) identifies thirty-four
direct loader calls and their destination constraints; wider imports remain gated.

Silent emulator runs confirm a four-MiB configuration, active relocated text
loaders, intro dialogue, English-first input, case conversion, single-character
deletion, cursor movement, six-character enforcement, all five mode transitions,
and successful name confirmation. The proportional name-cursor correction passes
the same regression and has been visually checked during entry. Destination-name
entry, its six-character limit, and confirmation also pass. A 218-step run reaches
town arrival and verifies long choices, selected text, and the English town field.
No hardware-certified build or
release candidate exists. Save/reload, travel, mail, board, RTC, calendar, credits,
seasonal events, and original hardware tests remain outstanding.

The runtime changes the town insertion command `7F2F`; recorded message assertions
confirm the supplied town name appears without the Japanese village suffix.
Catchphrase, song, mail, and board editor callers also need their own regressions.

The GameCube-style grid is a separate implementation task; the current keyboard
still uses the N64 radial layout. See [keyboard design](../specs/KEYBOARD.md),
[validation](VALIDATION.md), and [build instructions](BUILDING.md).

Public release requires completed translation review, stability testing,
original-hardware results, and third-party provenance review. Only patches and
original tooling may be published; ROMs and extracted assets stay local.
