# Current progress

## Active work

Complete the main translation/runtime port, then the matching GameCube image
replacements and GameCube-style keyboard. Immediate work covers broader missing
dialogue, normal gameplay/save validation, unsupported text controls,
and the general-string/name/mail destinations. Candidate review remains required.
The [completion queue](WORK_QUEUE.md) tracks all required work;
partial milestones do not complete the project.

Prioritise bulk English coverage and complete playable sections, batching useful
crash/save/text checks across changes. Difficult isolated edge cases stay in the
follow-up queue. A human playthrough drives the broad gameplay bug and polish
pass after the main port; planned human testing is not completed validation.

Pelly's receipt-failure patch returns rejected letters to their original pockets
and selects accurate English errors. Native tests pass 48 receipt cases, eight
hand-back initializer cases, sixteen refusal selectors, and ten index boundaries.
The tests use the actual action initializers and cover both reason-indexed
message lookups. Normal animation, subsequent input, and rendered error
progression remain unverified. Follow-up mail work covers those interactions
and remaining readers/metadata before generation. Read-only letter headers
resolve complete English villager names without changing saved identities.
All 216 names pass host checks; eight native letter windows pass complete text,
page, glyph, source-retention, and preference checks. The ordinary-header native
regression also passes ten header cases, body/footer rendering, and non-read
mode forwarding across 1,010 recorded steps.
The three native NPC letter-show paths also pass nine complete isolated window
cases, including unknown sender handling. No additional production patch is
needed for these callers. Normal actor interactions, post-office progression,
remaining inline readers/metadata, and ordinary save-menu/post-load gameplay remain.
The isolated native FlashRAM round trip passes all 192 stored letter slots in
both save banks. A separate fresh process reads only the cartridge save and
reconstructs complete English letters from both formats and both record layouts.
This does not establish normal saving, edited-letter persistence, or hardware
compatibility. See [persistence scope](../specs/FLASH_MAIL.md).
Isolated native Controller Pak writing and fresh-process reading also pass the
17 passport letter slots and all 160 stored-letter slots. Complete files,
checksums, player/NPC imports, and English reconstruction pass without changing
the live save payload. The ordinary station-travel and storage-menu flows remain
unverified. See [Pak persistence scope](../specs/PAK_MAIL.md).
The original letter-menu selector passes 120 isolated status/gift/marker/context
cases with unchanged complete letters. All 44 static menu-label definitions pass
native length calls; that shared text helper is not a snapshot reader. Received
letters select Read, while player-written drafts select Rewrite. Normal UI
transitions, generated status assignments, and custom editing remain separate
requirements. See [menu evidence](../specs/MAIL_MENU.md).
The isolated whole-letter generation API passes all 6,398 supported host
reference assembly cases. Native calls pass 46 complete English reference cases,
seven rejected generations, and 42 capture cases, with complete save retention
and intact guards. Publication changes only validated text/split bytes and the
transient capital state. The 1,380-byte generation probe is separate from the
resident image, which has 1,856 linked bytes free. NPC resident allocation and
on-demand loading are implemented; delivery integration tests and semantic
template approval remain. Default builds leave snapshot generation disabled;
an explicit experimental option installs NPC generation. See
[generation contract](../specs/MAIL_GENERATION.md) and
[receipt evidence](../specs/PELLY_RECEIPT.md).
The [NPC creator binding audit](../specs/NPC_MAIL_GENERATION.md) checks seven
native functions, six native tables, and corresponding English executable
evidence. All 24 composite group/gift contexts and 36 classic reply selections
use supplied source slots; composite footer `psz:004D` remains unavailable.
The native caller ignores assembly failure. A source-guarded submission gate
passes 41 isolated native cases using actual receipt/copy/capacity routines and
a controlled creator fixture. Twenty cases deliver complete records into the
native queue; rejected cases retain all save data and never use older staging
text. The gate is connected to the cartridge creator in the optional experimental
build. Real creator-to-receipt and pending-loop validation remain follow-up work.
The separate [NPC reply-word resource](../specs/NPC_MAIL_WORDS.md) contains all
352 complete phrases with exact legacy/English agreement and explicit native
ID mappings. Eighty-three need more than the native ten bytes; all fit sixteen.
The resource is connected to scoped capture and the optional cartridge creator.
The [saved-name alias resource](../specs/NPC_MAIL_NAMES.md) recovers full English
names for all 216 villagers from 394 exact known saved-name keys. It rejects
ambiguous mappings and leaves unknown names unresolved. Complete native lookup
and generation-time capture are implemented and optionally installed.
The reader releases its 3,552-byte decode workspace immediately after opening
a snapshot. Its complete 2,236-byte display cache remains resident; the 32 KiB
reservation and heap boundary are unchanged. Host allocation/error tests, the
four-MiB train-to-town run, and all eight native letter windows pass. Independent
module, ROM, and patch builds match.
The [scoped capture implementation](../specs/NPC_MAIL_CAPTURE.md) retains full
English source values beside the original native preparation calls. Host tests
cover all 352 phrases and 394 saved-name aliases, ordered capture, unchanged
native temporary fields, and failure rejection. The relocatable code builds with
the existing VR4300 toolchain; the resident image uses 22,720 linked bytes.
The new module passes the four-MiB train-to-town regression, and independent
module, ROM, and patch builds match. All 48 native creator comparisons pass,
including complete English generation, unchanged random state and native fields,
all six personalities, both reply types/origins, thirteen retained gifts, and
complete save retention. The 197-call run also checks source validation, native
relocation/cache maintenance, guards, and checkpoint restoration. Ordinary
delivery remains a follow-up integration check. The
[whole-creator transaction](../specs/NPC_MAIL_CREATOR.md) now stages complete native
metadata and English text and publishes all 164 bytes only after validation.
It resets stale capture, rejects nested/intersecting requests, detaches its
session, and retains caller text/capitalization on failure. Host sanitizer checks
pass. The native transaction passes 48 reply comparisons, eight successive
letters, and six rejected requests, with 163 calls and 898 assertions. Complete
save retention, shared capitalization, scope cleanup, and checkpoint restoration
pass. The [resident loader](../specs/NPC_MAIL_LOADER.md) passes 56 complete native
cartridge-created letters and eight failures, with no debugger-uploaded creator
code/resources. Whole-letter reconstruction, original metadata/RNG, shared
capitalization, heap release, full save retention, and checkpoint restoration
pass. The optional generation ROM also passes all ten four-MiB train-to-town
checks. Independent module and creator builds match. Thirteen loader/installer
tests and the seven loader sanitizer tests pass. The complete 389-test regression
suite passes, including the rebuilt module-bound generation probe. Main work covers missing dialogue and
normal-play coverage; remaining delivery and edge cases are tracked for batching.
All eight letter windows pass the capture-module regression across fourteen pages, including
1,705 glyphs and 6,820 vertex positions. The tested failure gate
provides the required return boundary; it does not replace source or semantic
review, normal reader/editor interactions, or save/hardware acceptance.

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
- 389 passing portable-C, synthetic, and retail-input tests. Retail tests require
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
- Experimental resident runtime module with a verified new DMA entry, 32 KiB
  heap reservation, preserved watchdog, source/build guards, and linker bounds.
  Four-MiB boot and the complete train-to-town regression pass with intact guards,
  including the actual malloc arena start. The observed-arrival scenario passes
  188 recorded steps and all ten acceptance checks on the mail-view build.
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
  cover assembly, free strings, the separate gyroid/demo message setter,
  clearing, and copying; eight bank-size
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
  The codec is linked into the resident module and passes isolated N64 CPU calls.
  Record discrimination, full-text reader integration, custom editing, and save
  integration remain.
