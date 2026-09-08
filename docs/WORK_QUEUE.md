# Completion queue

This is the durable queue for the complete translation project. A working
milestone does not complete the project. Continue through available work without
requiring the user to advance an automated procedure. Commit verified changes
and update the evidence links as each task progresses.

Prioritise bulk English content and complete playable sections. Batch automated
crash, save-integrity, text, and regression checks around meaningful changes.
Do not repeatedly retry difficult isolated tests while unrelated implementation
waits. A human playthrough supplies broad gameplay bug reports after the main
port, followed by the edge-case and polish pass.

Status meanings: **active** = being implemented or audited; **pending** = required
work remains; **external validation** = cannot be claimed without the specified
hardware or independent permission/evidence. A task becomes complete only when
its acceptance checks pass, not when a candidate or specification exists.

Follow-up R05 tasks: validate the ordinary post-office hand-back/error flow and
finish remaining readers/metadata before enabling generation. The Pelly patch
passes 48 native actor receipt cases, eight hand-back initializer cases, sixteen
refusal selectors, and ten index boundaries. Failed letters return to their
original pockets without reporting success. The fixtures run actual action
initializers but do not establish normal animation or subsequent player input.
See [receipt evidence](../specs/PELLY_RECEIPT.md).
Keep generation opt-in while completing unrelated content and gameplay work.

The first-job and ordinary NPC letter-show handlers in overlays `00814FA0` and
`00815B70` pass isolated native caller-level validation. Their three
reverse-conversion paths preserve complete ordinary/snapshot letters and reach
board read mode one. Instruction, BSS-lifetime, relocation, and execution
contracts are recorded in [NPC letter-show design](../specs/NPC_MAIL_SHOW.md).
Read-only letter headers now resolve complete English villager names using the
existing saved identity. Host tests cover all 216 villagers and fallbacks;
eight full native windows and ten ordinary-header cases pass. No saved
name capacity, source letter, font metric, or reference line break is changed.
The NPC caller harness passes all nine windows. It uses both original overlays,
independently checks their relocated file/BSS image, and keeps the temporary
letter allocated through close. Nine window cases cover all three caller
branches with ordinary letters and both snapshot kinds. The complete run and
checkpoint restoration pass. Normal actor interaction remains distinct from
these isolated calls. Next R05 work covers ordinary post-office hand-back/error
progression and the remaining inline metadata/excerpt, travel, and editor paths;
the direct reverse-conversion callers are no longer an untested-reader item.
The isolated [native FlashRAM persistence test](../specs/FLASH_MAIL.md) passes
all 192 saved mail slots in both native save banks. A separate fresh process
receives only the exported cartridge save and passes all 384 complete-record
checks and eight complete English reconstructions. This is not normal save-menu
or post-load gameplay validation; generation remains opt-in.

Native Controller Pak writing and fresh-process reading pass for the `1200`-byte
passport and `6700`-byte stored-letter note: all 177 complete letter records,
both file checksums, complete player/NPC imports, and six English reconstructions
in each process. See [Pak persistence contract](../specs/PAK_MAIL.md). Ordinary
travel and storage-menu flows remain separate requirements.

The [native letter-menu selector](../specs/MAIL_MENU.md) passes 120 isolated
status/gift/marker/context cases and retains every complete source letter.
All 44 static tag-label definitions pass native length checks, closing that
specific shared-helper provenance item. Received letters select Read; drafts
select Rewrite. Shared close-helper inspection establishes the read path's
motion-to-end transition without entering edit acceptance. Remaining editor work
includes parent-menu interaction, complete pointer ownership, generation status
assignments, and normal custom editing. These checks do not enable generation
or establish full menu gameplay.

The [whole-letter generation transaction](../specs/MAIL_GENERATION.md) now passes
all 6,398 supported host reference assembly cases and 53 native generation cases,
plus 42 native field-capture cases. It preserves complete saved metadata and
rejects missing fields, overflow, and unavailable resources before publication.
The generation code also belongs to the optional cartridge-loaded NPC creator.
Normal delivery and remaining reader/editor interactions remain follow-up work;
generation is not enabled by default.
The [NPC creator binding contract](../specs/NPC_MAIL_GENERATION.md) verifies
complete native/reference functions and selection tables. All available reply
parts have supplied source slots across 24 group/gift contexts and 36 classic
selections. One composite footer remains unavailable. Original creation failure
is not propagated to submission. The guarded failure-return gate passes 41
isolated native cases, including twenty actual queue receipts, rejected creation,
both counter components, every queue slot, invalid recipients, and full home
mailboxes. That receipt test uses a controlled creator fixture. Optional
installation connects the real creator; actual creator-to-receipt and pending-loop
checks remain queued for batch integration.
The [complete word source resource](../specs/NPC_MAIL_WORDS.md) verifies all 352
phrases against the actual source banks and records full source/reference IDs.
All 83 phrases beyond ten bytes are retained within sixteen bytes. Connect this
resource before native truncation. The [saved-name alias resource](../specs/NPC_MAIL_NAMES.md)
supplies all 216 full names from 394 exact original/short-English keys, without
guessing unknown identities. The scoped source/capture implementation passes
complete host coverage and cross-compiles as a bounded relocatable image.
All 48 original-versus-captured native creator comparisons pass, including full
English generation with unchanged RNG state, gifts, stationery, native fields,
and saved data. The whole-creator transaction now combines private metadata,
capture, complete generation, and guarded publication; host/sanitizer tests pass.
The native combined transaction passes 48 reply comparisons, eight successive
letters, and six rejected requests, including complete output/capital retention
on failure. The [resident cartridge loader](../specs/NPC_MAIL_LOADER.md), allocation
ownership, and real creator binding are implemented as one optional installation.
Native cartridge loading passes 56 complete English creations and eight failures,
including controlled allocation exhaustion, full save retention, and exact heap
totals after release. No creator code/resources are debugger-uploaded. The new
ROM passes four-MiB town arrival. Main content work proceeds while actual
creator-to-receipt and pending-loop checks stay queued for batch integration.
The resident module leaves 1,088 linked bytes inside the unchanged 32 KiB
reservation. Allocation/error ownership tests,
four-MiB town arrival, and all eight complete native letter windows pass.

