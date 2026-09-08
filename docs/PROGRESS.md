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
  N64 message already supplies the requested fields or an individually hash-bound
  current-player/current-town or resident-speaker approval establishes the added fields. Flow commands
  stay ordered; actor-prepared fields retain their original restrictions.
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
- 671 passing portable-C, synthetic, and retail-input full-suite regression tests,
  including the repeatable text-volume report.
  The suite includes all eleven item-identity/scenario-composition checks and
  five cartridge-clock/town-data error checks, and eleven native-mood reference checks.
  Retail tests require
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
- Ordinary resident year/month/day preparation uses English in the unchanged
  ten-byte free fields. Native lunar conversion is retained, including the leap
  month branch. All 53 format preparations, thirteen conversions, six complete
  festival-message loads, and eight date insertions pass native checks. Other
  actors, birthday item fields, and out-of-table years remain separate audits.
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
- 160 distinct reference IDs for complete English item-name candidates in 443 native storage
  slots, retaining GameCube spelling/case and the original ten-byte fields.
  Thirty-five direct item-loader calls and their contexts are inventoried.
  Wider imports remain gated on name, message, handbill, and UI destinations.
- Standalone sixteen-byte item-name API and separately configured DMA resource.
  All sixteen-bit item IDs pass portable index/conversion/guard tests. Native
  DMA tests cover every confirmed reference identity, group boundaries, invalid
  inputs, unaligned destinations, resource disabling, and header validation.
  The resource has 461 candidate reference IDs in 1,365 slots. This API alone does
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
- Complete-native-record alias matching supplies 41 unambiguous dialogue candidates.
  Source/reference hashes, the entire adapted output, and normal command/capacity
  checks are retained. No unresolved alias conflicts remain after exact native
  development labels are handled separately; drafts,
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

The current experimental resident-module pilot in `build/native-mood-pilot/`
contains 12,174 edits, including
9,755 reference main-bank candidates, all 460 choices, 572 original dialogue
drafts, one original-dialogue continuation, 290 original development-label drafts,
and 99 complete diagnostic drafts.
Two additional original
Pelly/Phyllis error messages extend the main bank
to 11,754 records; they do not change the existing candidate counts. Candidates
still require review. The original main-bank audit leaves 1,035
records without candidates; the classification and remaining restrictions are
listed below. The 1,471 conservative layout-warning records include full default
catchphrase width and do not trigger automatic
reflow. Detailed candidate, rejection, and coverage reports remain local in
`build/native-mood-candidates/` and `build/native-mood-coverage/`. The independent
mail control gate withholds `mailb:00BB` until native mail supports its
capitalization command. Layout warnings account for the wider catchphrase display.

All functional records in Nook's introductory range `07E0..083D` have English
candidates. Fourteen added records close ten functional gaps and provide four
reserved continuation slots. The complete job-ending speech and HRA explanation
retain GameCube wording, manual layout, and pauses, splitting only at existing
page transitions. The map handoff names the native R button. The short debt
insistence uses an original translation with all native commands unchanged.
Opening-reserve labels `083F/0840` have English label drafts; `083E` supplies the guarded
late-night resident introduction continuation described below.
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
Other things label. All 460 native choices have candidates: 451 supplied
reference labels and nine original drafts, including the shared-label corrections
in the broader native-menu batch. The twins' `172A/1737` remain withheld
for their separate speaker/echo differences. All 22 complete messages and six
referenced choice labels pass native cartridge loads with buffer/module guards
and checkpoint restoration. The 32-test reference batch passes, including four
new native-choice tests. See [native choice contract](../specs/REFERENCE_CHOICES.md).
Ordinary selection, selling/ordering, echo rendering, and line-width warnings
remain gameplay and human-playthrough checks.

The earlier N64 shop range `02DC..02F0` also has candidates throughout. Five
cross-ID GameCube matches and eleven native-command-preserving original drafts
cover its remaining text. The draft purchase prompts retain exits `02E6/02E5`;
the three-choice service menu gains no catalog action. Existing candidates stay
unchanged. These records have unestablished reachability and are counted as
text coverage, not additional proven gameplay interactions. The 33-test reference
batch and all sixteen complete native cartridge loads pass, with buffer/module
guards and checkpoint restoration. Original draft layout/presentation review remains separate from
the reference-candidate warning count.

Twenty-five favour/task-response messages retain the original native actor
request destination and value through individually hash-bound approvals. The
GameCube quest-row command is not imported into the native NPC0 actor row.
Complete native actor-command sequences, surrounding English wording/layout,
and normal field/flow/capacity checks remain enforced. All 25 complete cartridge
loads and actual request dispatches pass in one fresh four-MiB batch: fifty
native calls and 132 assertions. Complete order tables, adjacent/module guards,
and checkpoint restoration pass; the separate quest row remains unchanged.
All 44 reference-group tests pass. Existing candidates, font metrics, runtime,
and saved layouts are unchanged. Ordinary NPC actions and quest progression
remain combined gameplay/human-playthrough work. See
[native actor-request contract](../specs/ACTOR_REQUESTS.md).