- The native mail-viewer audit verifies the board object's complete layout,
  field scans, read-mode branch, header-split clamp, and six-line/sixteen-character
  body limits against the actual overlay. It also distinguishes the read-wait
  handler and pointer-clearing destructor from the edit-acceptance path that
  copies mail and header/footer preferences back into persistent destinations.
  Shared callbacks and opening callers remain under review. Full-text viewer
  integration must decode before native normalization and preserve GameCube
  newline/width intent.
- Full-letter assembly in Python and resident C preserves complete template
  wording, explicit line breaks, header-name placement, and captured substitutions
  and articles. Thirteen actual English executable routines are hash-guarded;
  the supplied GameCube release's sticky capitalization is captured in snapshot
  version two, so rereading a letter cannot change its case. Python, C, and an
  independent in-place reference model agree on 6,398 retail-template probes,
  all field/length/article/state combinations, malformed input, and guarded
  output tests. The reference preparation tool converts 4,807 of 4,866 mail
  parts; 59 require glyph support and remain rejected. Two probes of classic
  `0001` still require actual source-width evidence. Both C files cross-compile
  for VR4300 with no undefined symbols or mutable globals. All 287 native
  command/copy calls also pass with version-two envelopes and captured capital
  state; the machine checkpoint is restored. The installed codec passes 215
  N64 CPU calls and 303 memory assertions; the formatter passes 350 calls and
  544 assertions, including every opcode and complete output. A separate run
  passes 92 calls and 280 assertions for 46 English reference cases. Linked code
  and display state occupy 22,720 bytes within a 32 KiB reservation, with a separate 8 KiB test
  area and intact stack guards. Catalog identity review, generation/viewer hooks,
  editing, and normal save validation remain. Optional NPC generation emits
  complete snapshots, and the full reader calls restoration for tagged records.
