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
- 191 passing portable-C, synthetic, and retail-input tests. Retail tests require
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
- GameCube pixel-space (`67`) through both message cursor and sentence renderer.
  Native tests verify scaled width, complete token advancement, missing-argument
  handling, unchanged native formatting handlers, and memory guards.
- 178 complete English villager-name candidates within the unchanged six-byte
  native fields. All 216 names have confirmed reference identities; 38 longer
  names remain withheld for wider-name work. All native name loads and their
  adjacent guards pass, including the no-write invalid-ID path.
- Legacy item references recovered from the shipped loader's verified tables.
  All seventeen banks reconstruct unchanged, and 947 furniture groups map to
  their four native rotation slots. These are references, not approved imports.
- 107 distinct reference IDs for complete English item-name candidates in 231 native storage
  slots, retaining GameCube spelling/case and the original ten-byte fields.
  Thirty-five direct item-loader calls and their contexts are inventoried.
  Wider imports remain gated on name, message, handbill, and UI destinations.
- Standalone sixteen-byte item-name API and separately configured DMA resource.
  All sixteen-bit item IDs pass portable index/conversion/guard tests. Native
  DMA tests cover every confirmed reference identity, group boundaries, invalid
  inputs, unaligned destinations, resource disabling, and header validation.
  The resource has 282 candidate reference IDs in 649 slots. This API alone does
  not enable wider names at a destination. A verified placed-clothing alias fills
  its ordinary-name destination; direct loading and all four rotations pass.
- Sixteen-byte main-message item fields with unchanged native structure/save
  layout. All five rows retain complete values, clear shorter replacements,
  and reject overflows. The message insertion hook and item-ID wrapper pass
  429 native calls and 1,634 recorded steps, including capitalization, real DMA,
  disabled-resource fallback, exact message limits, and memory guards. The
  wrapper's five identified callers are integrated; other direct item loaders,
  free-string fields, handbills, and dynamic-choice insertion remain gated.
  The full train-to-town regression passes all 225 steps and ten acceptance checks.
- Hash-bound controller-text adaptations preserve the English reference except
  for individually approved button spans. Nook's clothing reminder uses START
  instead of GameCube Y, as does the unfinished-planting reminder. The highlighted
  span lengths are corrected and all
  surrounding GameCube layout/timing preserved. Portable and native DMA/end
  tests pass; ordinary gameplay of the adapted reminders remains.
- Token-aware coverage classification for all 29 native banks. Command-only
  records, exact placeholder labels, visible kana, Latin text, unknown glyphs,
  and candidate presence stay distinct. Source hashes and unique IDs are checked;
  candidate presence never implies review or unreachable code.
- Complete-native-record alias matching adds 41 unambiguous dialogue candidates.
  Source/reference hashes, the entire adapted output, and normal command/capacity
  checks are retained. Seventy-nine conflicting groups remain withheld; drafts,
  special approvals, and sequence permissions do not transfer automatically.
  All 41 native DMA loads pass full-content and adjacent-guard checks.
- The planting-job acknowledgement has a one-record, hash-bound GameCube
  approval retaining its repeated native emotions, full text, and continuing
  terminator. Two N64-specific greeting-job drafts avoid the GameCube-only
  mayor/wishing-well instructions and retain every native control and pause.
  Native loading tests pass; English ordinary actor traversal remains.
- Read-only village records expose home coordinates and recorded NPC positions
  for normal navigation, without changing greetings, schedules, or progression.
- A separate eight-byte display-name resource contains all 216 confirmed villager
  names and 64 special-actor rows covering 23 distinct names. All native ID and
  real-DMA row tests pass, including unaligned destinations, rejected inputs,
  disabled resources, malformed-header checks, and adjacent/module guards.
  Two nameplate consumers and the main-dialogue insertion now use the complete
  names. Native consumer tests cover full output, centering, stack guards, exact
  message limits, capitalization dispatch, and all eight rendered character quads.
  The combined build passes all 225 train-to-town steps and ten acceptance checks. Shared
  choice insertion and saved-name consumers retain six-byte formats.
- Injected native tests now require the verified graph-thread frame boundary.
  Arbitrary idle-thread injection can block the scheduler's idle fallback and
  caused a display-name test stop. The guarded-context run passes all 1,204 steps;
  The previously failing 451-case item batch also passes in this context;
  attribution of that older failure remains qualified by its missing register log.
  Read-only live NPC actor observations support outdoor navigation.
- Bounded controller navigation approaches a moving NPC from observed actor and
  player coordinates, without position, schedule, or greeting writes. It stops
  when dialogue opens, a target disappears, the route stalls, or its step limit
  is reached. Normal gameplay completes Cousteau's English introduction at `04E7`.
  The bounded page-advance helper stops at a closed conversation or active choice,
  without reopening a conversation. This older checkpoint still has native
  catchphrase text; ordinary conversations on the new catchphrase build remain.
- A separate ten-byte default-catchphrase resource covers all 216 confirmed
  villagers using the actual native/GameCube default tables and legacy agreement.
  Display lookup preserves four-byte saved/custom text and distinguishes a
  villager's own default from an unambiguous borrowed default. One ambiguous
  borrowed key remains native. Portable tests cover every default on every
  villager. Native tests pass 261 calls, 501 memory assertions, and 1,505 steps,
  including actual capitalization dispatch, exact message limits, unchanged
  saved bytes, resource disabling, and checkpoint restoration. The new build
  also passes all 225 train-to-town steps, ten acceptance checks, the eight-byte
  nameplate consumer regression, and the 429-call item-field regression.
  Shared choices, ten-character custom editing, mail, save/reload, and hardware
  remain separate work.