Twenty-six further messages have individually reviewed current-player/current-town
field permissions, retaining complete GameCube wording/layout and all ordinary
flow, actor, and expansion guards. Native `1A` and `2F` read verified current
player/village sources, not actor-prepared free strings. The complete final hashes
and exact added-field sets are independently checked by the builder. All 26
cartridge loads and 27 actual insertions pass in a fresh four-MiB run, including
complete resulting text/headers, player-name colour spans, cursor positions,
unchanged source names, buffer/module guards, and checkpoint restoration.
Existing candidates and production runtime/font/save structures are unchanged.
Seventeen additional conservative layout-warning records remain for polish.
The complete 440-test suite passes with the shared validation changes.
Different GameCube festival, tailor, and travel-rule records stay withheld for
native-specific translation. See [reviewed field contract](../specs/REFERENCE_FIELDS.md).

Seven [original N64-specific drafts](../specs/NATIVE_ADVICE_TRAVEL.md) cover
errand notes, telling time by sunlight, post-wait conversations, the travel
record-erasure warning, and both post-office original-Pak requirements.
All native commands/arguments are preserved except seven explicitly checked
colour-span lengths for the full term `Controller Pak`. The warning retains
its original choices, branches, and clear erasure wording. The 52-test reference
batch passes, and all seven complete native cartridge loads pass with guards
and checkpoint restoration. Ordinary travel/post-office actions and draft
presentation review remain. Existing candidates and production code are unchanged.

Twenty-seven [resident catchphrase approvals](../specs/REFERENCE_CATCHPHRASES.md)
retain the full English reference where the native speaker supplies the added
phrase. The normal talk request preserves its actor through requested window
`2E0`, native appearance initialization, and client `20`. The permission adds
only `1C`, binds complete source/reference/output hashes, and cannot combine with
other added-field or control approvals. All 27 messages pass actual native
appearance requests, complete initializer/DMA loads, and catchphrase dispatch.
The batch includes two distinct ten-character defaults, custom input, and a null
request clearing the previous client: 91 native calls and 432 assertions pass.
Complete actor/animal sources, message/window/stack/module guards, and checkpoint
restoration pass. The full 440-test regression suite passes. All existing 10,515
edits remain unchanged, as do production runtime, font, and saved structures.
Ordinary NPC traversal and final dialogue/presentation review remain.

Four [native festival drafts](../specs/NATIVE_FESTIVALS.md) retain the N64 carp
streamers and moon-viewing events instead of incompatible GameCube holidays.
All native commands, choices, branches, pauses, and pages are preserved.
The dated messages require the complete [resident-date patch](../specs/DIALOGUE_DATES.md),
which redirects three preparation calls and the leap-month literal without
changing the native calendar calculation, field sizes, or saves. The actual
cartridge overlay loader, 53 preparations, thirteen conversions across six
years and a leap month, six message loads, and eight date insertions pass:
102 native calls and 184 assertions, with full save retention and guards.
The resident-date build passes all ten train-to-town checks over 188 steps.
The complete 440-test suite passes. The resident image remains 22,720 linked bytes
with 1,856 bytes free. Final draft review and normal seasonal gameplay remain.

Twenty-one [native seasonal conversations](../specs/NATIVE_SEASONAL_CONVERSATIONS.md)
cover shrine/queue dialogue, moon-viewing food jokes, returning insects, winter
activities, and related fullness/travel-stock advice. The spring bug-catching
question and both responses retain the original choices, branches, and quest
values. All 21 drafts preserve every native command and argument, including
pauses/pages and the inviter field. All complete cartridge loads pass in one
four-MiB batch: 21 native calls, 65 assertions, and 114 recorded steps, with
adjacent/module guards and checkpoint restoration. Existing 10,546 edits,
production runtime, font, and saved structures are unchanged. Normal seasonal
actions and final draft wording/layout remain for the combined gameplay and
human-playthrough review. No additional train or mail-window run is needed for
this text-only batch.

207 [resident-animation approvals](../specs/RESIDENT_ANIMATIONS.md) retain
complete English introductions, moon conversations, clothing errands, and other
resident exchanges. The [broader conversation batch](../specs/RESIDENT_CONVERSATIONS.md)
covers 65 complete references, including clothes-delivery requests, recipients
trying on clothes, failed-errand returns, and furniture/roof-colour responses.
Four references remove only a redundant pre-field article-suppression command;
all English wording and presentation remain. Five original drafts retain the
complete fishing tip, winter flowers, March 14 White Day, and May carp streamers
where the English reference omits instructions or describes a different event.
All seventy complete cartridge loads pass in one four-MiB batch: seventy
calls, 212 assertions, and 359 recorded steps, with adjacent/module guards,
checkpoint restoration, and blank FlashRAM. All 457 host tests pass. Ordinary
clothing handoff/animation/return, sale/painting actions, dynamic-field display,
and final wording/layout remain in the gameplay/playthrough queue.
Only reviewed NPC0 slot-zero expression delivery differs; fields, other actor
requests, gameplay decisions, source identity, and complete payloads remain
guarded. The native batch passes 213 expression-selection cases, eighteen
cartridge loads, and 88 command dispatches: 322 calls and 654 assertions, with
complete save retention, allocation/stack/module guards, and restored checkpoint.
The test records calls at the animation-initializer boundary, so actual poses
and normal resident playback remain gameplay checks. Production animation code,
font data/metrics, and saved layouts are unchanged.