- An immutable cartridge mail catalog contains 4,807 complete reference parts
  with all 4,866 original indices preserved; 59 unavailable glyph rows remain
  explicit failures. Its 319,344-byte content is registered by complete hashes.
  The restoration API connects snapshot decoding, actual cartridge reads, and
  full-letter assembly without changing the saved record or publishing partial
  output. Host execution agrees on all 6,398 reference probes. Targeted N64 CPU
  tests pass 84 calls and 259 assertions, including 46 English reference cases,
  disabled resources, malformed headers, and guards. Catalog identities are
  immutable storage identities, not native semantic-match approvals. Generation,
  record discrimination, the full-text viewer/editor, and saving remain.
- Optional read-only mail body/footer hooks use actual pixel widths and retain
  explicit newlines, spaces, six-line geometry, and the approved font. Only two
  draw calls and their obsolete relocations change; editor modes tail-call the
  unchanged native routines. Host tests and 22 N64 CPU calls pass, including all
  264 vertex-position assertions for 66 rendered glyphs, graphics/stack guards,
  and argument forwarding. An isolated synthetic letter opens through the actual
  submenu loader, verifies execution at both installed hooks, and closes with A,
  B, and START with unchanged source mail and saved header/footer preferences.
  The complete train-to-town regression
  also passes. These hooks still read native 96/16-byte fields; snapshot decoding,
  longer generated letters, pagination where required, and editing remain.
  See [mail reader design](../specs/MAIL_VIEW.md).
- The separately enabled full snapshot reader decodes before native scans and
  normalization, preserving the source letter and clearing only its temporary
  display copy. A bounded resident cache holds full text, recipient placement,
  and complete pages. Explicit newlines/spaces remain; long bodies and signatures
  continue without truncation. Left/Right changes pages; A/B/START retain closing.
  Corrupt snapshots show an English error. Generated snapshots cannot enter the
  lossy native editor. Host tests pass, and four long classic/composite reference
  letters and two rejected snapshots pass actual window drawing across ten
  pages, including 1,134 glyphs and 4,536 vertex coordinates. An edit-open request
  safely becomes read-only. Ordinary letter opening/closing, ordinary header
  drawing, and non-read forwarding regressions also pass. The experimental split marker is not a released
  save format: generation, all other readers, editing, delivery, and persistence
  remain. See [full reader design](../specs/MAIL_READER.md).
- Home-gyroid owner-message display uses GameCube-style measured wrapping in
  its unchanged sixty-eight-byte temporary field. Explicit newlines and spaces
  remain, the original sixty-four-byte saved/editor limit is unchanged, and
  overlapping source/destination is safe. Three thousand host cases match the
  pinned English formatter with the native capacity. Native tests pass 47 calls
  and 165 assertions, including real dialogue insertion at the exact message
  limit, source preservation, and stack/module guards. The new build passes
  train-to-town and the complete snapshot-reader and ordinary-layout regressions.
  Ordinary other-owner interaction, the longer English default, and wider custom
  storage/editing remain. The audit distinguishes this routine from actual
  stored-letter consumers; the separate NPC reply and letter-quest grading paths
  use the complete-record integration below. See [gyroid display](../specs/GYROID_MESSAGE.md)
  and [NPC letter readers](../specs/MAIL_NPC.md).