- Exact debugger reads account for one-, two-, four-, and eight-byte access
  alignment, including cached reads. Writes preserve neighbouring bytes.
  Incremental result files are atomically replaced for concurrent observers.
- The mail audit verifies the 164-byte native record and contiguous 10/96/16-byte
  header/body/footer fields against actual instructions. Ten routine inventories
  cover assembly, free strings, excerpts, clearing, and copying; eight bank-size
  reports distinguish shared numeric IDs from GameCube-only records. Complete
  command-table validation rejects unsupported mail opcodes independently of
  main-dialogue capabilities, preventing unsupported-token conversion stalls.
  This withholds one previously accepted composite-mail candidate. Complete
  English mail still requires a lossless storage/display/editor design and
  delivery/save validation. See [mail requirements](../specs/MAIL.md).
- A lossless generated-mail snapshot prototype stores immutable template IDs,
  exact literal substitutions, article choices, and a checksum within the native
  122-byte text area. Python and freestanding C codecs agree, reject malformed
  inputs without partial writes, and preserve full-width fields. Every possible
  field union in the twelve native composite-reply groups fits; 981 of 982
  classic English records fit the conservative sixteen-byte field bound, with
  the remaining record requiring actual source bounds. All 287 native command/
  copy calls pass, including complete ordinary/villager mail record copying.
  The codec is not installed in the resident module. Record discrimination,
  full-text assembly/readers, custom editing, and save integration remain.
- The native mail-viewer audit verifies the board object's complete layout,
  field scans, read-mode branch, header-split clamp, and six-line/sixteen-character
  body limits against the actual overlay. Full-text viewer integration must
  decode before native normalization and preserve GameCube newline/width intent.

## Current reference candidates

The current experimental resident-module pilot contains 10,405 edits, including
9,151 reference dialogue candidates, all 460 choices, and nine original dialogue
drafts. Candidates still require review. Its final main-bank audit leaves 2,592
records without candidates; the classification and remaining restrictions are
listed below. The 1,353 conservative layout warnings include full default
catchphrase width and do not trigger automatic
reflow. Detailed candidate, rejection, and coverage reports remain local in
`build/mail-audit-candidates/` and `build/intro-jobs-coverage/`. The independent
mail control gate withholds `mailb:00BB` until native mail supports its
capitalization command. Main-dialogue candidates are unchanged; layout warnings
account for the wider catchphrase display.

General strings, mail, saved names, dates, and item names have separate caller
restrictions. The independent wider item, display-name, and catchphrase resources are not
additional ordinary-bank edits, and an API resource does not imply that every
gameplay destination uses its wider names.

## Validation and release status

The separate resident-module experiment contains 10,405 edits, including
9,151 reference dialogue candidates, all 460 choices, 178 villager names,
231 item-name slots, four N64-specific exercise drafts, two greeting-job drafts,
and the three remaining introductory drafts. It retains the GameCube calendar wording in Rover's
opening question and admits reference capitalization and protected-pacing spans.
Its reference generator rejects 2,593 main records; one receives an original
fallback draft. The final candidate-file audit finds 2,592 main records without
candidates: 1,661 with Japanese text, nine exact placeholders, 919 with no static
text, one with Latin text, and two with only numbers/symbols. Ten command-only
records contain dynamic insertions. All 919 retain their control-flow review
requirement; none is deemed unreachable from this classification.
Matching, actor fields, flow controls,
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
passes native DMA, continuation, final-termination, and guard tests. Normal actor
progression also traverses `07EC` and `2AE9`, finishes the English work offer,
and returns control to the player. The work-offer build
also passes all 225 full train-to-town steps and ten acceptance checks. The layout
build adds 264 formatting candidates with 1,308 total conservative layout warnings;
the layout build also passes the complete train-to-town regression and all ten
acceptance checks. The space build has 1,310 total conservative layout warnings.
Its native formatting/space test passes 476 recorded steps without modifying the
font assets. The space build also passes the full train-to-town regression, the
twenty-byte-choice regression, and cancellation tests. Six additional reviewed
identities use identical native shop/reward records at confirmed reference IDs;
their caller-specific gameplay review remains open. The name build passes all 216
real cartridge name loads and the invalid-ID no-write check, with 660 recorded
steps. Native name storage, identity structures, and file size stay unchanged.
The item build has passing runs covering all 4,547 native item-ID cases across
nine bounded scenarios, including every ordinary item, furniture rotation,
placed-item conversion, and empty/unsupported type. The final batch's first
attempt stopped unexpectedly at its first injected call; its complete rerun
passes, but that unexplained failure remains open for repeatability work.
Normal gameplay on the space build traverses
the English purchase confirmation and all four home-explanation records.
The exercise drafts retain every native command; seasonal-event testing remains.
Normal gameplay also enters Nook's shop and reaches the English uniform handoff.
The uniform is equipped through the inventory, acknowledged by Nook, and confirmed
by the native clothing item ID. The English planting-job instructions complete.
All seven supplied flowers and three saplings are planted through normal
inventory actions, with native pocket consumption checked after each item in
the final batches. Nook acknowledges the completed work at `07F9`, then requests
introductions at `0821`; `0822` reminds the player that villagers remain unmet.
The English versions of these three records pass native DMA tests, but their
ordinary actor traversal remains. The greeting break and later jobs are active.
The message-alias build passes all 225 train-to-town steps and all ten acceptance
checks. Native draft loading covers all nine current original dialogue drafts.
The following clothing reminder has an approved GameCube Y-to-N64-START button
adaptation in the controller build. Read-only player coordinates support navigation
without position edits. START opens the inventory during the normal shop test.
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