The [parcel and town-advice batch](../specs/PARCELS_TOWN_ADVICE.md) supplies
49 more complete English references and eight native-specific drafts. These
retain borrowed-item returns, cancelled searches, deferred rewards, shared-town
advice, White Day/May/Thirteenth Night, rain, native paint colour, and Nook's
498,000-Bell final renovation. All 57 complete cartridge loads pass with 173
assertions and 294 recorded steps; all 457 host tests pass. Every previous
candidate edit and all executable/font/runtime resources remain unchanged.
Normal handoffs, actions, dates, debt payment, final wording/layout, saves, and
hardware acceptance remain.

The [community conversation batch](../specs/COMMUNITY_CONVERSATIONS.md) supplies
75 complete English references and eighteen native-specific drafts. It covers
more introductions, trades, games, rewards, letters, seasonal remarks, and
advice. Native originals retain White Day, actual fireworks/blossom dates, the
shrine venue, home creature care, moon viewing, the countdown invitation, and
Nook's self-made free monument. All 93 complete cartridge loads pass with 281
assertions and 474 recorded steps; all 457 host tests pass. Code, fonts, runtime
bindings, saved layouts, and all earlier candidate edits remain unchanged.
The read-only expression-difference queue contains twelve remaining
special-actor, sleeping-resident, and title-menu comparisons; these contexts
are not covered by the standing-resident permission. Other identity, field,
control, overflow, gameplay, and final review work remain active.

The [native-context batch](../specs/NATIVE_CONTEXT_REFERENCES.md) adds 73 more
messages: 64 individually bound references, Copper's R-button map instruction,
and eight native originals. Local wording spans correct shrine venues, native
sports dates, Controller Pak instructions, cartridge warnings, and absent GC
actors while retaining complete reference newline/page/pause sequences. Native
drafts retain actual travel rules, October Sports Day, and Nook loan advice.
All 73 complete cartridge loads pass with 221 assertions across 374 recorded
steps, unchanged adjacent/module guards, checkpoint restoration, and blank
FlashRAM. All earlier candidate edits and executable/font/resource data remain
unchanged. These loader checks do not execute erasure, travel, seasonal events,
map handoffs, Resetti animations, or normal saves.
The complete 477-test regression suite passes. Basic generation admits 72 of
the new messages and correctly withholds `16A5` without capitalization command
`75`; all eight native-context drafts remain available.
The read-only unconfirmed same-ID comparison pool is empty under the existing
rules; broader matching and incompatible topics/fields/controls remain. The
reference typos in `0670/08BF` remain explicit wording-polish tasks.

The [Pak and festival batch](../specs/PAK_FESTIVAL_DIALOGUE.md) adds 50 missing
messages and corrects the existing carp-streamer reply `0BC4`. Its 26 Pak drafts
distinguish absent storage, unreadable data, capacity, note slots, removal,
repair, and recovery. Data-loss warnings precede the unchanged repair choices;
the native three-service menus gain no GameCube-only action. Its 25 seasonal
drafts retain native carp-streamer jokes and fireworks dates/venues, including
the tunnel-game reply and shrine-plaza viewing remark. All original commands
remain exact except explicit colour counts for the full `Controller Pak` name.
All 56 complete cartridge loads pass with 170 assertions over 289 recorded
steps, including five connected unchanged replies. All 485 regression tests
pass. Basic generation admits every new draft. No repair, deletion, storage
interaction, seasonal selection, or normal saving is executed by this loader
test; those actions and final wording/layout remain gameplay acceptance work.
All earlier edits except the deliberate `0BC4` correction remain unchanged,
as do code, fonts, runtime resources, and saved structures.

Five [complete phone/furniture/letter conversations](../specs/LONG_ADVICE_SEQUENCES.md)
fit through ten individually approved records. Each splits only at an existing
English page transition; no wording, manual line, pause, or other page is lost.
Rover's phone-mode pair stays together, and its original final `046F` link
remains. Three furniture explanations retain all A-button instructions and
gift/work context. The letter-sharing explanation retains capitalization with
its catchphrase and requires the resident runtime. Only redundant article
suppression before an already-native item field is removed from `08FA`.
All ten cartridge loads, five internal links, the external phone link, and both
termination phases pass: 36 native calls, 70 assertions, and 169 recorded steps.
Complete text/headers, adjacent/module guards, checkpoint restoration, blank
FlashRAM, and the UPS round trip pass. All 494 regression tests pass.
Every earlier candidate and all production
code/font/save resources remain unchanged. Two conservative layout-warning
records remain for polish. Ordinary conversation, phone animation, furniture
handoffs, and rendered presentation remain gameplay/playthrough work.