- Optional English ordinary-letter grading uses the GameCube's seven-rule
  scorer, with bounded English prefix tables in the original on-demand overlay
  allocation. The distinct native letter-quest length/rate path is retained.
  All 776 prefixes, 3,000 independent GameCube C comparisons, exact rank
  boundaries, sanitizer checks through 1,024 bytes, and installer/relocation
  rejection tests pass. Native tests pass 91 calls and 157 assertions, including
  actual cartridge loading, quest gifts/ranks, and local reply flags. The
  combined build passes train-to-town and all six complete-letter reader probes.
  Native ordinary bodies remain ninety-six bytes; the combined snapshot build
  connects complete decoded bodies through the send integration below.
  Generation, normal delivery, and saving remain. See [English grading](../specs/MAIL_GRADING.md).
- Whole-record NPC sending decodes tagged letters before native mutation and
  supplies distinct complete-body ordinary/quest grades through an exact-pointer
  context. Ordinary records retain native handling. Local and visiting-player
  reply flags, dates, friendship, gifts, and quest updates execute their original
  code. A guarded post-office result hook preserves failed letters and counters
  instead of discarding rejected snapshots. All 6,398 host reference cases pass;
  the N64 integration passes thirty-two controlled send cases, eighty native
  calls, and 313 assertions across 649 steps. Source records, unrelated NPC/player
  state, allocation ownership, nested contexts, and memory guards are checked.
  The combined build passes all 188 train-to-town steps and ten acceptance checks.
  Its full-letter reader regression passes all six windows and ten pages, with
  1,134 glyphs and 4,536 vertex positions checked.
  These tests restore isolated checkpoints; normal Pelly interaction, actual
  saving, complete metadata handling, semantic approvals, generation, and lossless
  editing remain. See [complete-letter sending](../specs/MAIL_NPC_SEND.md).
- Selected metadata and storage paths pass 140 isolated N64 cases, 217 native
  calls, and 267 assertions. Snapshot markers do not affect slot/send/gift
  predicates. Both record kinds retain complete contents through NPC conversion,
  both leaflet slots, all five post-office queue positions, and all ten slots
  in each of four home mailboxes. Full-storage failures retain their source;
  leaflet flags, neighbouring memory, and guards pass. The arrays and full
  checkpoint are restored. These checks do not establish ordinary delivery or
  save/reload; the actor-specific checks are described separately below.
- Pelly/Phyllis receipt failures use the native pocket-return flow and two new
  original English errors without changing any existing message or its pacing.
  Forty-eight native receipt cases pass, covering both record kinds, both
  sisters, successful delivery, and rejection across every player pocket.
  Eight hand-back initializer cases, sixteen refusal selectors, ten index
  boundaries, and 152 complete loaded-message checks pass. The native loader's
  complete relocated overlay, 407 function calls, 760 memory assertions, and
  2,084 recorded steps pass with checkpoint restoration and blank FlashRAM.
  The fixture runs actual action initializers but does not run the normal
  hand-back animation. The build also passes the 188-step town regression and
  all ten acceptance checks; independent module, ROM, and patch builds match.
- Read-only ordinary and snapshot letter headers resolve complete eight-byte
  English villager names from native saved identities. All 216 villagers pass
  host tests; player names, unsupported identities, disabled/bad resources, and
  suppressed-name header types retain their intended fallback behaviour.
  Native windows pass eight letters across fourteen pages, checking 1,705
  glyphs, 6,820 vertex positions, and all source/preference guards. Two probes
  use the original native NPC identity setter. The cache occupies 2,236 bytes;
  decode scratch is allocated only during restoration and freed before drawing;
  saved names, source records, font metrics, and reference layout are unchanged.
  The ordinary-header regression passes ten cases, body/footer glyph checks,
  and all non-read-mode forwarding checks: 36 calls and 842 memory assertions
  across 1,010 steps, with checkpoint restoration and blank FlashRAM.
  The 188-step town regression and all ten acceptance checks pass. Ordinary
  gameplay, save/reload, and hardware remain.
- All three direct NPC stored-letter show paths pass isolated native execution:
  first-job, ordinary known-sender, and ordinary unknown-sender. Nine windows
  cover ordinary letters and both snapshot kinds; six snapshot windows verify
  twelve pages, 1,713 glyphs, and 6,852 vertex positions. The 510-step run passes
  45 native calls and 151 assertions, checking complete native overlay relocation,
  zeroed BSS, source retention, unchanged player/NPC data during calls, and safe
  allocation lifetime through window close. Ordinary windows reach all three
  draw hooks with complete retained records and expected text lengths. All
  allocations are freed after close; checkpoint restoration and blank FlashRAM
  pass. No production change to these callers is needed. Normal actor gameplay,
  inline/computed-pointer readers, travel, editing, and normal saving remain.