## Main translation and runtime

Next content audits target the remaining inserted-text and actor-command gaps.
The [resident-animation permission](../specs/RESIDENT_ANIMATIONS.md) admits
207 reviewed complete English records while keeping all non-expression
actor commands, fields, flow, and capacity guarded. Its native batch passes
213 selections, eighteen initial loads, and 88 dispatches. Actual pose initialization
and normal resident playback remain gameplay checks, not reasons to repeat the
isolated selection batch. The wider expression-only mismatch pool still needs
individual topic/actor review; special actors and new values are not approved.
The [resident conversation batch](../specs/RESIDENT_CONVERSATIONS.md) supplies
65 additional references, including the clothing request/try-on/failed-return
conversations `0152..0198`, plus five native-complete fishing, flower, White Day,
and May festival drafts. All seventy complete cartridge loads pass with guards
and checkpoint restoration; 457 host tests pass. Normal clothing handoffs,
outfit animations, inventory returns, and sale/painting actions remain gameplay
checks. English same-ID references with changed native topics remain unsuitable
even where their command signatures match.

The [parcel and town-advice batch](../specs/PARCELS_TOWN_ADVICE.md) supplies 49
complete English references and eight native-specific drafts. All 57 complete
cartridge loads pass with 173 assertions, guards, and checkpoint restoration.
Native topics include White Day, May streamers, Thirteenth Night, rainy reading,
yellow-green paint, town dissatisfaction, size-based fishing advice, and Nook's
498,000-Bell final house expansion. Ordinary item/quest/debt/event actions remain
gameplay checks. The date-dependent draft is withheld without the complete date
patch; the other seven remain available in basic generation.

The [community conversation batch](../specs/COMMUNITY_CONVERSATIONS.md) supplies
75 complete English references and eighteen native-specific drafts. All 93
complete cartridge loads pass with 281 assertions and checkpoint restoration;
457 host tests pass. These retain ordinary trades/rewards, introductions, letters,
games, native event dates/venues, creature care, and Nook's self-made monument.
Ordinary actions, pose rendering, dates, final wording/layout, and saves remain
gameplay/playthrough requirements.

The [native-context batch](../specs/NATIVE_CONTEXT_REFERENCES.md) adds 64 complete
reference bindings, one R-button map adaptation, and eight original travel,
Sports Day, and loan drafts. All 73 complete native loader calls pass, with
221 assertions and checkpoint restoration; all earlier edits remain unchanged.
The complete 477-test regression suite passes, and basic generation retains
its runtime gates, including capitalization in `16A5`.
Wording spans retain every English newline and non-colour command. Normal
travel, erasure, saving, map handoffs, seasonal selection, Resetti display, and
final wording remain gameplay/playthrough work, not claims of this load test.
Keep reference typos `0670/08BF` in the final wording pass.

The [Pak and festival batch](../specs/PAK_FESTIVAL_DIALOGUE.md) supplies 26 Pak
drafts and 25 carp/fireworks drafts: fifty missing messages and a correction to
the previously mismatched tunnel response `0BC4`. The complete 485-test suite
and 56 cartridge loads pass, with 170 assertions and checkpoint restoration.
Native repair warnings, service choices, control arguments, and seasonal
dates/venues remain. Repair, data management, actual storage UI, seasonal
selection, saving, and final wording/layout remain gameplay checks.

`tools/identity_review_queue.py` exposes no further unconfirmed same-ID records
that fit the current rules. Its report in `build/mood-phrases-identity-review/`
identifies 866 without visible same-ID English, one requiring fields,
eleven with control differences, four overflows, 36 native non-static records,
ten glyph failures, and one encoding/hash uncertainty. These are review routes,
not permissions or unreachable-code claims. Cross-ID matching and native-only
translation remain available alongside existing field/control work.