The [native service/save batch](../specs/SERVICE_SAVE_DIALOGUE.md) supplies 47
original drafts: ten post-office messages, four gyroid messages, fifteen station
and Pak messages, and eighteen save-question/acknowledgement variants. Native
three- and four-service menus retain their actual choices and targets. Phyllis's
queue-full response and greeting keep every original expression and muted aside.
Repair refusal, success, failure, write failure, free space, and note slots stay
distinct; power/removal/data-loss warnings retain their native placement. The
six save pairs distinguish quitting from continuing. Every original command
remains except exact highlight lengths for Controller Pak, town data, and station.
All nine focused checks and all 503 regression tests pass. All 64 complete
cartridge loads pass with 194 assertions over 329 recorded steps, including
seventeen connected unchanged messages, guards, restored checkpoint, and blank
FlashRAM. This test loads text only, without performing saving or repair.
Basic generation admits all 47 drafts. Every earlier candidate, code/font/runtime resource, and
save structure remains unchanged, and the UPS round trip passes. Payment amount
width warnings remain explicit; ordinary menus, payments, repair, saving, dynamic
rendering, and final draft review remain gameplay/playthrough requirements.

The [seasonal topics batch](../specs/SEASONAL_TOPICS.md) supplies 29 original
drafts: 26 missing conversations and three corrected replies. Native moon
viewings, lunar dates, Sports Day, fishing rules, aerobics, matsutake, and seasonal
jokes retain every native command and argument. Ten questions keep their choice
and reply order. Six second-moon date drafts require the ordinary-dialogue date
patch; basic generation withholds them. All seven generic date-width warnings
remain visible, while all 372 English month/day combinations fit the affected
draft lines in host checks. All 511 regression tests, eight focused tests, and
46 complete cartridge loads pass, with 140 assertions over 239 recorded steps.
The load-only test restores
its checkpoint and leaves blank FlashRAM. Apart from the three explicit reply
corrections, all existing candidates remain unchanged. Code, fonts, runtime
resources, saved layouts, and event schedules remain unchanged. Ordinary event
selection, date rendering, shared choice-label wording, and full draft review
remain gameplay/playthrough work.

The [startup/Pak batch](../specs/STARTUP_PAK_DIALOGUE.md) adds 35 original drafts
for capacity, write failure, duplicate returns, accepted transfers, cancellation,
and mid-operation removal. The native overwrite warning stays before confirmation;
power/removal warnings stay before transfer requests. Start and post-transfer
targets remain exact. Only five explicit hardware/button highlight lengths
change. All 519 regression tests and 48 complete cartridge loads pass, including
thirteen connected unchanged messages, with 146 assertions and checkpoint
restoration. All new drafts fit without layout warnings in both full and basic
generation. Every earlier candidate remains unchanged. No storage operation is
executed by the test; actual startup/travel, confirmation/cancellation, dynamic
warning rendering, storage recovery, and final wording remain acceptance work.

The [startup greetings batch](../specs/STARTUP_GREETINGS.md) adds fifty original
drafts for player recognition, new faces, returning travellers, visitors,
retained-record preparation, menus, and clock acknowledgements. Full native
post-wait dialogue stays within ordinary preparations; travel paths keep their
different fields and continuations. The away-player warning, town-reset
cancellation, and identity retry retain their actions. No rumble option or
GameCube card field is imported. All 527 tests and 92 complete cartridge loads
pass, with 278 assertions and checkpoint restoration, covering all new messages
and 42 unchanged connected candidates. Seventeen generic town-width warnings
remain; all fifty drafts fit when checked with the native six-fullwidth-cell
town limit. Every earlier candidate and runtime/font/save resource remains
unchanged. Actual startup, storage actions, dynamic rendering, and final review
remain gameplay/playthrough requirements.

The six [opening clock references](../specs/STARTUP_CLOCKS.md) close the remaining
Japanese-static-text candidate gaps within `13F2..14E1`. They retain GameCube
greetings, calendar order, AM/PM, all manual lines/pages/pauses, and native
continuations, omitting only each unavailable storage-location clause. Full
source/reference/output hashes and exact allowed spans guard this narrow change.
All twelve cartridge loads pass for the greetings and their unchanged successors,
with 38 assertions, intact guards, restored checkpoint, and blank isolated saves.
All earlier candidates remain identical. Six new records have conservative
field-width warnings for presentation review; they do not trigger automatic reflow. Basic generation
withholds all six runtime-dependent references, and original-draft selection
also withholds actual module tokens without the module. Production runtime,
fonts, and saved structures remain unchanged. Normal startup selection, live
date rendering, full presentation review, and hardware acceptance remain.

The [resident-topic batch](../specs/RESIDENT_GAPS.md) fills 22 further records:
eighteen native-specific drafts and four complete cross-ID GameCube introductions.
It preserves letter/gift instructions, both bulletin boards, native moving rules,
errands, inventory refusal, train-delay fields, and related conversation. All
native controls remain except seven highlight lengths and AM/PM in the bedtime
draft. The four introductions preserve complete GameCube wording and delivery,
bound to identical native sources. All 31 complete cartridge loads pass, including
nine connected replies, with 95 assertions and restored isolated state. All
546 regression tests and eight focused tests pass. Every
earlier candidate remains unchanged. Basic generation admits 21 additions and
withholds the bedtime draft without its runtime. Five original drafts retain
conservative width warnings. Normal actions, live fields, final wording/layout,
saves, and hardware remain acceptance work.