- Native FlashRAM persistence passes with synthetic classic/composite snapshots
  in all 192 saved mail slots: forty player pockets, forty home-mailbox slots,
  five post-office records, two leaflets, and 105 NPC compact letters. The
  original asynchronous save pipeline writes and verifies both complete banks.
  A separate fresh emulator process receives only that cartridge save, verifies
  both native reads/checksums/town identities and all 384 complete stored
  records, and reconstructs full English output in eight native decoder calls.
  Memory guards, restored checkpoints, and graceful shutdown pass. The writer
  requires an entirely blank isolated chip and explicit opt-in; existing user
  saves are untouched. This is not ordinary save-menu/post-load gameplay,
  custom editing, travel, or original-hardware validation. No production code,
  saved record size, font, candidate translation, or generation setting changes.

## Current reference candidates

The current experimental resident-module pilot in `build/shop-menu-pilot/`
contains 10,441 edits, including
9,186 reference dialogue candidates, all 460 choices, and ten original dialogue
drafts. Two additional original Pelly/Phyllis error messages extend the main bank
to 11,754 records; they do not change the existing candidate counts. Candidates
still require review. The original main-bank audit leaves 2,556
records without candidates; the classification and remaining restrictions are
listed below. The 1,365 conservative layout warnings include full default
catchphrase width and do not trigger automatic
reflow. Detailed candidate, rejection, and coverage reports remain local in
`build/shop-menu-candidates/` and `build/shop-menu-coverage/`. The independent
mail control gate withholds `mailb:00BB` until native mail supports its
capitalization command. Layout warnings account for the wider catchphrase display.

All functional records in Nook's introductory range `07E0..083D` have English
candidates. Fourteen added records close ten functional gaps and provide four
reserved continuation slots. The complete job-ending speech and HRA explanation
retain GameCube wording, manual layout, and pauses, splitting only at existing
page transitions. The map handoff names the native R button. The short debt
insistence uses an original translation with all native commands unchanged.
Only the opening-reserve placeholders `083E/083F` lack candidates in this range.
All fourteen complete cartridge message loads pass in one fresh four-MiB run,
including buffer/module guards and checkpoint restoration. Ordinary job
traversal, HRA choices, and the HRA invitation's line-width warning remain queued
for the combined gameplay and human bug/polish passes. Existing candidates,
font assets/metrics, and saved structures are unchanged by this batch.

Twenty-two shop-service, sale, order, and disposal messages retain complete
English wording with the original native choice IDs and selection order.
Individually source/reference/payload-bound choice approvals prevent accidental
import of GameCube menu actions. Native choice `0009` has an original
fourteen-byte translation, `Turnip prices?`, replacing the incompatible GameCube
Other things label. All 460 native choices still have candidates: 459 supplied
reference labels and this original draft. The twins' `172A/1737` remain withheld
for their separate speaker/echo differences. All 22 complete messages and six
referenced choice labels pass native cartridge loads with buffer/module guards
and checkpoint restoration. The 32-test reference batch passes, including four
new native-choice tests. See [native choice contract](../specs/REFERENCE_CHOICES.md).
Ordinary selection, selling/ordering, echo rendering, and line-width warnings
remain gameplay and human-playthrough checks.

General strings, mail, saved names, dates, and item names have separate caller
restrictions. The independent wider item, display-name, catchphrase, and mail-catalog resources are not
additional ordinary-bank edits, and an API resource does not imply that every
gameplay destination uses its wider names.

## Validation and release status

The resident-module experiment contains 10,441 edits, including
9,186 reference dialogue candidates, all 460 choices, 178 villager names,
231 item-name slots, four N64-specific exercise drafts, two greeting-job drafts,
and four other introductory drafts. It retains the GameCube calendar wording in Rover's
opening question and admits reference capitalization and protected-pacing spans.
Its reference generator rejects 2,557 main records; one receives an original
fallback draft. The final candidate-file audit finds 2,556 main records without
candidates: 1,625 with Japanese text, nine exact placeholders, 919 with no static
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