Continue the ten comparisons in
`build/mood-phrases-expression-review/queue.jsonl`, generated by
`tools/resident_review_queue.py` from the current candidate file: Rover `0467`,
Gracie `0723`, Booker `0785`, Redd `0789`, Jingle `07AA`,
sleeping resident `0D3F`, and Gulliver
`2403/240A/240B/240D`. Every row is explicitly unapproved. Audit those actors'
consumers and contexts before changing their expression delivery; ordinary
standing-resident evidence does not establish those behaviours. Regenerate the
queue as candidates change. Broader same-ID identity review, unavailable fields,
native-topic corrections, and overflows also remain available content work.
Do not re-run the unchanged resident selector merely to admit more text.

The complete [late-night introduction](../specs/REFERENCE_SEQUENCES.md) uses
`04F7 → 083E`, split only at its existing GameCube page boundary after the clock
joke. Both complete records fit and pass native load/continuation/termination
checks. Basic builds omit the runtime-dependent group. Keep the original
wording, pauses, and manual layout; normal conversation and rendered clock
checks belong in the combined gameplay/playthrough pass.

Five [complete long conversations](../specs/LONG_ADVICE_SEQUENCES.md) now use
ten approved records, retaining all GameCube words and existing page/line/pause
intent. Rover's phone-mode pair and final link, three furniture explanations,
and the letter-sharing conversation's capitalization remain. All ten complete
cartridge loads, six links, and termination phases pass in one native batch:
36 calls and 70 assertions, with guards and checkpoint restoration. All 494
regression tests pass. Normal
actor progression, furniture handoffs, and rendered layout remain gameplay checks.
Remaining direct capacity rejections are `0B14` (native numeric test loop,
not missing Japanese prose) and `2511` (Resetti's special `58:08` ending).
The latter is not an ordinary `00/01` terminator and needs its own continuation
audit. Other overlong references remain inside the broader unconfirmed queue.

The [native service/save batch](../specs/SERVICE_SAVE_DIALOGUE.md) adds 47
original drafts, including the native-only menu variants, Phyllis `08B0/08B2`,
actual station/Pak conditions, and six quit/continue save triples. All original
commands stay exact except three explicit kinds of highlight-length changes.
No expression permission or new action is introduced. All 503 regression tests
and 64 complete cartridge loads pass, with 194 assertions and checkpoint
restoration. No saving or repair is executed. Payment amount preparation/width, ordinary service actions, save/reload,
Pak repair, and final wording/layout remain gameplay acceptance work.

The [seasonal topics batch](../specs/SEASONAL_TOPICS.md) adds 26 missing
conversations and corrects three existing replies, keeping ten native question
routes and six second-moon date dependencies. All 511 regression tests, eight
focused tests, and 46 full cartridge loads pass, with 140 assertions and
checkpoint restoration. All 372
English month/day combinations fit the seven date-bearing draft layouts under
host checks; generic warnings remain visible. Ordinary events, rendered dates,
the shared `2833` choice-label wording, and final draft review remain queued.
No event scheduling, date logic, actor permission, font, or save format changes.

The [startup/Pak batch](../specs/STARTUP_PAK_DIALOGUE.md) adds 35 missing storage
and return messages. All 519 regression tests and 48 complete cartridge loads
pass, including thirteen unchanged connected messages and 146 assertions. Every
new draft fits without layout warnings. Native erasure warnings, transfer
requests, cancellation, and continuations remain, with only explicit English
highlight lengths changed. Ordinary title/travel interactions, actual storage
recovery, warning rendering, and final review remain required. Do not repeat
the unchanged Pak loader batch.

The [startup greetings batch](../specs/STARTUP_GREETINGS.md) adds fifty complete
native greetings, preparations, menu variants, and acknowledgements, including
`14A2/14D9` without new expression permissions. All 527 tests and 92 full
cartridge loads pass, covering every new record and 42 unchanged connected
candidates. Native post-wait endings, twelve highlight corrections, actual
choice order, power warnings, and storage paths remain. Generic town-width
warnings remain; all new drafts fit the native six-cell town limit in host
checks. Normal startup/storage, warning rendering, and final review remain.

The [six opening clock references](../specs/STARTUP_CLOCKS.md) complete candidate
coverage for Japanese static text within `13F2..14E1`. Only the exact GC-only
storage-location clauses are omitted; all other reference wording and delivery,
native successors, and calendar/AM/PM intent remain. Complete native/reference/
output hashes guard every approval. Twelve complete cartridge loads and 38
assertions pass for the six greetings and six unchanged successors, with guards,
checkpoint restoration, and blank saves. Basic generation withholds the six
references; original drafts also require the module for extension tokens.
Normal startup selection, live clock rendering, and the six warning-bearing
records remain in gameplay/presentation review. Continue broader missing native dialogue;
no further static Japanese remains in this inspected startup range.

The [resident-topic batch](../specs/RESIDENT_GAPS.md) supplies eighteen native
drafts, including the moving and flower topics, and four full cross-ID GameCube
introductions. Native source equality establishes `2BC3/2BC5/2BC7/2BC9` against
`2DD1/2DD3/2DD5/2DD7`; complete references retain all wording and delivery.
All 31 cartridge loads and 95 assertions pass, including the complete connected
umbrella/colour-game reply chains, guards, and restored isolated state. Normal
actions, live field rendering, five original width warnings, and final review
remain. Continue broader untranslated native dialogue and candidate review.

The [reserve-label audit](../specs/PLACEHOLDER_TEXT.md) covers all 360 exact native
development labels. Fourteen approved continuation slots retain their full
English payloads; 55 valid reference labels remain; 291 original drafts supply
283 missing labels and eight corrections to unrelated GameCube imports.
No unresolved native alias conflicts remain. The generator and independent
builder reject unrelated dialogue in these label slots. All labels retain their
source controls and fit without width warnings. The 52-load native sample passes
158 assertions with guards, restored checkpoint, and blank isolated saves.
No reachability or new continuation allocation is inferred. Continue actual
missing conversations, field/control audits, and candidate review; do not count
label translations as newly translated gameplay conversations.

The [gyroid/resident-state batch](../specs/GYROID_CHARM_DIALOGUE.md) adds 21
native-complete drafts and two complete police-station references. All 33
cartridge loads and 101 assertions pass, including connected unchanged responses,
guards, checkpoint restoration, and blank saves. Native draft commands remain
exact; full GameCube police wording and delivery retain only the original N64
choice IDs. Basic generation includes all additions. Normal menus, state changes,
saving, owner messages, police choices, and final review remain separate work.

Continue broader missing native dialogue. Booker's `077E` has a native-complete
draft asking whether to take the item; its full loader check passes, while
ordinary claiming/refusal and shrinking-text presentation remain. Full references
`04D2/04FA` need semicolon glyph support and should not lose their supplied
wording just to avoid that support task. The [letter-fragment audit](../specs/LETTER_MESSAGE_FRAGMENTS.md)
supplies 74 complete cross-bank references and two native originals for
`1BFF..1C3E/1C53..1C5E`. Its native fields, complete reference text, and original
ending are independently guarded; this is not a mail-generation approval.
Keep the duplicate pronoun in `1C06` and missing verb in `1C2C` in the explicit
reference-wording polish queue. Normal caller/field and final presentation
review remain. Font-atlas edge
investigation remains paused; unrelated text and runtime work stays active.

The [native-menu batch](../specs/NATIVE_MENUS.md) supplies 135 complete reference
approvals, five native questions, five corrected connected replies, and eight
shared-label corrections. All 585 regression tests and the combined native
168-message/126-label load batch pass, with 632 assertions and restored isolated
state. Native menu IDs, answer order, event dates, and eye-chart success indices
remain exact. All reference wording and presentation remain; native drafts
keep every command and argument. Normal answering, live fields, final wording,
and rendering remain separate acceptance work.

The [contextual-choice implementation](../specs/CONTEXTUAL_CHOICES.md) supplies
twenty-six per-message mappings, including seventeen quiz menus and the reviewed
none/pear and agreement/refusal contexts. Shared Circle/X labels remain intact
for shape games. Five complete reference questions and four native-complete
replies add nine missing messages. Two native-original quiz mappings independently
guard every canonical native command and argument. Two complete unchanged-menu
references have their own explicit source kind and parent/hash checks. All
thirteen contextual tests pass within the 714-test full suite.
The combined birthday/calendar/choice native batch checks 57 selected labels and insertions
and 53 actual conditional branch cases, with 913 calls, 1,588 assertions, 4,083 steps,
restored checkpoint, and blank isolated saves.
Basic generation withholds eighteen mappings whose complete labels are missing;
it separately withholds old-calendar and birthday references without their preparation patch.
Do not bypass those dependencies. Broader contextual labels remain individual
review tasks, not a global label replacement.
The complete birthday references `088B/2586`, corrected acknowledgements
`088A/088C`, and original two-answer letter question `1C6F` are installed.
The birthday preparer retains the complete English names and dates, both
original random draws, native sign boundaries, and unchanged saved fields.
All 33 original birthday requests own a source-derived build dependency, even
without candidate metadata. Normal birthday entry/gifts, letter-show interaction,
and further shared-label contexts remain. Unsupported `74` remains rejected
except its existing direct pre-field removal; parsing a donor is not a new
runtime permission. Do not repeat the unchanged loader batch while those content
and runtime tasks remain available.

The [native return greetings](../specs/RETURN_GREETINGS.md) provide complete
original drafts for `00B0..00D2`; all 35 cartridge loads pass with 107 assertions,
unchanged page/field/ending controls, restored checkpoint, and blank isolated
saves. Every earlier candidate remains unchanged. Ordinary greeting selection,
live absence fields, final wording/presentation, saving, and hardware remain.
The [native daily greetings](../specs/DAILY_GREETINGS.md) add 85 complete drafts
for `005B..00AF`, including the adjacent thirteen month-return conversations.
Every native field, page/line count, and continuing ending remains. All earlier
candidates stay unchanged, and all 11,777 edits match the complete built-bank
payloads. Six generic current-town width warnings remain; all 85 drafts fit with
the verified six-cell current-town limit and all other fields' full bounds.
No font, runtime, or saved layout changes. The entire `005B..00D2` range has
English drafts; final caller, field, wording, and gameplay review remains.
All 610 regression tests and the 85-message cartridge batch pass, with 257
native assertions, restored checkpoint, and blank isolated saves.
The [introductions/reunions](../specs/REUNION_GREETINGS.md) add 72 complete drafts
for `0013..005A`. All native commands, fields, pages, and continuing endings
remain; the only line-count change combines the five-line `002C` opening into
four lines without dropping text or a pause. Both build modes add only these
72 records. All 620 regression tests and 72 native cartridge loads pass, with
218 assertions, restored checkpoint, and blank isolated saves. Every earlier
candidate remains unchanged; all 11,849 built-bank payloads and the UPS round
trip pass. Code, fonts, runtime resources, and saved layouts are unchanged.
Nine generic town-width warnings remain; all drafts fit the native six-cell
current-town limit with every other field's conservative bound unchanged.
The full `0013..00D2` range has 192 English drafts, requiring normal caller,
field, wording/presentation, gameplay, and hardware review.

The [moving/game-launch batch](../specs/NATIVE_MOVING_AND_LAUNCH.md) supplies
eight complete native conversations and seven NES prompts, preserving native
questions, answer routes, menu absence, and exact supplied English game titles.
The [diagnostic batch](../specs/NATIVE_DIAGNOSTICS.md) covers all 99 recognised
rumour-pattern, script-bug, and gyroid debug notices, filling 73 gaps and
correcting 26 incomplete labels. The independent builder requires complete
wording, printed numbers, credit, and commands; coverage classification stays
unchanged. These diagnostics remain distinct from gameplay dialogue.
All 632 regression tests and 116 complete cartridge loads pass, including the
unchanged `0FA9/17B5` connections, 350 assertions, and isolated state restoration.
All 11,937 installed edits and the UPS round trip pass. Normal moving selection,
game launch/quit, actual diagnostic callers, and wording/layout review remain.

The four [complete native travel explanations](../specs/NATIVE_TRAVEL_ADVICE.md)
`0848/0866/0870/087A` retain Controller Pak instructions, native advice, and
all pauses/fields/pages. `0848 → 0A27` replaces only its existing transition
before bulletin-board advice, preserving the whole 1,134-byte-expanded draft
in parts bounded at 663 and 489. The independent native-original sequence
guard binds the complete draft, original commands, explicit colour lengths,
safe reserve evidence, every slice, and both final payloads. All twelve focused
checks, 644 regression tests, and five complete native cartridge loads pass;
the same batch verifies the link and both termination phases with ten calls
and 25 assertions. All 11,941 installed edits and the UPS round trip pass.
Normal conversations, live fields, travel, board posting, final wording/layout,
and hardware remain. Do not replace compatible glyph-blocked references such
as `04D2/04FA` with native drafts merely to avoid implementing punctuation.

The [explicit furniture-name registry](../specs/ITEM_REFERENCE_MATCHES.md)
adds 179 complete supplied English identities, independently guarded by the
native source spelling/hash, English reference/hash, and equal rotation names.
Fifty-three names also fit ten bytes: 212 new native slots. All 179 fit the
sixteen-byte resource: 716 new slots. Current ordinary storage has 779 slots from
242 references; the wide resource has 2,713 slots from 771 references. The 126
longer new names remain withheld from unexpanded ten-byte destinations. No
existing candidate changes. Both generation modes, all installed payloads,
resource reconstruction, UPS round trip, and all 700 full-suite tests pass,
including fifteen focused item checks. The first-300-group native loader batch passes
757 calls, 749 memory assertions, complete names, guards, and restored state.
Remaining name work covers unapproved furniture groups, ordinary banks, and each
unexpanded destination. Name identity is not
proof of matching artwork or complete gameplay integration.

The [mapped-name batch](../specs/MAPPED_ITEM_NAMES.md) adds 308 furniture
approvals, 170 across shifted English indices, plus two carried-clothing
spelling approvals. It preserves native insects/fish/umbrellas, chess colours
and pieces, fossil parts, and seasonal series. Full resources gain 1,348 wide
slots and 336 ordinary edits without changing earlier candidates. All installed
payloads, converted full-name expectations, UPS reconstruction, and 700 tests
pass. Native batches pass 850 wide/header calls, 335 original-width calls, and
fourteen final spelling-variant calls with guards and restored blank states.
Gyroids, changed species/clothing/clock/umbrella designs, native game slots, and
unexpanded callers remain unapproved. Preserve supplied `racoon obje` spelling
until the final wording pass.

The [native cartridge-clock and town-data errors](../specs/STARTUP_ERRORS.md)
`09CC/09D1` retain the original hardware meaning, pauses/pages, both clock-error
answers and branches, and the native corrupted-town request/end. The supplied
GameCube's additional hardware fields and erasure choices are not installed.
Both full/basic generation modes include the complete drafts. Five focused
tests, the full 700-test suite, all actual installed edits, UPS application,
and five native loads covering the drafts and their connected messages pass.
Normal clock failure/recovery, date entry, saving, and final wording remain.

Twenty-five [complete mood-preserving references](../specs/NATIVE_MOOD_REFERENCES.md)
retain both original mood/timer orders at individually matched English pages or
phrases, with all reference words, layout, and pauses unchanged. Thirteen mood
checks, the 96-test reference group, seven coverage checks, all installed payloads,
UPS application, twenty-five native loads, and 50 native order dispatches pass
within the combined topic/context/mood batch.
The unchanged runtime retains its 700-test full-suite checkpoint. Explicit
phrase anchors cover `203A/262B/2637/264B/266B`; unanchored page rules stay strict.
Normal mood/timer progression and rendered conversations remain gameplay checks.
The complete `2773` snow reply is approved after reviewing the coherent English
parent and all three connected replies together. No general mood, actor, or random-branch
permission is granted by these individually bound approvals.

Continue the other remaining Japanese dialogue and distinct `0001..0012` samples
without assuming reachability. The early block includes personality descriptions
`0007/0008`, branching state tests, colour/position/scale tests, and timed voice
samples, not merely placeholder labels. `0004` already has a 1,314-byte
conservative native expansion bound; preserve its complete test semantics while
addressing English capacity. `000F/0010` terminate through timed-close `58`;
`0011` retains syllable pauses and sound variants. Do not flatten those controls
or let this separate sample audit delay the broader dialogue/runtime work.

The [later renovation block](../specs/NOOK_RENOVATIONS.md) installs the complete
English invoice as `107E → 083F`, changing only its price to the native 49,800
Bells and splitting at an existing English page boundary. Individually bound
native-price checks retain full wording and the 1,024-byte buffer limit.
Original `107F/1081` drafts retain native expensive-room enlargement, agreement,
refusal, and roof choices, not the GameCube basement actions. Eight focused,
96 reference, eleven placeholder, and seven coverage checks pass. The native
batch passes four complete loads, invoice continuation/termination, and all six
agreement/roof branch selections: 33 calls, 51 assertions, and restored state.
Normal repayment, roof selection, rendered progression, and hardware remain.

The [native-topic batch](../specs/NATIVE_TOPIC_GAPS.md) fills nine missing records
and corrects connected `25FD`. Original net, holes, moving, romance, item
attachment, sign/map quizzes, and complete meal-greeting jokes retain native
actions and answer order. Both full English shouts keep the original per-character
scale and colour; only their exact formatting lengths change. The separate
complete snow approval fills one more record. Nine topic tests pass, and every
new/corrected message is covered by the combined native batch. All installed
payloads and UPS reconstruction pass. Actual conversation selection/actions,
shout rendering, rewards, sign/map artwork, calendar selectors, and final wording
remain. Do not resume the paused font-atlas investigation for this text work.

The complete [old-calendar quiz](../specs/DIALOGUE_DATES.md#actual-old-calendar-quiz-request)
`246D` retains all supplied English wording and presentation. Native request
seven/value one prepares the current old-calendar month/day in free fields 15/16;
its complete English date-overlay dependency cannot be omitted through candidate
metadata. Affirmative/negative labels retain success/failure order. All 700
regression tests pass, including thirteen date/dependency checks. All 403 complete
month/day text combinations fit without reflow, and all actual installed payloads
and UPS reconstruction pass. Basic output is unchanged. Normal request polling,
calendar selection, rendering, rewards, and out-of-table dates remain.
Six actual quiz requests and relocated dispatcher cases pass complete current-date
preparation/insertion; two non-one requests leave all fields unchanged. All
53 ordinary preparations, thirteen earlier conversions, eighteen direct quiz
conversions, twelve date-message loads, and twenty date insertions pass. The
combined native run restores the complete clock and checkpoint, retains the
saved game, frees its owned allocation, and keeps both isolated saves blank.

Current main-bank coverage is 10,739 candidates; 1,013 records remain without
candidates, including 91 containing Japanese static text. The reference
rejection queue contains 926 unconfirmed identities, 62 control-signature
differences, 24 missing-field records, and two expansion overflows. These are
candidate counts, not completed semantic or gameplay review. Other overlong
records may use existing page-boundary splitting after their complete native
gameplay/field meaning and unused continuation slots have been established.

Twenty-five favour/task-response messages have individually approved native
actor requests. Native `09` writes NPC0 row four; `0C` writes quest row nine.
The adaptation retains the original `09`, slot five, and exact native value,
with complete actor-sequence and payload guards. All 25 full cartridge loads
and native request dispatches pass, including complete order-table and memory
guards. See [request semantics and scope](../specs/ACTOR_REQUESTS.md). Normal
subsequent actor actions and quest traversal remain gameplay/playthrough checks.

The 24 missing-field rejections include remaining catchphrases (`1C`), player
names (`1A`), town names (`2F`), mixed fields, and incompatible native topics.
Audit the actual insertion consumers and caller context rather
than assuming that a field absent from a native message is available globally.
Do not weaken field/actor guards simply to reduce rejection counts. These audits
must proceed in bounded content batches, without returning to repeated isolated
mail tests while broader implementation remains.

Twenty-six messages have exact, independently source/reference/payload-bound
permissions for added current-player/current-town fields. Native `1A` reads the
current-player pointer at `80136FD8` through `8009EBB0` and `8009EC88`; `2F` reads
the current town through `800950D8` and `8009F428`. All 26 complete cartridge
loads and 27 native insertions pass, including complete output, colours, cursor,
source retention, and guards. See [field contract](../specs/REFERENCE_FIELDS.md).

Four native festival drafts cover `119C/27C0` (carp streamers, not Harvest
Festival) and `11AC/180B` (moon viewing, not meteor showers). Complete native
commands and arguments are preserved. See [festival wording](../specs/NATIVE_FESTIVALS.md).
Seven original advice/travel drafts cover
`11F1`, `14FE`, `0945`, `1BD3`, `1BD4`, and the native post-wait conversations
`147F/14CF`. All seven complete cartridge loads and the 52-test reference batch
pass. See [draft contract](../specs/NATIVE_ADVICE_TRAVEL.md). Ordinary actions,
draft wording/layout review, and blank native-record flow review remain.

The carp reminder `27C0` retains native choices `0010/0018`, not the reference's
`0066/0018`, and branches to `27E8/27E9`. Both response candidates already fit
the native eating/refusal joke and preserve its complete actor/flow commands;
do not replace them solely because the GameCube preceding question mentions pies.
Moon-viewing drafts `11AC/180B` require the complete English ordinary-dialogue
date patch. Native tests pass 53 preparations, thirteen actual calendar
conversions, six message loads, and eight date insertions with unchanged saves
and field bounds. Free fields `3C/3D` retain the year's converted event dates,
not the current date. See [date preparation](../specs/DIALOGUE_DATES.md).
Normal seasonal selection/rendering and final wording/layout review remain.
Twenty-one further [native seasonal drafts](../specs/NATIVE_SEASONAL_CONVERSATIONS.md)
cover six shrine/queue conversations, eight moon-viewing conversations, five
spring/winter conversations, and the fullness/travel-stock responses. The
complete spring question `1F6B` and responses `1F77/1F78` retain native
choices `011E/0128`, both branches, and quest values. All original commands,
fields, pauses, and pages are preserved. No reference permissions or production
runtime changes are needed. All 21 complete cartridge loads pass in one native
batch, with 65 assertions, adjacent/module guards, and checkpoint restoration;
the full 440-test suite passes. Final native wording/layout and gameplay remain.
Birthday fields `34/35` are separate item
slots, not these free fields. Other date preparers and native calendar years
outside 2000–2032 require their own audit.

Twenty-seven individually approved resident conversations add the speaker's
catchphrase under a separate [hash-bound contract](../specs/REFERENCE_CATCHPHRASES.md).
The native appearance request/initializer preserves the actor through window
`2E0` to client `20`. All 27 actual initializer/DMA loads and field dispatches
pass, with distinct long defaults, custom input, null-client clearing, complete
source retention, and guards. This is not ordinary NPC traversal or final review.
The remaining thirteen catchphrase-only rejections have changed choices/actor
commands, blank native records, or different topics; do not import them as an
unrestricted class. Broader missing-field, control-signature, and unconfirmed
identity batches remain, alongside final native festival review and gameplay.

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| R01 | English runtime substitutions, including town/date/time formats | active | Town, seven message date/time fields, AM/PM, ordinary resident year/month/day/leap-month preparation, and all 33 birthday-request fields pass targeted checks; normal birthday entry/gifts, other UI callers, and out-of-table native calendar dates remain |
| R02 | Choice strings beyond ten bytes | active | All 460 choices have candidates; nine original labels retain native meanings, 167 dialogue approvals preserve native menu order, and twenty-six contextual mappings retain answer indices/actions; twenty-byte capacity, thirteen long DMA loads, four rows, insertion, and cancellation pass targeted MIPS tests; further contextual labels, full review, and actor-specific runtime paths remain |
| R03 | General strings and UI caller capacities | active | Thirty-four direct calls inventoried; ten-byte default catchphrase display passes all 216 default loads and main insertion with unchanged saved bytes; gyroid owner-message pixel wrapping and native insertion pass with unchanged saved/editor limits; longer gyroid default/custom storage, ambiguous borrowed phrases, shared choices, mail, and shop destinations remain |
| R04 | NPC and item names | active | 178 six-byte villager names and all native loads pass; eight-byte API covers all 216 villagers and 64 special-actor rows; main insertion, two nameplate consumers, eight rendered quads, and guards pass native tests; combined train-to-town regression passes; 242 item reference IDs occupy 779 ten-byte slots, and 771 references occupy 2,713 wider-resource slots; all 4,547 native item-ID cases have passing runs with documented initial failures; mapped-name batches pass 1,199 native calls with restored states, and full converted-name checks pass; sixteen-byte main item fields and one item-ID wrapper pass native tests; other destinations and identities remain |
| R05 | Mail, headers, footers, and NPC mail components | active | Verified 164-byte record and 10/96/16 fields; full-letter codec, formatter, immutable catalog, and restoration pass host/native tests; full snapshot reader retains all wording across pages and matches 6,398 host reference probes; actual window tests cover long classic/composite letters, complete glyph vertices, page input, and unchanged source/preferences; English ordinary scoring and distinct quest word tables pass native tests; complete-record send decoding and post-office failure retention pass 32 N64 cases, including local/visitor replies, friendship, quests, gifts, counters, and unchanged rejected records; experimental split marker is not release-approved; 59 reference parts need glyph support; complete metadata/other-reader handling, semantic identities, generation, lossless editing, normal delivery, and save/reload remain |
| R06 | Remaining GameCube controls | active | AM/PM, capitalization, protected pacing, complete choice-close handling, and pixel-space rendering pass targeted MIPS tests; random-range and wider flow coverage remain |
| R07 | Remaining message matching | active | Hash-bound identities, complete reference and native-original sequences, 41 unanimous complete-native-record aliases, and 74 separately guarded cross-bank letter references implemented; all 360 exact development-label slots accounted for, including sixteen guarded continuation allocations; 99 complete diagnostic labels covered; 91 Japanese-static-text gaps and broader matching remain |
| R08 | Review all candidate dialogue | pending | Meaning, placeholders, branches, actor arguments, and delivery reviewed; candidates are not automatically approved |
| R09 | Embedded UI, calendar, credits, and other uncovered text | pending | Inventory extends beyond the current 29 banks and keyboard UI |
| R10 | Punctuation and layout polish | pending | Preserve GameCube line/page/timing intent; review necessary N64 departures individually |
| R11 | Reported font-atlas edge defect | pending, paused by user direction | Do not resume the discarded font comparison investigation without renewed direction |

## Stability and compatibility

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| V01 | Repeatable build and regression suite | active | Verified inputs, deterministic outputs, all tests passing, clean tracked worktree |
| V02 | New-town creation through normal gameplay | active | Name/town entry, arrival, house purchase, both explanation choices, English work offer, uniform equipment, and planting completion/acknowledgement pass; meeting villagers, later jobs, and normal save remain |
| V03 | Save/reload and long names | active | Native two-bank FlashRAM writing and fresh-process reading pass all 192 synthetic stored-letter slots, complete records, and English reconstruction; normal save-menu/post-load gameplay, custom editing, longer names, and RTC remain |
| V04 | Keyboard callers beyond player/town names | pending | Catchphrases, apology, song request, mail, and board |
| V05 | Dialogues and menus across progression | pending | All control families, four-choice menus, inventory, shops, item displays |
| V06 | Travel and Controller Pak | active | Isolated native passport/stored-letter writes and fresh-process reads pass all 177 complete letters, file checksums, complete player/NPC imports, and English reconstruction; ordinary travel/storage UI, error paths, different towns, and saved names remain |
| V07 | Dates, RTC, seasons, events, and credits | pending | Event coverage and boundary dates with controlled test saves |
| V08 | Legacy glitch/crash audit | active | Paired native/reference audit identifies incorrectly labelled Pak erasure, repair, and write-failure messages; native-specific drafts retain correct conditions/actions; reported runtime glitches/crashes still require reproduction, and text corrections do not establish crash fixes |
| V09 | Four-MiB memory and resource budgets | active | 32 KiB module reservation and actual malloc arena start pass boot and town-arrival guards; linked mail calls pass separate stack/buffer guards; broader heap/graphics tests remain |
| V10 | Original hardware matrix | external validation | Real console/flash cartridge/Controller Pak evidence; emulator evidence is insufficient |

## Image and keyboard stretch goals

Work on these after the main porting effort, while inventory work may identify
the required resources earlier. The title screen is the user's image priority:
match and adapt the supplied English GameCube title artwork first. Keep other
Japanese text-bearing images in the inventory and completion requirements.

The [title source route](../specs/TITLE_ASSETS.md) records the supplied English
animated letter groups, background/trademark, and separate Press Start tiles,
with verified English data and native-overlay hashes. No title replacement is
installed. Audit native drawing/assets and convert source representation without
changing original menu, clock, save-data, or selected-player transitions.

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| S01 | Identify every Japanese text-bearing image | pending | Asset IDs, dimensions, texture formats, palette use, and in-game location |
| S02 | Match English GameCube images, including title screen | pending, title sources located | Scoped English logo/animation/background/prompt source locations and hashes recorded; native drawing/asset binding and complete source extraction remain |
| S03 | Replace images with matching GameCube artwork | pending | Preserve identical artwork where formats allow; document any necessary conversion; check N64 memory/graphics budgets |
| S04 | GameCube-style English keyboard | pending, specified | Real 10×4 grid, case/symbol pages, N64 controller mapping, all editor callers and save limits tested |

## Release

| ID | Task | Status | Acceptance/evidence |
| --- | --- | --- | --- |
| P01 | Complete coverage report | active | Token-aware inventory covers 29 banks and distinguishes candidate presence from review; embedded UI/assets, wider resources, and complete review remain |
| P02 | Provenance and redistribution review | pending | Nintendo inputs remain local; legacy permissions assessed; patch-only package |
| P03 | Reproducible release artifacts and instructions | pending | Source-hash rejection, verified patch application, checksums, install and compatibility notes |
| P04 | Final acceptance | pending | Main work, stretch goals, regression matrix, and required external validation complete |

Current observations and counts live in `PROGRESS.md`. Implementation contracts
live under `specs/`. Dated results and exact build hashes live in `WORK_LOG.md`.
Generated detailed inventories, captures, test saves, and binaries stay ignored
under `build/` and `local/`; original tools and documentation are versioned.