The [development-label batch](../specs/PLACEHOLDER_TEXT.md) covers all 360 exact
native labels: 346 English label candidates and fourteen complete approved
continuation pages. The label drafts add 283 missing entries and correct eight
unrelated GameCube imports; all other existing edits remain unchanged. Exact
recognition, source hashes, importer/builder guards, and protected sequence
allocations prevent labels from becoming arbitrary gameplay dialogue. All 346
unallocated labels fit with their native commands, endings, and expression resets.
The 52-load native sample passes 158 assertions and checkpoint restoration;
all 557 full-suite tests pass. No font/runtime/save change or new continuation
allocation is made. Labels are not counted as additional gameplay conversations.

The [late-night introduction](../specs/REFERENCE_SEQUENCES.md) retains the complete
English `04F7` through `04F7 → 083E`. Its 1,174-byte conservative expansion bound
becomes two bounds of 773 and 419 by splitting only at the existing page break
after the clock joke. The buffer remains 1,024 bytes; no wording, pause, manual
line break, or clock read is removed. AM/PM requires the verified English runtime
and a preceding hour within the same record. Both native cartridge loads, the
continuation target, both termination phases, and memory/checkpoint guards pass
across seven calls and fifteen assertions. Normal resident progression and
rendered clock/presentation checks remain. Basic candidate generation completes
while withholding both runtime-dependent sequence members.

General strings, mail, saved names, dates, and item names have separate caller
restrictions. The independent wider item, display-name, catchphrase, and mail-catalog resources are not
additional ordinary-bank edits, and an API resource does not imply that every
gameplay destination uses its wider names.

The [gyroid/resident-state batch](../specs/GYROID_CHARM_DIALOGUE.md) adds 21
native-complete drafts and two full GameCube police-station explanations.
Every native draft control remains exact, including earlier gyroid menus,
owner-message insertion, power-off warning, state command `41`, and original
actor requests. The complete resident responses do not acquire GameCube-only
continuation targets. Both police explanations retain all GameCube wording,
layout, and timing, changing only their menus to original native choice IDs.
All 567 full-suite tests and 33 native cartridge loads pass, including ten connected unchanged responses,
with 101 assertions, complete guards, restored checkpoint, and blank saves.
All earlier candidates remain unchanged. Basic generation admits all 23 additions.
One generic owner-message field-width warning remains; the actual custom-message
formatter has its separate contract. Normal gyroid, saving, state transitions,
police choices, final wording/layout, and hardware remain acceptance work.

The [letter-message fragments](../specs/LETTER_MESSAGE_FRAGMENTS.md) supply 74
complete GameCube references and two native originals across
`1BFF..1C3E/1C53..1C5E`. Sixty-six Japanese bodies have exact cross-bank
equivalents after only outer whitespace and dialogue-ending removal; eight
source variations are individually reviewed. The separate importer and builder
bind both native sources and the complete reference/output, permit no added
fields, and append only the original ending. The originals preserve the actual
writer field and a joke missing from the mail counterpart. Basic generation
admits all 76 additions. All 577 full-suite tests pass before the final adjacent
fragment addition; all ten focused tests pass on the complete final batch.
All 76 final cartridge loads pass with 230 assertions, full guards, restored
checkpoint, and blank saves. Every earlier candidate, production code, font,
runtime resource, and saved layout remains unchanged. Eight generic field-width
warning records and two explicit reference typos remain for polish. Normal
callers, live fields, complete wording/layout review, and hardware remain;
this main-bank work does not approve stored-mail generation or delivery.

The [native-menu batch](../specs/NATIVE_MENUS.md) adds 135 complete GameCube
references and five native-specific questions, and corrects five connected
replies and eight shared labels. All 164 native-choice approvals bind exact
source/reference/menu/output hashes. English reference wording, manual lines,
pages, emphasis, and pauses remain; original N64 selection order and gameplay
branches are retained. Ten native dialogue drafts preserve every original
command and argument. Event answers retain native fireworks, April/October
Sports Fairs, and both moon viewings. The first eye chart displays M for its
actual third-choice answer; the bathing question and shared reply retain the
native yesterday/general-response context.
All 585 full-suite tests and seven focused tests pass. A combined native batch
loads all 145 new or corrected dialogue records, 23 unchanged connected replies,
and 126 actual referenced choice labels, including all eight corrections:
294 native calls and 632 assertions pass over 1,353 recorded steps, with full
text, adjacent/module guards, restored checkpoint, and blank isolated saves.
All 10,403 candidate main records and 460 choice records match their complete
built-bank payloads. Only the main/choice text, their pointers, and the DMA
directory change; code, fonts, runtime resources, and saved structures remain
unchanged. The UPS round trip passes. Basic generation admits 134 new references
and all eighteen original edits, withholding `0A0A` without cancellation support;
its candidate file does not establish that longer labels fit a retail buffer.
Nineteen new reference warning-bearing records and two original formatting
warnings remain for polish. Shared Circle/X labels stay available for shape
games; the contextual-label implementation supplies English answers for fourteen
approved quiz questions without changing their answer order. Nine menu
comparisons, further label contexts, live fields, ordinary answer actions,
final wording/layout, saving, and hardware remain.

The [contextual-choice implementation](../specs/CONTEXTUAL_CHOICES.md) gives
nineteen questions complete English answer labels without changing their answer
indices or actions. Fourteen quiz questions no longer display ambiguous shape
labels; actual shape games retain Circle/X. Five additional complete reference
questions and four native-specific connected replies fill nine missing messages.
All surrounding reference wording, lines, pages, emphasis, and pauses remain.
Every original draft command stays exact, including the native two-way trade
continuation and the moving conversation's final ending.
All 595 regression tests and ten focused tests pass. One isolated native batch
passes forty unique message checks, 42 selected-label/insertion cases, and all
38 corresponding conditional branch cases: 302 calls and 484 assertions over
1,195 steps, with restored checkpoint and blank FlashRAM/Pak files. Ordinary
trades, moving, quiz actions, rendering, and gameplay remain separate checks.
All 11,657 ordinary edits match the current built ROM. Against the native-menu
pilot, only main text, its pointers, and the DMA directory change; all twelve
referenced labels, fonts, code, runtime resources, and saved layouts remain
unchanged. The UPS round trip passes. Basic generation withholds sixteen
otherwise eligible contextual messages because complete required English labels
are absent; it does not shorten labels or silently restore misleading answers.
Nine menu comparisons and further native dialogue, fields, and caller review
remain active.

The [native return greetings](../specs/RETURN_GREETINGS.md) fill 35 missing
conversations in `00B0..00D2`. Their supplied same-ID GameCube records contain
only termination, so these are original translations of the native Japanese.
Every original command, month/week field, catchphrase occurrence, page transition,
per-page line count, and continuing ending remains. All full conservative
expansion and layout bounds fit; no font or runtime change is needed.
All 602 full-suite regression tests and seven focused tests pass. The complete
native loader batch passes all 35 messages and 107 assertions
over 184 recorded steps, with guards, restored checkpoint, and blank isolated
saves. All 11,692 ordinary edits match their actual built-bank entries, and
the UPS round trip passes. Both full and basic generation add exactly these
35 messages without changing or removing any earlier candidate. Ordinary
greeting selection, actual absence-field preparation, rendered names/catchphrases,
final wording review, saves, and hardware remain separate requirements.
The adjacent `00A3..00AF` month-return conversations belong to the complete
daily-greeting batch. The earlier `0013..005A` introductions/reunions have their
own complete draft batch below. The distinct `0001..0012` samples remain
untranslated and require individual content/control review; their position
in the bank does not establish reachability.

The [native daily greetings](../specs/DAILY_GREETINGS.md) add 85 complete original
drafts for `005B..00AF`: 24 recent-move conversations, 24 daily greetings, 24
repeat greetings, and thirteen month-return conversations. All same-ID English
slots are empty. Every native command, field/page sequence, per-page line count,
wait/clear, and continuing ending remains. English preserves the separate old
and current town fields, repeated names, month counts, native jokes, sleepiness,
day/night distinctions, and the three-kilogram remark.
Full and basic generation add only these 85 messages; all earlier candidates
remain unchanged. All 11,777 ordinary edits match their complete built-bank
entries, and the UPS round trip passes. Only main text, its pointers, and the DMA
directory change; code, fonts, runtime resources, and saved structures remain
unchanged. Six explicit generic current-town width warnings remain for polish;
all 85 layouts fit with the verified six-fullwidth-cell current-town limit and
every other field's full conservative bound. No global validator is narrowed.
The combined `005B..00D2` range has 120 complete English drafts. Actual callers,
normal greeting/move selection, live fields, final wording/presentation, saves,
and hardware remain separate acceptance requirements.
The isolated native batch passes all 85 complete cartridge loads, 257 assertions,
and 434 recorded steps, with complete headers, adjacent/module guards, restored
checkpoint, and blank FlashRAM/Pak files. It does not execute ordinary greetings
or change any player, NPC, or saved progression.
All 610 full-suite regression tests pass, including the eight focused
daily-greeting checks on the final drafts.

The [native introductions and reunions](../specs/REUNION_GREETINGS.md) add 72
complete drafts for `0013..005A`: 24 introductions, 24 long-absence reunions,
and 24 short-absence reunions. All same-ID English slots contain only termination;
native and legacy Japanese agree, with no identical visible native duplicate.
Every original command, field occurrence/order/page, wait/clear, page count, and
continuing ending remains. Literal one-month wording, dynamic month/week units,
repeated names/catchphrases, delayed recognition, and native jokes stay distinct.
Only `002C` page zero changes its five native lines to four English lines by
combining the interrupted greeting and surprise, without dropping any meaning,
field, page, or pause. No actual GameCube reference is reflowed.
Both generation modes add exactly these 72 records and leave every earlier edit
unchanged. All 11,849 ordinary edits match their complete built-bank payloads;
UPS application reconstructs the verified ROM. Changes are confined to main
text, its pointers, and the DMA directory; code, font/runtime resources, and
saved structures remain unchanged. All expansion bounds fit at 148–620 bytes.
Nine explicit generic current-town width warnings remain; all 72 layouts fit
with only `2F` substituted by six fullwidth cells and all other fields retaining
their conservative bounds. The global validator stays unchanged.
All ten focused tests and all 620 full-suite regression tests pass. The silent
four-MiB cartridge batch passes 72 complete loader calls, 218 assertions, and
369 recorded steps, with complete headers, adjacent/module guards, restored
checkpoint, and blank FlashRAM/Pak files. These checks do not execute ordinary
introductions/reunions or their field preparation, nor establish final wording,
presentation, saving, or hardware acceptance. The complete `0013..00D2` range
has 192 English drafts; full review remains required.

The [moving and game-launch drafts](../specs/NATIVE_MOVING_AND_LAUNCH.md) supply
eight native conversations and seven NES prompts. The town-satisfaction question
retains its original answers/replies; native moving remarks gain no GameCube-only
menus or actions. The launch prompts retain all seven exact supplied GameCube
furniture titles, original choice order, and the existing quit-button explanation.
Only the seven prompts' title/question-mark colour lengths change. The moving
drafts retain every native command and field placement by page. All fifteen fit;
two generic current-town warnings remain, with the verified six-cell check passing.

The [complete diagnostic guard](../specs/NATIVE_DIAGNOSTICS.md) covers 99 records:
28 rumour-pattern labels, 68 script-bug labels, and three gyroid debug notices.
It fills 73 missing entries and corrects 26 partial English labels, preserving
printed numbers, the debug-report request, native credit, and every command.
These are diagnostics, not 99 additional gameplay conversations. The builder
rejects partial labels, changed numbers, and unrelated save/menu imports.
Diagnostic recognition does not change the coverage categories or denominator;
the 26 corrections earn no extra source-volume credit.

Both generation modes add 88 records and correct exactly those 26 labels, with
all other edits unchanged. All 11,937 installed payloads and the UPS round trip
pass. The twelve focused checks and complete 632-test suite pass. One silent
four-MiB batch passes all 114 new/corrected cartridge loads and unchanged
connections `0FA9/17B5`: 116 calls, 350 assertions, and 589 recorded steps.
Headers, adjacent/module guards, checkpoint restoration, graceful shutdown,
and blank isolated FlashRAM/Pak files pass. Production code, fonts, runtime
resources, and saved layouts remain unchanged. Actual moving, game launching
and quitting, diagnostic callers, final wording/layout, and hardware remain
outside these loader checks.

Four [complete native travel explanations](../specs/NATIVE_TRAVEL_ADVICE.md)
retain the Controller Pak instructions and native personalities instead of
importing GameCube-only Memory Card travel rules. All native pauses, fields,
page order, actor commands, and endings remain, with only explicit colour-length
corrections. `0848` retains every detail of its travel and bulletin-board advice
through `0848 → 0A27`. Its full 1,134-byte expansion bound becomes 663 and 489
bytes by splitting only at the existing page boundary before bulletin-board
advice. The original translation and both complete parts are hash-bound.

The independent builder supports an explicit native-original sequence source,
checks the complete native command sequence, and reconstructs every original
English byte from ordered slices. Original work is not attributed to the supplied
disc; GameCube sequence permissions stay unchanged. The exact `0A27` reserve has
no native message-script target, matching audited instruction immediate, or
aligned non-executable halfword reference. This is not an exhaustive indirect-
caller proof. Both generation modes install the complete group and all three
ordinary drafts. Every other candidate is unchanged; the reserve's old label
is the only replaced existing edit.

All twelve focused checks and all 644 regression tests pass. One silent native
batch verifies five complete cartridge loads, the internal link, both termination
phases, memory guards, and restored state: ten calls, 25 assertions, and 56 steps.
All 11,941 actual installed edits and the UPS round trip pass. Code, fonts,
runtime/name/mail/choice resources, buffers, and saves remain unchanged.
The three ordinary drafts fit at 861, 695, and 828 expanded bytes. Three generic
current-town warnings remain; all four complete layouts fit the verified six-cell
town limit with every other field bound unchanged. Normal conversation, travel,
board posting, final wording/presentation, and hardware validation remain.

## Complete item-name identities

The [reviewed item-name registry](../specs/ITEM_REFERENCE_MATCHES.md) supplies
179 complete GameCube furniture names where legacy wording alone did not match.
Each approval binds the native Japanese spelling, source hash, English reference
and full padded hash, and all four rotation names. Both candidate generation
and independent ROM/resource construction enforce the approval. Removing its
metadata or re-hashing shortened text cannot bypass the complete-name check.
Ambiguous artwork, species, figurine, and unused-name differences stay unapproved.

All 179 names fit sixteen bytes, adding 716 resource slots. Fifty-three fit the
unchanged ten-byte fields, adding 212 ordinary slots. Current full generation has
12,174 edits; basic generation has 11,464, including both startup-error drafts
and all nineteen mood-preserving references.
All earlier candidates remain unchanged.
Ordinary item storage contains 443 slots from 160 distinct references; the wide
resource contains 1,365 slots from 461 references. Four rotations are one name,
not four distinct translations. The 126 new names longer than ten bytes remain
complete in the wide resource, not shortened for unexpanded callers.

All 12,174 actual installed edits, source/candidate/build hashes, the complete
wide-resource reconstruction, and the UPS round trip pass. The name-only pilot
changes only the native item-name file and the existing wide-name resource
relative to the travel pilot; their dimensions and DMA entries remain unchanged.
Runtime code, main text,
fonts, save structures, and caller capacities are unchanged by the name edits.
The 671-test suite includes all eleven item checks. The combined native loader
batch passes 757 calls and 749 memory assertions over 2,271 steps, including all
461 wider-name reference identities and all 212 new ten-byte slots. Complete
names, unaligned wide destinations, capacity/header failures, guards, and restored
state pass. The earlier shorter-time-limit run remains recorded as incomplete.
Normal item display and remaining wider destinations still need their own
integration and gameplay checks.

## Native startup errors

The [cartridge-clock and town-data drafts](../specs/STARTUP_ERRORS.md) translate
`09CC/09D1` without importing the GameCube's different hardware and actions.
The clock warning retains playing immediately or waiting, native choices
`00E7/00E8`, and successors `09CD/09CF`. The corrupted-town notice retains its
original request and normal ending, without adding erasure or card-slot choices.
Every native command remains except the exact highlighted booklet-name length.
Both complete drafts fit at 361 and 178 expanded bytes with no layout warnings.

All five focused checks and the 671-test full suite pass. One silent four-MiB
native batch passes the two drafts and three connected messages: five complete
loads, seventeen memory assertions, guards, and restored state. The final ROM
retains every earlier edit, all name resources, code, fonts, and saved structures.
Normal error selection, clock recovery, date entry, final wording, saving, and
original hardware remain separate acceptance requirements.

## Native mood effects in complete English references

Nineteen [complete English conversations](../specs/NATIVE_MOOD_REFERENCES.md)
retain the original resident mood and duration commands at individually reviewed
corresponding pages. Every supplied English word, newline, page, and pause stays
intact. The sun-contest message places its effect after the fourth English page
clear, not the third native page clear. The approval requires complete original
actor-command order before adaptation and the unchanged native mood consumer.
No gameplay code, saved structure, font, or buffer capacity changes.

All eleven focused tests and the 671-test full suite pass. The silent four-MiB
native batch passes nineteen complete cartridge loads and 38 actual order
dispatches: 57 calls, 140 memory assertions, guards, and restored state. All
12,174 installed edits and the UPS reconstruction pass; every earlier candidate
and every resource outside the main text/table remain unchanged. Normal resident
mood progression, rendered conversation, final wording, saving, and original
hardware remain separate acceptance requirements.

## Text-volume measurement

The generated coverage report measures 634,913 covered source characters out of
746,978 across all 29 native text banks. The denominator counts non-whitespace
visible characters in Japanese-static-text records; each native record ID counts
separately. Commands, exact development labels, already-English records, and
symbol-only sources are excluded. The numerator uses the original source weight
when a complete decoded Latin or punctuation/symbol candidate is installed;
longer English wording does not earn extra weight. English letter-header commas
and punctuation-only dynamic responses remain candidate replacements.

`tools/text_coverage.py` writes both per-bank and aggregate volume values with
the source/candidate hashes and measurement definition. Empty, still-Japanese,
or undecodable replacements receive no credit. Separate runtime resources do
not add credit for incompletely integrated destinations. Embedded UI strings
and image text are outside the extracted-bank denominator. This is candidate
replacement coverage, not semantic review, gameplay acceptance, total discovered
asset coverage, or overall project completion. Report percentages only when
explicitly requested, and retain this definition for comparable text measurements.

## Validation and release status

The resident-module experiment contains 12,174 edits, including
9,755 reference main-bank candidates, 290 original development-label drafts,
99 original diagnostic drafts,
all 460 choices, 178 villager names,
443 item-name slots, four N64-specific exercise drafts, two greeting-job drafts,
four other introductory drafts, eleven earlier-shop drafts, seven native
advice/travel drafts, four native festival drafts, 26 native seasonal
conversation drafts, eight native town-advice drafts, eighteen native
community drafts, eight native-context drafts, 26 Pak drafts, 25 carp/fireworks
drafts, 47 native service/save drafts, 29 seasonal-topic drafts, 35 startup/Pak
drafts, fifty startup-greeting drafts, eighteen resident-topic drafts,
21 gyroid/resident-state drafts, two letter-fragment drafts, ten native-menu
dialogue drafts (including five connected reply corrections), four
contextual-menu reply drafts, 35 native return greetings, 85 native daily,
move, repeat, and month-return greetings, 72 native introductions/reunions,
eight native moving conversations, seven game-launch prompts, and four complete
native travel explanations using five records, and two native startup errors.
It retains the GameCube calendar wording in Rover's opening
question and admits reference capitalization and protected-pacing spans.
Its reference/label generator rejects 1,036 main records; one receives an original
fallback dialogue draft. The final candidate-file audit finds 1,035 main records without
candidates: 113 with Japanese text, no exact placeholders, 919 with no static
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
