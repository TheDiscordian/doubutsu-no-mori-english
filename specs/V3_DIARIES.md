# Shared diary imports

## Scope and current boundary

All sixteen GAFE01-r0 carried styles, `2B00..2B0F`, share one diary system.
`tools/v3_diaries.py` binds their official names, prices, collection/display
aliases, and complete diary consumers to the actual checked donor. The styles
remain unavailable for selection until the complete native path is installed.
A converted cover is not a working diary.

The calendar/reading/editing/storage controller and shared native-save adapter
are implemented in source and compile for VR4300. Host checks cover room surface
selection, calendar navigation, editing/privacy/capacity admission, and the
save → probe → reload path. They do not establish in-game UI operation,
native FlashRAM timing, ordinary gameplay, or hardware compatibility. ABI 322
contains menus, resident packets, room/visit hooks, save dispatch, carried readers,
complete room covers, and catalogue/scoring integration at
`build/v3-diary-category-work-01/reserved-installed-01/`. Neither patcher changes.

## Donor contract

Each of four players has twelve **monthly** pages, not a separate 992-byte page
for each day. `mDI_diary_ovl_init` selects
`entries[menu_info->data1][menu_info->data3]`; `mCD_MVPL_day` supplies the selected
month modulo twelve. Each page contains 992 space-padded game-font bytes.
The total text capacity is 47,616 bytes, independent of the chosen cover.

The owner can edit. Another player can read an unlocked diary, but cannot edit;
a locked diary rejects that reader. The owner's `calendar.edit` field is the
lock flag. `m_cpwarning_ovl.c` contains the source lock-confirmation flow and
official English prompts; use those resources when integrating the UI.

`mDI_Play_read_to_write_scroll` starts the existing donor editor with 32 bytes
per logical row and a 192-pixel display width. `edit_line$741` gives diary mode
31 rows: 32 × 31 = 992. Preserve manual newline bytes and proportional glyph
widths; wrapping must not insert, remove, or overwrite characters. The prepared
editor uses the accepted N64 keyboard's command values and 192-pixel geometry,
with a seven-row reading window and bounded scrolling. It retains the full
992-byte buffer, including the end-cursor case at capacity.

`mCD_player_calendar_c` supplies 104 bytes per player: twelve played-day words,
twelve event-day words, event flags, lock, reserved byte, year, month, and final
padding. Calendar rollovers clear relevant **calendar markers**, not diary text.
The source `m_calendar.c` defines forward/backward-time, event, and year-change
rules. `diary_calendar.c` implements them and the source calendar marker reader;
native event/date integration remains required. Explicit owner refresh clears
that owner's markers, not the current visitor's calendar. The source's internal
`clear(-1)` must not accidentally erase a visitor when opening a stale house.

Collection aliases are `30FC..3138` in steps of four. Ordinary room placement
retains the carried diary identity instead of substituting a catalogue cover.
Do not install those aliases as independently selectable furniture.

## Interaction and screen controller

`diary_room.c` follows `aMR_CheckDiaryOnMe`: a selected diary occupies a cell on
the upper foreground layer of a surface actor. It reuses the installed carrying
geometry for every surface size/rotation. The player's X **or** Z alignment must
be within twelve world units of that cell's centre. Checking distance to the
centre in both directions prevents normal edge interaction and is not the donor
rule. All sixteen styles follow this same path.

The checked native A-tap caller is `80942060`, calling `8093DB64` in the relocated
My_Room owner. The source adapter preserves the existing message/demo and short-
hold gates. Seven native updates retain the N64 interaction threshold. It checks
upper then lower contacts, requires valid actors/profiles, and resolves the house
owner by full personal ID using native `mPr_GetPrivateIdx`. Vacant houses and
failed menu opening cannot accidentally activate the supporting furniture.
The original controller handles non-diary interactions unchanged. Exact consumers,
caller bytes, and the one removable relocation are bound in the preparation.
`diary_native.c` binds the menu-open and selected-style exports to actual native
data and the compiled screen owner. The shared room hook and carried-item handling
are installed; selection remains disabled while required gameplay is unfinished.

`diary_menu.c` provides one transient controller for all covers:

- Month selection spans eleven months before/after the current month. C-up
  returns to the current month; B/Start exits.
- Day selection uses the source C-button navigation and up/down cycling through
  multiple events before changing weeks. The event provider must use the actual
  game's schedule, not advertise unimplemented GameCube holidays.
- The owner can enter editing with A/Start. Other residents only read unlocked
  pages; A/B/Start returns those readers to the calendar.
- Done opens the official Yes/Rewrite choice. B returns to the preserved draft.
  Finishing opens the official privacy question; C-left/right selects Yes/No.
- Privacy confirmation admits the page and lock together. Capacity rejection
  shows an explicitly project-authored warning and returns to the intact draft.
  Changed/corrupt source data returns to the calendar instead of overwriting it.

Native drawing, full-page keyboard handling, submenu ownership, transitions, and
sound/lifecycle adapters are implemented and linked for VR4300. Native date/event
reading and room entry are installed; participation callers remain
unfinished. Eight official prompt strings
and three project-authored error strings are
credited in `translations/provenance.json` under `v3/diary/`; preparation verifies
each source location and encoded text. Month/day artwork and event labels remain
part of the screen integration, not additional uncredited prose.

### Screen and keyboard preparation

`tools/v3_diary_screen.py` prepares one shared packet for every cover. Its current
output is `build/v3-diary-category-work-01/screen-04/`: 144,240 bytes, SHA-256
`c6ec72c0e2eb1c63a80d15b146597c8e53ddde7f026f45835c90ad37a3c9f531`.
The 148 resources and 141 display/loading lists include every month, day number,
year digit, calendar background, paper section, source control, and finish/privacy
graphic. Caller-table receipts retain actual month order, shared palettes, colours,
and month-label positioning. All 118 textures have individual official-source
entries under `v3/diary/art/` in `translations/provenance.json`. An offset suffix
distinguishes source textures with identical local symbol names.

`v3_ui_art.py` extends conversion by render category, using the existing native
command emitter and texture converters. UI contracts explicitly identify inherited
textures/combiners and state-only lists. Complete sequences preserve shared vertex
loads, native triangles, and packed Dolphin geometry. Unsupported state, unknown
commands, missing source relocations, and unloaded vertex reads reject. Direct
textures may use the full 4 KiB of TMEM; CI palettes keep their upper-half reservation.
Two-texture button graphics retain separate colour and alpha tiles. Ordinary
furniture defaults and its stricter material rules stay unchanged.

`diary_draw.c` implements the native calendar, paper, confirmation, privacy, and
warning draw paths with the converted packet. It preserves source matrices,
colours, selection geometry, and prompt text. Graphics-space checks precede drawing;
the source packet's segment binding is restored before returning. The native owner
provides projection/animation positions; the native calendar provider supplies
actual event labels/day types. Paper and text use the same absolute scrolling offset,
including during transitions. Native cursor/end-marker callbacks use proportional
positions and explicitly bind the keyboard's marker assets before drawing. These
functions are installed, but not visually verified. The compiled largest
draw frame is 304 bytes; engine callees and actual stack high-water use remain
native execution checks.

`diary_editor.c` adds mode six around the accepted English keyboard. Mode four
initializes a bounded caller buffer before the adapter restores all 992 characters,
31 proportional rows, and the preserved cursor. The new mode cannot index native
five-entry handler tables. Existing modes pass to the previous implementation.
Case/page/repeat/feedback input remains the accepted keyboard's implementation;
diary commands, including Done, go to the shared transactional controller.
Done opens confirmation without saving; Rewrite retains the draft. The adapter
preserves the native twenty-update cursor blink and recomputes the accepted
character-alteration mapping after successful commands. The owner
passes an explicit resident session through editor `data3`, with matching submenu,
owner, and input-buffer checks. Its native init/update hooks are installed.
The largest compiled adapter frame is 240 bytes, before its diary callees.

### Native ownership and prepared hooks

`diary_screen.c` owns an explicit `AFDY` mode of native HBOARD program two.
Its resident state retains the menu, draft, view animation, access provider, and
keyboard session. Calendar/read/finish/privacy views share this owner; editor
program ten, mode six, is a genuine native child. The child's pre-move/pre-draw
callbacks keep the paper active, while all input belongs to the child until
native return restores the diary owner. An A press is consumed once across the
two donor animation steps per native menu update. Prompt answers require their
initial reveal; Rewrite does not commit or reconstruct the draft. Read-only and
locked access, capacity rejection, native end/return, and invalid-session closure
retain explicit handling. Ordinary house-message mode uses the original native
constructor, dispatch, and destructor.

`tools/v3_diary_ui.py` links the owner/drawing code and prepares additive hooks
against the checked current cartridge. Output is
`build/v3-diary-category-work-01/ui-06/`: 18,416 code bytes, SHA-256
`dbb5951b0e50f1b94326ec05955062740cfe43c1f239c0a7be315bbda2782077`,
2,240 bytes of screen state, and 488 bytes of native context. Planned code/state/art reservations start at
`806A0000`, `806A8000`, and `806B0000`; each has a guard and is checked against
existing reservations plus the prepared diary save workspace. No mutable state
is hidden in the linked code packet.

The context occupies `806A8900` inside the state reservation, after the complete
screen. Transactional editing uses a separate candidate at `806D4000`, 48,048 bytes
plus a sixteen-byte guard. It cannot reuse the compressor's 120,112-byte scratch:
the preflight constructs a complete save there while reading the candidate.

The prepared HBOARD overlay is 2,304 bytes and the keyboard is 39,936 bytes.
Together they require 1,600 additional aligned menu-arena bytes. The current
arena term is `8089A860`, not an older keyboard build's bound; the proposed term
is `8089AEA0`. The accepted keyboard lives at VROM `03E70000`, with relocation
`03E80000`. The builder preserves its complete previous prefix, including accepted
graphics, changing only the init call and PLAY dispatch entry. HBOARD changes
only its constructor's init/set-proc calls; prepared owner metadata also replaces
set-proc and destructor so native child return cannot restore house-message
handling. Complete retained-prefix checks pass at two real relocation bases.
Installation reserves DMA storage and applies owner/arena updates together;
both overlays are installed in the current experimental cartridge.

Native call inspection confirms the keyboard's once-only resource initializer
does not index the mode table. Its drawing calls the parent's draw callback and
the accepted grid renderer; its PLAY dispatcher is the replaced entry. The
adapter retains blink advancement and the actual character-alteration reader
without entering native mode-six command tables. The N64 graph-thread stack is
`1800` hex bytes (`sys_stacks.h`/`sys_stacks.c`); the complete dynamic call path
and runtime high-water margin are not yet verified.

The screen builder can reuse a prepared packet when current complete resources,
generated commands, source identities, and every compiled section agree. Metadata
and renderer bindings do not force another graphics compilation. The prepared
save core and carried model remain unchanged; current carried commands and relevant
prompt provenance are checked directly rather than treating unrelated catalogue
additions as a reason to rebuild the save module.

### Native dates and entry

`diary_events.c` reads the complete 81-row native event master at `80104B60`.
Nineteen calendar rules identify actual holidays rather than duplicating their
crowd/weather/sports actors or advertising rumour periods as holidays. They retain
N64 fixed dates, recurring Sundays/Saturdays, ordinal weekdays, seasonal ranges,
and both lunar moon-viewing dates. Overnight festivities appear on their named
date rather than on the next day's midnight endpoint. The owner's birthday is
read from the actual `BD0`-byte player record, not the current viewer's birthday.
Calendar colours retain Sunday/event/current-day meanings and the donor's
birthday colour rule. Monthly results are cached; drawing does not repeatedly
decode the full schedule or change the live RTC to browse other dates.

The real native lunar conversion at `800D60E4` is guarded to years 2000–2032.
Its own lower-bound test is insufficient for its lookup table. Gregorian dates
in adjacent browsing years still work without an out-of-bounds lunar lookup.
Native Town Day and other absent GameCube-only dates are explicitly absent, not
assigned invented dates. Zero-valued optional special dates preserve the core's
original donor behaviour when actual special dates are supplied.

`tools/v3_diary_events.py` checks native decoder/conversion functions, their
complete lookup tables, and native player/date readers. Twenty labels are bound
to the single provenance catalogue. Official calendar strings are preferred;
Valentine's Day, mushroom season, and Jingle use identified official passages.
White Day, Children's Day, and the second Moon Viewing label retain the existing
explicitly assistant-authored N64 credits. This does not claim human review.

`diary_native.c` connects the real `game + 1CBC` submenu to the resident screen,
selected style/profile rows, current player/RTC, owner birthday, glyph-width
reader, and complete-save preflight. A prepared hook at `8007FA20` calls the
original live-player predicate and records the current play day only after the
native title, player-selection, demo, and player-control gates. An already-marked
day avoids another calendar refresh. The original predicate result is preserved.
The hook is installed. Event participation remains a separate actual-player
caller requirement: calendar occurrence does not set attendance. Native event IDs
cannot index the donor's differently numbered special-event flags.

The complete donor text-section direct-call inventory for
`mCD_calendar_event_on` (`0000D4A0`) contains exactly two calls:

- `001B4C90`, inside `aES2_talk_init` (`001B4C08`, 164 bytes), marks attendance
  when Tortimer's holiday conversation starts. Function SHA-256:
  `6e7d254653e58a7b937d09914bd760904523252b442a287e34cb6f5641d7b2a6`.
- `00219398`, inside `aTS0_talk_init` (`0021933C`, 184 bytes), is gated on the
  actor being Tortimer, not Copper or an ordinary exercise participant.
  Function SHA-256:
  `2a2d4d791098405e7222b4d689653c9133904e6893d3c847b68534e7a5dd55da`.

The corresponding source is
`src/actor/npc/event/ac_ev_soncho2_talk.c_inc` and
`src/actor/npc/ac_taisou_npc0_talk.c_inc` in the pinned donor checkout. The native
game lacks Tortimer; his shared event/conversation support is also required for
imported holiday gifts. Attendance therefore depends on that shared actor path,
not an unidentified native festival caller. Keep this dependency explicit while
finishing diary selection and native UI/save integration. Ordinary NPC dialogue,
scheduled events, or merely visiting a festival cannot stand in for these donor
conversations. This does not mark attendance implementation complete or waive it.

The combined sanitized host check uses actual native schedule data and the local
N64 lunar implementation, covering 420 months, boundary years, recurring events,
overlapping holidays, birthdays, style selection, real entry, and guarded preflight.
Current linked menu/visit hooks and the donor-calendar comparison also pass.
These checks do not execute native graphics, FlashRAM, or ordinary gameplay.

### Shared Tortimer conversation and attendance

`holiday_talk.c` connects the complete Ev_Soncho2 conversation state machine to
the existing holiday selector/transaction kernel and real diary calendar storage.
All 28 holiday event identities share this controller; Harvest Festival retains
its distinct message base. First/repeat visits, claimed trophies, three random
repeat messages, visitors, full pockets, and the actual handover signal retain
the donor branches. The actor chooses its reward variant once; preparing a new
conversation must reuse that variant, not reroll on each line or frame.

Preparation only selects dialogue. The actual talk-init entry marks attendance
using the actor's captured date and **donor** event ID. It does not map the donor
ID into the unrelated N64 schedule. `af_diary_calendar_event_check` reads the
same special flags and twelve-month interval as the donor, before talk-init
changes them. Visitors cannot mark a resident's calendar or receive a resident's
trophy. The separate exercise talk-init entry requires an explicit Tortimer
identity; Copper and ordinary exercise villagers cannot mark attendance.

January/February vacation branches retain their quest-start callback and the
two dates seven/eight days after the actual RTC date. Missing lighthouse support
rejects rather than pretending the quest is present. This controller does not
install a lighthouse or the exercise-card conversation. Those actor dependencies
remain required where their donor routes are used.

The handover uses the existing checked item selection and receipt transaction.
Changing players or removing the selected item cannot award or mark it. If
pockets become full after the initial dialogue check, delivery rejects and
retains the offer without awarding a trophy. Repeated delivery signals cannot
give the same reward again. This is a no-loss platform guard, not a substituted
event reward. The installed shared transport applies message/continuation,
listen/start, item/event name, handover, and camera/turn. The source actor
controller owns think/melody restoration; the actor/event owner remains unlinked.

`tools/v3_holiday_talk.py` binds the complete donor talk functions, relocations,
and pinned C references. The ordinary holiday preparation command compiles both
the selector and controller. External diary/reward calls and compiler-generated
`memcpy` remain explicit link dependencies, not guessed resident addresses.
The current prepared objects and source receipts are in
`build/v3-diary-category-work-01/tortimer-talk-03/`.
The prepared controller does not install an active Tortimer actor or event
schedule. Installed artwork, official messages, and transport are reused when
linking that controller; no import is enabled by preparation.

The sanitized connected check compiles the complete donor talk file beside the
port. Every holiday uses first/repeat/claimed/full-pocket/visitor branches and
all three repeat-message outcomes; vacation dates, duplicate start/delivery,
player/profile changes, and real calendar effects are checked together. The
calendar query separately matches the actual donor calendar C, including all
event IDs and out-of-window dates. Existing selector/handover checks pass for
the changed shared selector. These are host results, not native conversations.

### Shared official dialogue and native transport

`tools/v3_holiday_dialogue.py` converts all 28 holiday groups plus the vacation
and exercise/card conversations in one pass. Starting with 344 selector records,
following every branch adds `338E..3390`, giving 347 messages. Donor intervals
`3280..339A`, `33F4..3415`, and `3422..343F` map to native IDs starting at
`2F01`; four required choices start at `01FF`. IDs do not depend on selection
order. Unknown commands, incomplete closure, unsupported characters, and native
buffer overflow reject. All branch/choice targets are rewritten, not just the
first message selected by the actor.

Official wording, manual lines/pages, pauses, and NPC0 orders remain intact.
Redundant donor article-suppression flags are removed because native insertions
do not add articles. Two horizontal dash glyphs in `33F4` become the native
halfwidth hyphen. These changes are explicit in the 411 per-text provenance
entries, alongside the four choices, 31 ordinal dates, and 29 event names.
No new English passage is authored. The maximum expanded message is 867 bytes,
inside the existing 1,024-byte buffer; no pagination or timing changes are needed.

The ordinary four-resource text installer repacks the expanded banks into checked
free physical ROM space, preserving virtual identities and every previous text
record. Both message bounds and both choice bounds increase together. The source
event-name permutation binds to the actual donor table; Town Day inserts the
actual six-character N64 town name before the official suffix.

The 1,824-byte stateless adapter at `806E6800` and 640-byte field/ID packet at
`806E7800` fit the existing additional-NPC reservation. Registry, cane, artwork,
actor guards, and inactive flags are retained. No resident allocation or saved
format changes. The native bridge binds the transport before actor construction.

Continuation uses the actual `MainNormalContinue` function at `8009E908`, which
checks main state two and the next `7F01` command. The continuation setter is
`8009DBA4`. Message preparation uses native turn/camera/message calls; talk-init
uses ListenAble/Start. Complete item names use the selected-category reader at
`801969C8`, bypassing the old quest helper's native-ID precheck. The normal
16-byte item-field setter receives item slot zero and event slot one. The
startup-restored free-field setter receives the two four-byte ordinal dates.
Handover sets NPC1 orders `0=item`, `1=7` (PUTAWAY), and `2=0`; only the existing
reward transaction inserts the item and marks the trophy. Invalid fields or
message IDs reject before the first demo mutation.

The current build is `build/v3-diary-category-work-01/tortimer-world-02/`.
Focused checks compare every converted message token against the official source
after reversing declared adaptations, inspect installed resources/bounds/guards,
and connect the actual talk/reward/transport code under sanitizers across all 28
events, visitors, full pockets, duplicate delivery, and dates. Browser/offline
empty, mixed, and all-supported composition agrees. Individual transport frames
are at most 96 bytes, before callees. Native conversation execution and complete
dynamic stack use are not established. Event/world/cleanup and separate card
integration remain required before actor or diary activation.

### Tortimer artwork and native actor connection

The shared streamed-NPC converter prepares Tortimer's complete model at
`build/v3-diary-category-work-01/tortimer-art-04/`: 9,456 model bytes and 4,128
texture bytes, within the native `2800`/`1620` hex NPC buffers. All 325 vertices,
256 ordered faces, 26 joints, 14 displayed parts, twelve body tiles, and eight
eye expressions are retained. Donor draw rows 348, 354, 358, 365, and 373 share
these exact resources. No character, native model, or original texture is replaced.

`tools/v3_npc_stream_art.py` extends the existing mesh conversion rather than
flattening the rig. Each material loads its complete CI4 texture. Body textures
use segment seven; the current eye/mouth use segments eight/nine. Source mirror,
wrap, explicit extents, alpha-to-coverage, and double-sided parts are retained.
The mouth's reference to the later head matrix is valid: all CPU-generated
matrices exist before the RSP executes the task. Pipe synchronization precedes
each material replacement. Existing atlas conversion retains its checked output.

Native drawing preloads **4 KiB**, not 2 KiB: `FD900000` and `F3000000/077FF000`
describe 2,048 16-bit transfer units. The converted bank stores its palette first,
body at offset 32, expressions next, and checked final padding. The entire native
preload therefore stays within the bank without dropping any source pixels.
Per-material loads replace that temporary atlas before the actual mesh draws.

`npc_stream_draw.c` retains the six-argument skeleton ABI and chains through the
installed accessory entry `80473100`. Its actor texture fields are **segment-six
offsets**, not CPU pointers. The actual bank comes from actor `+708` and the native
`game + 110 + slot * 54` object record. The adapter checks bank identity/readiness,
size, expressions, and command capacity, emits the current body/face bindings,
and restores both opaque and translucent segment state. Ordinary NPCs take the
unchanged accessory path. Native record generation retains donor flags, scale,
collision dimensions, and full voice 281. The additive registry assigns `D090`,
profile `CC`, and object banks 448/449 without reusing a native identity.

`tools/v3_npc_stream_runtime.py` checks both complete current-ROM renderers and
their existing accessory calls at `80978654` and `8099A2E0`. Only the JAL changes;
the actor argument in the delay slot and both relocation tables remain. The
prepared VR4300 object at `build/v3-diary-category-work-01/tortimer-draw-04/`
has a 120-byte maximum local frame. The installed registry supplies its record
lookup and links the adapter into both owners. No new native fixture is run and
the existing diary test budget remains exhausted.

Six focused source/current-cartridge/host checks pass: complete pixel and
ordered-face preservation, texture-transfer bounds, native draw/config records,
both caller patches, all expression choices, ordinary fallback, original argument
forwarding, insufficient-space rejection, and state restoration. The shared
atlas converter's existing checked command output is unchanged. These checks
do not prove native rendering, animation, conversation, or playable diaries.

Continue the same category with the actual actor and event connection. The native
NPC prefix is `93C` bytes; do not cast the donor's `994`-byte NPC onto it. The native
clip pointer is at `80136EEC`, installed by `80980D74` in the retained NPC owner.
Its constructor map in `build/disassembly/npc-animation/code.asm` provides:

| Native clip offset | Consumer |
| --- | --- |
| `BC`, `C0`, `C4` | Birth check, constructor, destructor |
| `C8`, `CC`, `D0`, `E4` | Save, init, move, draw |
| `F8`, `FC`, `100` | Action request, head request, talk demo |
| `104`, `108`, `10C` | Animation init, schedule change, destination position |

These offsets are not the donor clip layout. The cane uses the donor's shared
`aNPC_SUB_ANIM_TUE` channel and `cKF_ba_r_npc_1_tue1` (64-byte NPC motion record,
donor animation index `F3`), not a static hand pose or an assumed identical native
index. The registry, descriptor chaining, full voice, model, textures, and drawing
adapter are installed. The full cane resource and its native animation caller
are installed. Event scheduling, official messages/demo transport, and the
exercise-card path remain unconnected. Reuse the installed resources and 28-event controller
while finishing those consumers; no diary selection is enabled.

### Additive actor allocation and complete resource loading

The shared builder's `--npc-registry-art` path installs the actor registry,
allocation/free, both drawing callers, complete model/texture banks, full voice,
and checked startup together. Current preparation/build is
`build/v3-diary-category-work-01/tortimer-installed-03/`, ABI 313. The 64-KiB
packet occupies `806E4000..806F4000`; its code occupies 3,984 bytes. Registry,
descriptor, profile, drawing, and stream records sit in its checked record area.
Two actor slots start at `806F0000`, each with 16-byte ownership and tail guards,
a 2,612-byte actor, and alignment padding, for a total stride of 2,656 bytes.
Native allocation and cleanup stay unchanged for ordinary NPCs. New cleanup
retains the actor body because the native caller reads its name after release,
and handles the resident descriptor's loaded count exactly once. Profile drawing
stays null until the native init installs the ctor's draw callback.

`D090` and profile `CC` identify the donor's `D074` Ev_Soncho2. Native no-demo,
tent, balloon, and camper reservations are retained. Runtime flags distinguish
implemented and selected; both must be set before allocation. Both stay zero,
and lifecycle fixups stay unresolved while the actor providers are unfinished.
Installing the registry is not a completed actor, event, or diary import.

Object banks 448/449 reference complete artwork at virtual `03FE0000`/`03FE4000`.
Their physical extents are allocated by the existing guarded ROM allocator, not
inside the nearly full item-data blob. The object-status bound, table, and main
startup header all use capacity 450. Existing growth/selection data immediately
after the table remains intact. Neither art conversion nor a DMA-directory row
is duplicated or repurposed.

`npc_dma.c` handles these registered ranges inside the ordinary DMA worker.
The original sync/async request functions and completion notifications remain.
The runtime hook replaces only the worker call at `80026A24`, preserving its
delay slot. It is installed after the packet's complete transfer/CRC/cache
verification, never placed in boot ROM where it could run before loading.
Unknown requests follow the original processor. Crossing a bank, invalid RAM,
misalignment, overflow, and physical-transfer failure take the native error
path rather than acknowledging an unperformed transfer. Audio DMA is separate
and unchanged. The physical reader, complete processor, and complete worker
are checked against the current cartridge before installation.

Startup loads seventeen packets in 644 of 688 reserved bytes and then enables
the checked object dispatcher. Native startup/execution remains unverified.
Four focused tests cover installed code/resources/CRCs, normal fallback,
inactive/full/damaged allocation, matching cleanup, full voice, drawing records,
whole/partial DMA and failed requests, and startup failure before execution.
The existing private browser/offline check agrees for empty, mixed, and all 191
supported choices on this build; diaries remain unavailable.

The shared keyframe converter preserves the entire 64-byte NPC motion record,
not just its 20-byte animation prefix. The cane's 26 joint flags, 54 key counts,
108 key triples, and 27 constants occupy 912 aligned bytes with the header.
Start/end frames 1/29, repeat mode, morph -5, and null face/effect/audio programmes
are retained. The resident header is `806EF348`; arrays use checked resident
addresses. Non-null dependent programmes require explicit conversion and reject
instead of being dropped. Ten shared converter checks pass, including unchanged
ordinary keyframe outputs. The runtime caller uses the installed motion services
described below.

### Shared native motion services

`--holiday-actor-services` connects the motion adapter through the shared builder,
using the existing registry packet rather than allocating or converting more art.
The motion resource receipt is `build/v3-diary-category-work-01/tortimer-services-03/`;
the current proposal retains this complete code and resource path.
The 2,016-byte adapter begins at `806E6000`; the remainder of the actor-code
reservation contains the dialogue code/fields described above, with remaining
space through `806EE000` for the event/actor bridge.
All packet bytes outside that code remain unchanged, including inactive profile
flags, original registry code, complete cane data, and actor guards.

The outdoor animation entry at `809749D0` dispatches through a scoped wrapper.
Ordinary actors enter the original function through a checked prologue trampoline;
the continuation is resolved from the live clip. For the owned Tortimer subtype
three, the wrapper temporarily hides the unsupported native table index, retains
all original main/face initialization and native bank reference counts, restores
the subtype, and initializes keyframe `354` from the resident cane's full control
record. Native joint tables match the donor: joints 18–21 use the cane channel,
and 23–24 use the speaking channel when appropriate. The ordinary animation-bank
references remain valid for playback and cleanup. Wait/clap indices 5/67 are
verified against every donor keyframe array and control field, not inferred from
matching index numbers.

Walking uses native schedule four with scoped decision/init dispatch. The donor's
six-of-ten walking branch cannot become running; fatigue, sleep, turn continuation,
collision/range, destination attempts, interrupts, and request priority are
preserved. Starting on a block edge refreshes home X/Z and block-centred bounds,
retaining home height. Unexported helpers resolve relative to the live outdoor
schedule export. Exactly two native relocations are removed for the replaced
decision call and init-table entry; all others remain.

The lifecycle controller reads `game_GameFrame` at `80145048` once per actual
native think update. Timers use elapsed 60 Hz ticks, including the transition
tick and residual time on repeated clapping, while native movement/collision and
positioned audio still execute once per world update. GameCube initialization
uses frame divisor one; N64 initialization uses two. Source/timer comparison
checks this adaptation; native wall-clock execution is not claimed.

The sanitized movement adapter is compared with the complete donor decision
function. The existing complete donor-think comparison covers elapsed-tick wait
and repeat boundaries, alongside the connected conversation/calendar/handover
check. Current installed code/relocation/trampoline/guard/resource checks and
empty/mixed/all-supported browser/offline composition pass. No additional native
fixture is run, no diary is enabled, and no save format/profile changes.

### Connected holiday movement and lifecycle bridge

`holiday_actor.c` implements all fifteen Ev_Soncho2 think states against the
existing conversation/calendar/reward controller. It preserves sports-field
selection, active-runner tracking, shrine-relative turn/walk/wait routes, tug
animation and positioned clapping, vacation deletion, and the countdown's
captured-date correction. Request priority remains the native service's decision.
Reward variants are chosen once for the actor; requesting/preparing dialogue does
not grant an item or record attendance. Dialogue consumes RNG only in the donor's
random branches. Ending a real demo restores the recorded movement state and
the conditional melody-restoration callback. Construction refreshes the active
resident's calendar only; source player `-1` does not mean all four players.
Visitors leave resident calendars unchanged.

`holiday_npc.c` supplies the N64 lifecycle and primitive callbacks through the
live clip, rather than calling unrelocated overlay addresses. Native special
think/schedule indices are 8/5; the donor's indices 9/6 are not passed through.
Think and schedule callbacks live at `7A4` and `7C0`, interrupt flags at `7A8`,
action/step at `7C5`/`7C6`, destination at `8BC`/`8C0`, and talk request at `91C`.
The actual NPC0 delivery signal and native SPEAK/TALK checks reach the shared
controller. Full-pocket or stale-profile delivery stays pending instead of
silently completing. English message/continuation and handover callbacks use
the installed transport described above; event/world providers remain required.

The actor's complete o32 size is `A34` hex (2,612 bytes). Native
`Actor_malloc_actor_class` sends D/E identities to clip `0C` without a heap
fallback. That allocator at `80980830` rejects sizes above `960` hex (2,400
bytes). Registration must therefore install a matching additive allocation/free
path, not merely enlarge the profile's size. Do not grow the nine original slots
or write the new transient state beyond an original slot. The existing native
free path also routes D/E identities through clip `10`.

Preparation at `build/v3-diary-category-work-01/tortimer-dialogue-02/actor/` contains the
shared controller and native bridge, with maximum individual frames of 88 and
144 bytes respectively. Their complete dynamic stack and native execution
remain unverified. Cadence adaptation has source and host evidence above.
`tools/v3_holiday_actor.py` checks all 37 complete donor actor
functions, relocations, complete actor data, and current native request/think/
schedule/constructor dependencies. The 15-state controller and the real
conversation/calendar/reward functions pass one sanitized combined host check;
the native bridge is compiler/source checked, not executed. No native fixture is
started and the exhausted diary title-fixture budget is unchanged.

`af_holiday_npc_bind` and `af_holiday_npc_unregister` are installed in the shared
placement/observation packet. `af_holiday_npc_event_world` supplies actual special
dates and saved vacation state from the shared state packet. The full lifecycle
is linked against these installed exports, with all four profile callbacks bound.
The native calendar caller is installed; activation remains gated on required
event owners and the calendar behaviour choice.
The native world wrapper, saved reward bindings, and full-voice resource check
are implemented below. The installed dialogue/continuation, walking/cane/resource
exports, and elapsed-tick controller are reused; allocation and drawing are
already connected. The separate
exercise/card route remains required.
These are remaining consumers of the same diary category, not new per-event
tasks. Keep the existing art, draw, and conversation objects; link and install
the connected path before enabling diary choices.

### Live player and reward connection

`holiday_world.c` links the complete movement, conversation, reward, and calendar
kernels to real N64 player/inventory/trophy readers. The shared actor-service
refresh installs this 13,072-byte module at `806E8000`, reusing the existing NPC
packet and leaving its registry, cane, graphics, pool, and guards unchanged.
The 370-byte source reward table is at `806E7B00`; the 536-byte `AFHW` destination
map is at `806E7C80`. This map contains all 65 source candidates, checked against
the installed inactive records, not merely the currently selectable catalogue.
No record is promoted by installation.

The stable registry maps source `1FC0` to additive `3C94`. Source diaries map to
carried `2B10..2B1E`, sharing their respective cover/profile selections; the donor
New Year's selector still has its fifteen-style range. The sixteenth diary is
not silently added to that source distribution. All ordinary furniture rewards
use their canonical imported IDs. Runtime lookup requires matching index/item
identities and enabled fields in both the 80-byte profile and 32-byte metadata
record. A diary also requires the correct carried-parent field. Disabled or
unknown candidates return no reward; they never fall through to a native item
with the same numeric ID. Fixed/gender rewards do not consume RNG; source-random
groups select uniformly among their selected candidates.

World binding reads the actual RTC, player number (`80136EA3`), active pointer
(`80136FD8`), and gender (`PrivateInfo + 10`). The four resident records start at
`80126EC0`, stride `BD0`; visitor four must point to `g_foreigner_private` at
`801439A0`. Every free-slot, trophy, and handover callback rechecks pointer/slot
identity. An active conversation cannot transfer to another player. Visitors
retain the official visitor dialogue without altering a resident's diary,
inventory, or trophy state.

The ordinary free-slot reader is `800B83D4`; handover uses `800B8B8C`, including
the installed wrapped-present adapter and collection hooks. Its true success
result precedes the saved trophy mark. The reward module calls the installed
`af_v3_reward_flag`, preserving the four independent 12-byte saved flag records.
No separate insertion, fake animation-completion timer, saved-format change, or
new state allocation is introduced. The native lifecycle wrapper calls the
world binding and full registry/voice checks; its prepared object is
`tortimer-world-02/actor/holiday_npc.o`, SHA-256
`44a1c1cd50bf0ddaccae2dc2881553a7b6a0d3d39ff328ea5daaa69d73488035`.
Maximum individual frames are 144 bytes for the controller/bridge and 128 bytes
for world binding, before callees. Actual stack high-water use remains unverified.

Remaining owner connections share one category task:

- Bind actual event state to `event`/`field_event`, shrine position, running
  athlete, melody restoration, and cleanup. `m_soncho.c` prioritises active
  events except autumn fishing, then autumn fishing, January/February vacation,
  and morning exercise. Date occurrence alone is not native RUN/SHOW state.
- Reuse the installed native event directory/campsite infrastructure: 128 index
  entries, 64 today slots, and 80 manager references. Shared shrine/wandering
  callbacks and the schedule caller are connected; dedicated owners remain.
  Camper event 70 stays reserved.
- Bind the installed shared shrine and wandering owners from `ac_event_manager.c`
  (`soncho_start/stop/in`, `sonchowandar_start/stop`) to native placement. New Year's, sports,
  cherry blossom, meteor, harvest moon, and Harvest Festival have event-specific
  owners; New Year's cleanup targets Ev_Miko. Sports cleanup selects the active
  ball-toss/foot-race/tug owner, not an arbitrary holiday row. Halloween spawns
  `SP_NPC_SONCHO_D079`, not the ordinary Ev_Soncho2 identity.
- `af_holiday_npc_event_world` supplies the actual Town Day/harvest dates and
  vacation-state callbacks. Zero special dates mean absent events. It must not
  invent saved dates, start an unsupported lighthouse quest, or duplicate the
  already-connected player/reward binding. N64/GameCube calendar differences
  need the specified real behaviour choice, not mismatched native event IDs.
- Connect the separate Tortimer exercise/card actor and its actual talk-init
  attendance gate. Neither an exercise villager nor the ordinary police actor
  substitutes for that source gate.

Focused cartridge and manifest checks pass. One sanitized host test exercises
the actual world/talk/reward/calendar/flag implementations: all 65 mappings,
128 handovers, four-player isolation, visitors, full/stale inventory, repeated
delivery, invalid dates/identity, and resource gates. Inventory calls are host
doubles; these are not native gameplay or save-I/O results. Browser/offline empty,
mixed, and all-191 composition agrees, with all diaries still unavailable.
No native fixture is attempted. The existing title-fixture result stays open.

The shared capacity manifest tracks the complete appended choice bank and table.
Its legacy record is accepted only when exact predecessor hashes and the one
declared reader-bound change reconstruct the checked old reader; current bytes
must then match the declared new resources. New builds store the updated record
and validate it again. Unknown resource/reader changes still reject.

### Event schedule and owner lifecycle

`holiday_events.c` supplies the connected scheduler and owner controller at
`806EB400` inside the existing NPC packet. The complete code is 3,824 bytes;
the 812-byte `AFHE` source packet is at `806ED800`. The native directory bridge
also uses this packet. No allocation, profile bit, saved format, or artwork
changes to this packet. The current build is
`build/v3-diary-category-work-01/reserved-installed-01/`, ABI 322; its additional state
packet and save extension are described below.

`v3_holiday_events.py` derives all 49 relevant rows from the complete checked
GAFE01 schedule and all 44 associated ownership records from the relocated
event-manager directory. The data retains source ordering, dates/hours, the
28-event actor priority, callback presence, and the distinct shared shrine,
wandering, Halloween-costume, and dedicated event owners. Nineteen complete
binary source functions are checked. Null source callbacks remain null; a
dedicated callback is an actual required binding, not a successful no-op.

Planning preserves equinox replacement, weekly/day-after encoding, Town Day,
lunar dates, inclusive hours, daily exercise, and overnight/year boundaries.
Father's Day and Officer's Day suppress their overlapping fishing appearance.
The caller supplies actual equinox/lunar/town dates and lighthouse availability;
the scheduler does not create those saved values or start a vacation quest.
Bridge-event preemption still belongs to the native calendar adapter. A source
working-player gate returns no events. Insufficient output capacity or invalid
inputs leave the destination unchanged. The 48-row caller-owned planner feeds
the separately checked 64-row native directory; their row layouts differ.

Owner start/stop, acre entry/exit, keep flags, and placement/culling outcomes feed
RUN and SHOW separately. Being on the calendar never implies either state or
diary attendance. Failed search/reservation sets ERROR, whereas the source's
outside-field early return does not. An actor appears only on a successful
native show callback; delayed culling leaves SHOW set. Priority and cleanup
match `mSC_get_soncho_event`, `mSC_get_soncho_field_event`, and
`mSC_delete_soncho`, including delayed autumn-fishing priority, New Year's Miko
cleanup, and sports-owner SHOW priority. The native death-notification helper
at `800814B8..800815F0` preserves matching placement coordinates before setting
STOP and the cleanup countdown; its caller must use the verified destination
event identity, not the donor number.

Two current checks pass: source/current-cartridge preservation, and a sanitized
connected calendar/owner/conversation/attendance/handover check. The complete
donor priority and cleanup functions execute beside the port. The current
browser/offline empty, all-supported, and mixed compositions also agree.
Host event/placement services are doubles, not native gameplay. The maximum
individual scheduler frame is 656 bytes, with a 56-byte decoder before further
callees; actual native stack use remains unverified. The native schedule caller
and special-state persistence are installed below. Dedicated actor owners,
calendar behaviour choice, exercise/card integration, and actor activation remain
unfinished. No native test budget is reset, no
diary is selectable, and neither patcher deployment changes.

### Native event directory connection

`holiday_native.c` occupies 1,360 bytes at `806EC300`. Version-one identity maps
at `806F1A80` assign all 44 sorted donor owner IDs to native IDs 71..114. Native
0..69 and camper 70 remain independent. The mapping does not depend on selections
or daily schedule order. The 128-byte forward and inverse maps are checked
against the complete source-derived owner set before installation.

The native 16-byte row layout is `type, hours, begin, end, status, reserved`, not
the portable planner's 12-byte layout. Sixty-four rows at `806F1500` and eighty
manager references at `806F1900` fit after both guarded actor slots and before
the packet's final guard. All 21 native base consumers and four end consumers
move together: initialization, four-row reset, slot admission, hourly update,
special insertion, status readers/writers, cleanup, and debug display. Both
cleanup loops include all mapped IDs. The adjacent original index initializer
stays untouched; the existing campsite wrapper clears the live 128-entry index.
The camper's reader moves with the array and accepts all 64 slots.

All three manager reference readers use the resident array. Their six original
HI/LO relocations are removed, so loading the owner at a different address cannot
move those resident pointers. All other relocated bytes and the 29 existing
owner controls are retained. The manager collector uses the current control
pointer directly and tests capacity before its store; the taken branch's delay
slot only calculates an index. Counts 80 and above cannot write past the list.
The storage-only owner prefix is 40,048 bytes; the connected placement directory
extends it as described below while retaining this complete prefix except for
the two control-base pairs and control count.

`af_holiday_native_merge` validates the complete directory, source identities,
unique plan rows, flags, and free-slot count before any mutation. Failed admission
leaves native rows, index, and count intact. Existing events retain their live
flags; planned rows add hours/dates/EXIST only. The native hourly/acre logic owns
ACTIVE. Snapshot/current/field/cleanup readers translate native IDs back to donor
IDs and preserve the native ERROR masking rule. Death notification calls the real
`800814B8` helper with the mapped identity. New Year's Miko deletion remains an
explicit separate owner action, not an ordinary notification substitute.

The compiled schedule bridge connects the installed source planner to this native
insertion path. Its live caller remains unbound pending actual special dates,
vacation state, calendar behaviour selection, and complete owner callbacks.
Imported keep flags have separately owned storage/reset; new owners never index
unknown native keep-array padding. Installing storage and the bridge does not activate actors or diary
choices, fabricate missing dates, or count scheduled events as attendance.

Three focused checks pass in `tests/test_v3_holiday_native.py`: complete installed
reader/relocation retention; sanitized all-44 insertion alongside twenty retained
native rows, overflow/malformed rejection, status, scheduling, and cleanup; and
the actual patched MIPS collector block at capacity boundaries, including branch
delay execution. Host death notification is a double. Current browser/offline
empty, mixed, and all-191 compositions agree. Maximum individual bridge frames
are 608 bytes for scheduling and 600 for status snapshots, before callees;
native stack use and gameplay remain unverified. No native fixture is attempted.

### Native placement and shared event owners

`holiday_placement.c`, its native adapter, and the shared NPC observation/cleanup
providers occupy 4,448 bytes at `806F1C00`.
`holiday_owner.c` occupies 1,008 bytes at `806EC900`. Both use the existing
64-KiB NPC packet; the artwork, movement, dialogue, world/reward, event kernels,
actor pool, and guards are retained. Thirteen complete donor functions and the
native field/manager dependencies are checked by `v3_holiday_placement.py`.

The shared search preserves the three source fallback phases, deterministic
source-ID seed, selected-shrine margin two, and wandering margin one. It excludes
the native town's four actual landmarks; the N64 has no donor island dock to
exclude. Native coordinate structures are `z,x`, including by-value parameters,
not the donor's `x,z`. The manager's shrine is at `22C/230`; `214/218` belongs to the pool.
The shared checked decoder retains separate pool/station/shrine/home exclusions.
Real native field/collision/NPC functions supply candidate units and terrain.
Appearance uses the donor's ordered 3×3 foreground/height-gap
search, then the ordinary unit-search fallback, real ground flattening, and the
NPC clip's actual nine-argument spawn function. No appearance in the entering
acre returns two; actual spawn failure returns zero. STOP controls culling.
Invalid coordinates reject before native terrain access. Overlay-private helpers
resolve against the checked currently loaded manager, not its link-time address.

The complete native event-owner directory has 73 rows: the 29 existing controls,
including camper 70, followed by all 44 donor owners using fixed IDs 71..114.
Both manager directory-base pairs and its control count refer to the new table.
Copied original callbacks retain independent relocations; resident imported
callbacks do not receive overlay relocation. Native clock/acre dispatch remains
responsible for RUN and SHOW. The 21 shrine/wandering owners connect start,
placement, appearance, stop, and culling through that native dispatch. No diary
attendance comes from scheduling or spawning alone.

Eight bytes at `806F1B80` hold imported keep flags indexed by `native_type - 71`.
The complete native common-data reset at `80078A10..80078A88` retains its existing
clear, preserved byte, field initializers, and private-info call, adding two
inline stores to clear those eight bytes. It calls no early packet code. Original
keep routines and storage remain unchanged. The fixed actor-name pair at
`806F1B88` maps ordinary source D074 to D090; the D079 costume destination remains
zero until its distinct actor is connected. A missing/inactive actor or dedicated
callback rejects rather than substituting a different actor or returning success.
The donor's `dpppp` alias is only a developer-arrow reader; real common placement
storage owns actor position. No new debug-arrow subsystem is claimed.

`tests/test_v3_holiday_placement.py` checks complete donor-search agreement under
54 host conditions, all 21 shared owner paths, nearby search/spawn/culling,
reservation and coordinate failures, actual compiled packet/linker bindings,
complete native/camper relocation retention at two bases, allocation metadata,
and execution of both original and changed common-reset instructions. Native I/O
is doubled in host checks; native gameplay remains unverified. Current private
browser/offline empty, mixed, and all-supported compositions agree. Saved format
eleven and selection flags stay unchanged; all sixteen diary choices remain
inactive. The calendar caller and state/provider connections are installed below.
Dedicated/costume/exercise actors, calendar behaviour choice, and activation remain
part of this same category task. No native fixture is restarted.

### Shared NPC observations and cleanup

`holiday_observers.c` implements `af_holiday_npc_bind` and
`af_holiday_npc_unregister` in the existing placement packet. The event and
field readers call the installed native-directory mapping at their actual use
sites; native events cannot masquerade as donor identities. The world adapter's
existing reward-variant callback, motion, and dialogue services are reused.

The real shrine helper is `8008E8E0..8008E9C4`: native block kind four, shrine
foreground `5825` or dummy `F0EF`, and centre-position conversion. Its output
is the source's intentional `x,z,y` short-array order. Race tracking reads mapped
donor event 15, saved record eight, big-endian flag `0400`, and first-runner
coordinates at offsets `0A/0C`. The imported race owner must supply that record;
the original native race (event ten) does not satisfy this dependency.

Ordinary cleanup uses the installed source-priority selector and mapped native
death notification. New Year's special cleanup searches actor part three for
the additive reserved Miko profile `CD`, name `D091`, instead of native profile
`84`. The reservation is version two of `SPECIAL_NPCS`, not an installed Miko
actor or claim of complete New Year ownership. The complete checked donor
Tortimer actor initializes `melody_inst` to zero with no nonzero assignment;
conditional restoration therefore performs no write.

The native clip constructor at `80980D74..80981018` places its 284-byte table at
linked `80983A80` inside the outdoor NPC owner's BSS. Metadata at `80101090`
supplies the actual load address. Validation checks that allocation and the exact
live table pointer before dereferencing, then checks eleven lifecycle/movement/
draw entries against that relocated owner. Heap addresses or the indoor clip
cannot satisfy the binding. Full actor/resource validation remains the existing
world service, rather than a second model/voice checker.

The installer refreshes only the checked placement/observation and owner code
regions. Installed manager callbacks must keep their addresses; manager data,
relocations, reset code, resource packets, guard words, save profiles, and artwork
are retained. No additional resident allocation or save-format change is needed.
Three focused current checks cover the corrected landmark decoder, all mapped
observation/cleanup paths, clip bounds/rejection, source/native dependencies,
and retained cartridge data. Native I/O is doubled in the sanitized host check.
Browser/offline empty, mixed, and all-supported outputs agree. The event-world
provider and native calendar caller are installed below; required dedicated/
costume/exercise actors, calendar behaviour choice, and activation remain unfinished.

### Saved holiday state and connected lifecycle

`holiday_state.c` supplies saved Town Day and the complete lighthouse quest
state, following the checked `m_soncho.c`, `lb_reki.c`, and town initialization
source. Town Day is chosen once from the donor's thirty July dates excluding
July 4. Harvest Moon uses the complete 2002–2030 source table; the native lunar
fallback is bounded to its actual 2000–2032 table. Equinoxes use the source
formulas. The shared clock provider does not clear vacation state while working.

The quest preserves day zero, the seven working days, the return period through
day seventeen, the six-o'clock rollover, entry hours, each player's contribution
and completion flags, and the donor's completion/check order. Player deletion
removes that player's contribution flag, not the town's quest. Date/time changes
follow the source availability check. These helpers are not a claim that the
lighthouse building or its interaction owner is implemented.

`tools/v3_holiday_state.py` installs one guarded 32-KiB packet at `806F4000`,
links the complete prepared NPC lifecycle, and redirects 25 public entries in the
existing diary/save module. All old callers and function pointers keep their
addresses; only their eight-byte entry windows change. The original NPC packet,
profile bits, calendars, pages, buffers, and canonical codec remain in place.
Startup validates and loads all eighteen packets before initialization. The
actor descriptor's four callbacks are bound, but selection flags stay zero until
the remaining owner connections work.

The complete checked native scheduling function is `8007F358..8007F6A0`.
Its call at `8007F630` reaches `af_holiday_calendar_before_cleanup`, inside the
unchanged native working-player gate. The wrapper plans the complete source
batch through the installed shared directory bridge, then retains the existing
camper scheduling and native first-entry result. Native cleanup and hourly
activation still own event status. A disabled actor selection changes no dates,
RNG state, or daily records. The caller does not bypass the unfinished event-owner
or behaviour-choice requirements to make imports selectable.

`tests/test_v3_holiday_state.py` uses the existing save-device doubles with
address/undefined sanitizers for actual diary editing/preflight, full-town/
console/diary saving, format-eleven migration, and legacy-reader rejection.
It covers source dates, quest boundaries, four players, deletion, working/visitor
rules, and malformed state. Native RTC/RNG/lunar/FlashRAM calls are doubles.
The current-cartridge check verifies the new packet, retained data, all entry
redirects, and startup descriptor/CRC. Browser/offline composition agrees for
empty, mixed, and all-supported selections. No native fixture is restarted.

### Reserved layouts and dedicated owners

`tools/v3_holiday_maps.py` converts the complete donor event-layout graph and
compiles all 14 dedicated owners through one native adapter. The shared runtime
installer installs the complete code and layouts in ABI 322 at
`build/v3-diary-category-work-01/reserved-installed-01/`. The manager's dedicated
callbacks remain disabled while the required services are unfinished.

The source directory contains 17 entries, including the explicit null Halloween
map. Its 52 variants cover all seven pool shapes and 341 logical placements.
Shared fishing layouts are deduplicated without removing logical entries.
Every source pointer, relocation, resource extent, NPC mask, uniform, actor/
decoration identity, and unit position is retained and checked. `AFHM` is a
1,496-byte, big-endian packet with a 16-byte header and 20-byte directory rows;
each placement is a source name followed by X/Z bytes. Source IDs are never
implicitly treated as installed N64 IDs. Shrine layouts ignore pool shape;
pool layouts reject an invalid shape instead of selecting another arrangement.

The generator preserves 39 complete donor functions for the 14 owners, including
the shared sports creation/deletion and culling functions. The only structural
adaptation passes explicit context into the source's no-argument sports cleanup.
Generated donor C stays in ignored build output with complete source/binary
receipts. The committed compatibility layer routes primitive operations through
caller-owned state; it does not cast donor manager/common structures onto N64.

`holiday_dedicated_native.c` connects mapped status/keep operations, real native
landmarks, reserved placement, foreground setup/removal, actor creation, effects,
and both acre-entry paths. Five complete private owner functions and six complete
core functions are checked before binding. Private calls resolve from the loaded
manager descriptor rather than calling link-time overlay addresses. Missing
identities reject explicitly. Strict foreground deletion retains placement and
sets ERROR on failure; the donor's separate sports-cleanup variant clears its
placement after the removal attempt. Those behaviours are not merged.

The combined module is 10,288 bytes at `806F8800`; the map packet resides at
`806FB800..806FBDD8`, below existing harvest dates and the packet guard. The
installed 4,480-byte
placement module retains the shared search/observation implementation and adds
an explicit placement-ID appearance entry. Its corrected game-context pointer
is `8010EF90`, verified against both the native symbol and the signed-offset load
at `8095E0D0`. The shared owner and saved-state lifecycle bind the five current
placement exports; installation verifies their unchanged public entries.
No caller retains a moved placement address. The complete packet occupancy,
dates, guards, bootstrap transfer/CRC entries, and unchanged save/profile fields
are checked together. No additional resident allocation is required.

The adapter still requires checked installed identities, imported scene fade
and escape-position handling, persistent imported common state, and live manager
dispatch. The announcement reader and native acre lock are bound below; those
completed components do not finish the whole scene-transition path.
Control/effect identities must name their actual converted behaviour; a native
counterpart's integer is not a completed imported controller. These requirements
include costume, exercise/card, Miko, race-state production, event participants,
and the specified calendar behaviour choice. No owner activation or diary
selection is claimed until the connected path works.

`tests/test_v3_holiday_maps.py` checks the complete layouts, all generated owner
callbacks, actual adapter dispatch, distinct cleanup semantics, unavailable
identities, indoor gates, malformed layouts, and native/source game-pointer
agreement. The host check uses address/undefined sanitizers; native I/O and
identity/fade providers are doubles. The MIPS build passes, with a
160-byte largest new individual frame; total dynamic stack, native gameplay,
and hardware remain unverified. The exhausted diary fixture is not restarted.

### Event announcements and acre lock

`tools/v3_holiday_scene.py` derives the complete 18-event/16-title mapping from
the checked donor initializer. `AFHT` at `806FB700` is 208 bytes: a 16-byte header,
128 event-to-title bytes, and 32 big-endian message IDs. The first sixteen IDs
are opening messages; the last sixteen are conclusions. A source flag of one
selects opening; other values select conclusion. Unnamed events produce no
message. The sports umbrella event retains its actual source title mapping.

The installed 512-byte reader at `806FB200` replaces only the native initializer
table pointer at `80104ADC`; the original `8007C484` function remains intact.
Native event IDs retain their original path. Additive IDs map back to source
events before choosing a message. The original door copy, colours, camera,
message delay, and thirty-frame scene delay are preserved. The actual message
field is a 32-bit value at demo offset `300`, not a donor structure cast.

Twenty-eight messages reuse the installed complete English records. Morning
exercise and New Year's announcements retain the reviewed shrine-plaza wording
and existing credits. Four complete official Groundhog Day/Harvest opening and
closing messages occupy `305C..305F`, with source records `1751`, `1752`, `17A7`,
and `17A8` recorded in `translations/provenance.json`. Manual newlines, colours,
pauses, and the individual automatic-close delays remain intact. All previous
messages and choice resources are retained; both native message bounds cover
the four additions. No assistant-authored replacement announcement is used.

Sports callbacks call the native setter `800B21D0`. Its matching getter
`800B21E0` reads the existing common-state byte `801378DC`. The complete native
`mEv_PlayerOK` and four player functions are checked, including all seven getter
calls for directional movement, ordinary/snowball acre transitions, and reset.
No new player hook, guessed common-data field, or copied lock state is needed.

`tests/test_v3_holiday_scene.py` compiles the actual donor title switch alongside
the port for every event value and relevant flag. A sanitized initializer check
preserves non-message fields and original-event fallback. Cartridge checks cover
complete resources, actual reader hooks, both changed startup packet entries,
retained public exports, and all five relinked placement callers. Native I/O is
doubled; these are not executed in-game transition tests. Current empty, mixed,
and all-supported browser/offline outputs agree, with 191 supported selections
and every unfinished diary still unavailable.

### Shared transition and native scene bridge

`tools/v3_holiday_transition.py` prepares the complete shared collision, escape,
and fade path at `build/v3-diary-category-work-01/transition-native-06/`. The same
code is installed in the ABI-325 proposal at
`build/v3-diary-category-work-01/decorations-installed-01/`. It compiles
six whole donor functions, including `title_fade`, `player_lap_check`, and
`mEvMN_CheckLapPlayer`, through an explicit normalized context. The two complete
escape-offset arrays are checked against actual donor relocations and data:
448 bytes for the two 28-position searches, and 96 bytes for fixed obstacles.
The expanding search, near-gate fallback, five transition gates, and Groundhog
branches are retained. Generated donor C remains ignored.

The collision reader follows all seventeen source layout entries in ACTIVE
order, including a null layout masking later active entries. Structure names
belong to source type **5**, confirmed by the actual enum, not type 8. Every
active structure must resolve to an installed identity before scene mutation.
Eight checked native geometry functions provide acre/unit conversion, structure
footprints, landmark lookup, police collision, NPC space, and nearby gates.

`af_holiday_transition_native_fade` connects the generated fade to actual native
player, manager, common, and scene state. The complete original fade at
`8095EC24..8095EDE4`, the player accessor, and all directly bound native functions
are guarded. Source announcement type 13 maps to native type 12. The request is
written before `goto_other_scene`, even when that call rejects the transition.
The player-position predicate is called **after** the scene request, not cached
before it. Return-door data, the additive event ID, title flags, manager skip,
and wipe/fade fields are committed before rhythm capture, player warp, and BGM.
Unrelated native fields and existing door padding are preserved.

The native bridge still requires actual imported common-state providers. These
must supply source/native ACTIVE identities, current acre and pool shape,
present-demo and room-message gates, Groundhog state, climate/rhythm handling,
and the alternate event-message lifecycle. Missing providers reject explicitly;
native demo 13 is **not** treated as source event-message-2. No substitute owner,
zero-filled gate, or no-op side effect is an implemented service.

The linked module is 6,592 bytes, SHA-256
`2c19448ef951fab59e98d602581629baa8a7b3fed029653449b7537ffbe0dc47`,
with a 328-byte largest individual frame. It occupies `806FC000` within the
installed 16-KiB extension of the holiday packet, ending at `80700000`. The
complete preceding 32 KiB and its guard are preserved, as is the original physical
ROM resource. The replacement 48-KiB packet has a new physical allocation and
final guard. Its actual startup descriptor transfers/checks/invalidates the
whole packet. Every prepared native binding and source hash is checked before
reuse; the module is not recompiled. Installed code does not activate incomplete
owners. Remaining service providers and live manager dispatch stay unfinished,
along with costume/exercise/Miko/race behaviour in this same diary category.

`tests/test_v3_holiday_transition.py` runs one sanitized host check of the actual
generated functions and both native adapters. It covers every layout placement,
ACTIVE/null precedence, escape/fallback, gates, ordinary and Groundhog doors,
request rejection, post-request position changes, ordered native writes, and
missing-provider rejection. Native I/O, installed identities, and imported
services are doubles. Total dynamic stack, in-game transitions, native diary
gameplay, and hardware remain unverified. The exhausted native fixture budget is
unchanged; no old build or fixture is replayed.

### Shared hourly activation and event-state lifetime

`tools/v3_holiday_active.py` connects the full native hourly updater to donor
sports state, without treating scheduling as attendance. The 784-byte module
occupies `806F3000` in the existing NPC packet; its largest individual frame is
64 bytes. `AFHolidayDedicatedCommon` occupies four bytes at `806F3FE0`, initialized
to two signed `-1` values. `af_holiday_dedicated_current` passes that same state
to the complete dedicated-owner adapter. It is transient, not a saved extension.

The native `common_data_reinit` and `mEv_ClearEventInfo` both reset the imported
state inline. Neither calls unloaded packet code. The latter retains every
native reset operation, replacing seven zero stores with the checked native
28-byte `memset` and preserving the remaining function. Scene/manager changes
retain the state until an actual reset. These two callers and the complete native
hourly/status/place/rumour functions are guarded before patching.

All 64 daily rows share the native ACTIVE/START/CLEAR, short-event, occupied-acre,
ERROR/RUN, change-count, and rumour rules. Original identities and camper 70
retain native cancellation. Imported identities 71..114 use the fixed reverse
map: source sports umbrella 16 is suppressed until the donor over-status matches;
ball toss 12, tug-of-war 14, and foot race 15 stop while over-status is not `-1`.
The source START precedence and early-continue behaviour are retained. The
complete donor source initializes over-status but supplies no further direct
assignment; no invented completion writer is installed.

The focused sanitized host comparison compiles the complete donor hourly
function with engine-I/O doubles, comparing the connected sports paths. It also
checks native/camper cancellation, last-slot handling, rumours, and the shared
owner-state entry. The current cartridge check executes the rewritten reset
prefix with bounded native-call doubles and inspects installed code, unchanged
saved format/profile, full packet preservation, and the actual startup descriptor.
Both checks pass. Browser/offline output agrees for empty, mixed, and all-supported
selections. No native scene/event execution, hardware test, owner activation,
or newly playable diary is claimed. Save format twelve and diary schema two
remain unchanged; older V2/format-eleven readers cannot read these saves.

### Shared event-decoration resources

`tools/v3_holiday_structures.py` discovers every structure in the actual seventeen
donor layouts through the complete 83-row `aSTR_setupActor_proc` directory. All
eighteen names resolve to eleven complete actor profiles. Source callbacks,
included drawing/movement files, shadow descriptors, and layout membership stay
attached to the resulting records. The preparation at
`build/v3-diary-category-work-01/decorations-01/` contains 32 deduplicated native
objects, compiled together through the existing model converter.

The batch retains both countdown skeletons and complete animations, both
independently selected ten-frame digit banks, all seasonal palette selections,
the two-layer scrolling spotlight, complete opaque/translucent streams, and
projected shadows. Actual empty donor streams remain terminal returns. Shared
format support binds projected vertices to the caller's segment, distinguishes
independently selected textures from blended texture layers, and supports the
separate segment-ten palette. Source colour expressions and native commands
are compared in the focused check, including all triangles and model returns.

The right fireworks stall's source shadow descriptor requests ten projections,
but its vertex and adjustment arrays each contain seven entries. Its converted
contract preserves both complete arrays and all model geometry, records the
source count, and limits projection to seven entries. The native owner must
consume `projection_count`, not repeat the source out-of-bounds loop. This is a
bounds correction, not omitted artwork or a gameplay behaviour choice.

The ordinary holiday-services refresh installs the prepared objects and twelve
projection-flag arrays as `holiday-decorations-GAFE01-r0`: 135,520 bytes, SHA-256
`89d6a15d6fb339273fefa0e03b77c4c2edcb29007262d19b4bcde9221c12593b`.
It reconstructs and checks the prepared objects without compiling again. No
resident reservation, actor callback, profile bit, saved field, or public patcher
changes. Artwork storage does not establish working decoration actors. The
current proposal retains save format twelve and diary schema two; ordinary
native execution, reload, and hardware remain unverified.

Continue the connected actor path through the existing structure owner:
VROM `008CB690`, RAM `809E7ED0`, relocation `008CD350`. Its setup pointer at
`809E93F8/809E9400` already calls `af_v3_campsite_structure_setup`; preserve that
chain and campsite identity `5849`. Reuse the shared structure segment/instance
allocation and checked complete resources. Port the real constructors, collision,
movement, drawing, destruction, and interactions, including Harvest-table fork
handling, radio/exercise participation, countdown control, and fishing ownership.
Do not activate an actor with only artwork or alias it to a native actor with
different event semantics.

The original native event-layout directory has fifteen types at `80105030` and
fifteen pointers at `801055E8`. Its readers are `80081E60..80082168`; the existing
disassembly is `build/v3-diary-category-work-01/native-core-map/code.asm`.
Native radio `582B` differs from donor `582C`; native fireworks stalls `582C/D`
differ from donor `582D/E`. Native Goza `582A` is one picnic blanket, whereas
donor `582A/B` are two tables. Several donor layouts add Tortimer or replace
participants. Native moon owners 21 and 22 are distinct native calendar events;
neither is a verified alias for donor meteor owner 37. Preserve the native graph
for native events and use checked donor-to-destination identities for imported
owners. Positional zipping or numeric passthrough would spawn unrelated objects.

Five focused checks cover the new format paths and complete current cartridge
resource. Private browser/offline empty, mixed, and all-191 compositions agree.
The same unfinished diary category still includes owner connections, native/source
ACTIVE resolution, scene-state services, actual attendance, and calendar choice.
No native fixture is restarted, and the existing harness budget is retained.

## Serialized diary state

`AFDiary` is a 48,048-byte, endian-independent byte array:

| Offset | Content |
| --- | --- |
| `0..3` | `AFDY` |
| `4..5` | Big-endian diary schema 2 |
| `6` | Town Day; zero before initialization, otherwise 1–31 excluding 4 |
| `7`, `15` | Reserved zero |
| `8..11` | Lighthouse start year (big-endian), month, day; zero when absent |
| `12` | Seven daily light flags |
| `13` | Low four started-player bits, high four contribution bits |
| `14` | Low four completed-player bits |
| `16 + player × 12008` | Complete 104-byte calendar |
| Player record + `104 + month × 992` | Complete monthly page, months 0–11 |

The calendar uses source big-endian field order. Invalid reserved bytes, lock
values, day high bits, and month metadata reject. Text layout is validated before
editing or drawing; arbitrary saved glyph data must not index outside the
font/line buffers. Schema one requires zero bytes `6..15` and upgrades without
moving player data. Player deletion clears that player's calendar, pages, and
lighthouse contribution bit, preserving the other players and town state.
New towns/reset initialize all pages to spaces. All covers access the same data.

## Save envelope and edit admission

The optional `AF_V3_DIARY_STORAGE` build extends the shared compressor, retaining
its old API for console-only envelopes. `AF_V3_HOLIDAY_STORAGE` writes format
twelve with schema two. The payload contains:

- The complete canonical format-eight, registry-five town: 65,536 bytes.
- All four existing console records: 6,528 bytes.
- The complete diary state: 48,048 bytes.

Decoded size is **120,112 bytes**. Stored size remains one 65,536-byte bank;
both independent FlashRAM banks remain. The existing stream area, town header,
town-ID mirror, native checksum, disk CRC, canonical CRC, and console CRC remain.
Envelope word `F9A4` (header offset 36) contains the diary CRC in formats eleven
and twelve; earlier envelopes retain zero there. Both require canonical format
eight/registry five and the exact expanded size. Format eleven requires schema
one; format twelve requires schema two. Unknown
formats, corrupted streams, padding, lengths, and checksum failures reject.

`af_v3_save_expand_diary` reads existing supported compressed formats and
initializes diary state when absent. Format-eleven migration validates all CRCs
before upgrading the existing diary header, retaining pages and console progress.
The canonical decoder still validates/migrates the complete town/profile.
**New saves require this or a newer compatible V3 build; V2 and format-eleven-or-
earlier V3 cannot load them. Preserve backups.** Only the experimental
cartridge uses this format; the stable deployments and user's saves are untouched.

Writing first measures the complete encoded save. Failure leaves the output
bank unchanged. The diary editor additionally stages the changed page in
caller-owned state and calls `af_v3_diary_preflight` before committing it. That
function constructs the current canonical town using the ordinary save header,
current profile/state, and current console progress, and measures the candidate
diary without erase/write calls. Rejection retains the old live page and the
editable draft; it does not invoke the fatal save-error screen.

This is a capacity check for the current town, not a proof that every possible
future combination fits. Future town/console growth can still exceed FlashRAM;
the existing pre-write failure gate remains. Do not claim that compression gives
unlimited storage or that a synthetic vocabulary represents every player's text.
The controller, warning renderer, and native keyboard implement rejection and
return-to-editor; their connected native execution remains unverified.

## Memory and prepared code

`build/v3-diary-category-work-01/prepared-05/diaries.json` binds the complete
22,544-byte save/calendar/menu module to ABI 308 and current source hashes. Preparation uses
the existing Docker toolchain and checks the current report's RAM reservations.
These are installed guarded allocations:

| RAM | Bytes | Purpose |
| --- | ---: | --- |
| `80670000` | `6000` hex, including end guard | Retained code and stable redirected entries |
| `80676000` | 48,048 + 16 | Live diary state and guard |
| `80682000` | 120,112 + 16 | Expanded save workspace and guard |
| `806F4000` | `8000` hex, including end guard | Holiday state, updated storage, and linked NPC lifecycle |

The existing console records and compression hash workspace retain their
allocations. The old decode buffer is not grown into neighbouring console/model
memory. The largest compiled local frame is 2,264 bytes in the editor command
handler; its layout helper adds 232 bytes. Native menu-thread stack capacity and
transient candidate/edit allocations must be checked during UI installation.
The packet has no mutable globals or unresolved symbols.

## Shared cartridge installation

`tools/v3_diary_install.py` is called by the existing shared runtime builder with
the explicit `--diary-core`, `--diary-ui`, and `--diary-screen` preparations.
It reuses the complete checked core, screen, and menu packets without reconversion.
The current installed build is ABI 310, ROM SHA-256
`9f2b847858e9852b1e67fa2888ae34f2ad4ffed0fb5dac44652a9887bddced15`,
at `build/v3-diary-category-work-01/carried-03/`. Its build lock pins the report
and cartridge; it is an implementation checkpoint, not a playtest release.

Three physical-ROM resources load the 24,576-byte storage reservation, 36,864-byte
UI/code/state reservation, and 144,256-byte artwork/guard packet. The shared
startup retains all existing packets and checks every transfer and CRC before
entering initialization. Sixteen descriptors and their loader fit in 600 of 688
reserved bytes. Live diary state, compression workspace, and separate edit
candidate have independent guards. Total added reserved RAM is 421,952 bytes,
including code, artwork, state, scratch, and guards, below the framebuffer.

All 23 stable console/storage entries redirect to the new save module. Their
23 corresponding exports inside the insect packet also redirect: insect seasonal
code calls its local save-state checker directly, so changing only the stable
entries would leave calls to the obsolete scratch/guard implementation. The
complete predecessor packet is checked before replacement; only those eight-byte
entry windows change. Canonical format-eight codec bodies, creature artwork,
and all other packet bytes remain. Both packet hashes and the startup CRC are
updated. Canonical-code and storage-code ownership remain distinct in the report.

HBOARD code/relocation move to logical VROM `04600000`/`04610000`; keyboard
code/relocation move to `04620000`/`04630000`. Their original DMA indices remain
adjacent, as required by the native overlay manager. Old physical allocations
are preserved. Each new physical destination is checked against DMA owners,
physical resources, and nonzero data. The submenu owner descriptors and the
1,600-byte arena growth are installed together. The room hook removes exactly
one owner relocation while preserving the relocation footer, all other rows,
and its original delay slot. The native played-day call retains its delay slot.

`tests/test_v3_diary_install.py` checks complete installed packets, both save
dispatch routes, current checksums, all fifteen startup descriptors, menu DMA
identities, owner descriptors, room relocation at two load addresses, and unchanged
surrounding data. The shared sanitized startup test checks transfer/CRC failure
before initialization for every descriptor. Three focused tests pass. These are
cartridge and host checks, not native menu rendering, FlashRAM execution, or
hardware evidence. No diary choices are enabled by this installation.

## Connected consumer map

| Consumer | Current implementation / remaining work |
| --- | --- |
| Category identity/data | Fixed `2B10..2B1F` destinations preserve native `2B00`; shared names/prices/types, placement/pickup, and collection record/check readers installed |
| Carried/collection artwork | Shared pocket icon and ground/police/handover model installed; all sixteen distinct room/catalogue covers installed once and shared between consumers |
| Calendar entry | Surface A-tap uses additive carried IDs; owner/player resolution, dates/events/birthdays, drawing, owned menu, and visit hook installed; actual participation callers remain |
| Reading/editing | Controller, ownership, wrapping/scrolling, cursor, keyboard child, confirmation/privacy, transitions, atomic commit, overlays/DMA/arena installed; native execution remains |
| English UI | Official prompts, project errors, all screen textures, and native event labels extracted/credited/checked; native rendering remains unverified |
| Persistence | Shared reset, clear, probe, pack, commit, forward migration, and preflight implemented/tested on host; startup and both stable/direct native dispatch installed; native UI/save verification remains |
| Catalogue/scoring | All sixteen furniture-page records, donor framing/prices, scoring metadata, and upper-layer clutter exemption installed; native execution remains |
| Selection | All sixteen parent/cover/profile, catalogue, and scoring bindings implemented; browser/offline pending handling verified; choices remain disabled until required gameplay is connected |
| Verification | Run bounded combined current-ROM UI/save checks after integration; no separate style-by-style native scenarios |

Continue this same category with connected native UI/save checks. The carried-ID
save/profile and independent/all selection bindings are implemented below. Actual attendance
requires the shared Tortimer conversation path identified above; keep that
remaining behaviour explicit rather than searching for a nonexistent native
calendar caller. The category remains unfinished until that dependency works.
The native `item1_B_tableNo` retains its existing `2B00` entry of type 21.
Names/type/price and display/pocket conversion wrap the current shared readers,
with disabled-import rejection. Ordinary placement retains the carried diary;
collection record/check uses its cover. The surface predicate uses the same
fixed registry range. Reuse the installed
core, screen packet, UI, and source catalogue, and
retain passing save evidence unless those paths change. Do not redirect to
acquisition, gold-tree work, or replay exhausted creature/console fixtures.

The native menu tables have no calendar/diary slots. Reuse an explicitly owned
mode in an existing submenu rather than passing the donor indices 27/28 into
the shorter native table. The accepted English editor remains the keyboard.
The UI converter retains the donor's 2D combiners, geometry/render states, and
explicit inherited textures; the ordinary furniture mode still rejects unsupported
states. Do not flatten away unknown commands or substitute a generic screen.
Current room/core disassembly is retained under
`build/v3-diary-category-work-01/native-{room,core}-map/`; do not remap these callers.

### Shared carried installation

`tools/v3_furniture_install.py --refresh-runtime --diary-items` installs all
sixteen carried styles through `tools/v3_diary_items.py`. The current ABI-310
proposal is `build/v3-diary-category-work-01/carried-03/build-lock.json`, ROM
SHA-256 `9f2b847858e9852b1e67fa2888ae34f2ad4ffed0fb5dac44652a9887bddced15`.
The guarded `806E0000..806E4000` physical-ROM packet holds 1,680 code bytes,
the complete 400-byte identity/name/price table at `806E2000`, the shared donor
icon at `806E2300`, and the reused 816-byte carried model at `806E2600`.
It does not enable profiles or change the save format/profile.

Seven checked entry replacements chain to existing name/type/price, placement,
pickup, and collection readers. Disabled diaries cannot index native short
tables or write collection bits. Collection recording resolves the actual player
and uses the existing shared save extension. Cover rotations map to the same
carried identity and collection bit. The default pocket-icon branch preserves
the native 64-bit register state and delegates non-diaries to the installed
creature branch. Native tools and gifts retain their own branches.

Shared category 44 (`27 + donor category 17`) uses the existing 71-entry
ground/police/handover tables. Each seasonal overlay receives a complete new
descriptor bank after its retained scenery bank; changing the ground configuration
does not relocate scenery resources or change actor/index-array capacities.
Both the actual overlay allocation and relocation BSS size include the new bank.
The room A-tap predicate is relinked with the new identities; only its checked
constant changes, and all installed UI exports and other UI bytes remain intact.
The complete sixteen-packet startup fits in 600 of 688 reserved bytes.

`tests/test_v3_diary_items.py` verifies the current source data, installed packets,
reader chains, unchanged native identities/scenery, startup CRCs, and guarded
allocation. Sanitized host checks cover all sixteen styles and rotations,
four-player collection routing, disabled/malformed records, the complete startup
failure paths, and all four seasonal descriptor banks beyond 64 KiB. The connected
surface/menu host check uses additive IDs. These checks do not establish ordinary
native diary use, menu appearance, saving, or hardware behaviour. Diary choices
remain disabled while participation, ready-choice activation, and connected native checks
remain unfinished.

### Selection and save-profile binding

`tools/v3_diary_selection.py` binds all sixteen installed carried/cover pairs,
complete sparse records, inverse parent metadata, immutable reader packet, and
cover artwork. The single cover bit at byte `32 + floor((63 + style) / 8)` in the
192-byte profile controls both representations. Native `2B00` retains its original
path; neither a cover rotation nor a source ID becomes a separate saved identity.
Unknown or changed identities, enabled pending profiles, and incomplete records
reject. The existing canonical codec needs no new saved field or format.

The shared resolver and catalogue/scoring generators support individual/all
parent bindings. The authoritative selectable catalogue excludes unfinished
diaries, and final composition rejects a caller-forged catalogue. Browser plans
record these bindings under `pending_options`, never under selectable options.
Their installed catalogue rows retain their exact source positions for input
validation, then disappear when a supported profile is composed. Their scoring
metadata is disabled unconditionally. Select all has an explicit derived output
hash because the installation contains prepared but unavailable rows; it must
not enable unfinished imports merely to reproduce the installation hash.

For ABI 313, empty output is the pinned V2-14; all 191 supported development
choices produce SHA-256
`f2e5c31a5b890ad1112bde72cc7b5da9a9f13e3a0547cf706fb63e5a5f8d81fc`.
The main build lock remains unchanged. Neither deployed
patcher consumes this experimental plan.

`tests/test_v3_diary_selection.py` checks all parent/profile bindings, complete
category catalogue/scoring resolution, rejection of forged readiness, and three
current browser/offline profiles. Its sanitized save check links the actual
carried/cover readers, native selected-style resolver, canonical codec, and
format-eleven adapter. Four players retain separate collection flags and pages
through save/reset/reload; removing any selected style rejects without writing
live state or the simulated device. The test uses an isolated host FlashRAM
double and does not prove native UI use, native I/O timing, or hardware operation.
Eleven browser-engine checks include unavailable selection, pending-row removal,
overlapping writes, input preservation, and existing checksum/profile contracts.

### Shared room covers and catalogue

`--diary-room-art build/v3-furniture-all-static-prepared-02` installs all sixteen
complete prepared models through the shared runtime builder. The donor's
Shop_Goods table uses the individual covers in rooms and shops; its generic
diary graphic belongs to ground/police/handover consumers. Both donor modes and
all four drawing lanes are checked, including models using the second opaque
lane and the scroll's different room/catalogue layer bindings.

The native Shop_Goods owner moves to logical VROM `01A50000`, with relocation
at `01A60000`, retaining its original consecutive DMA indices and linked RAM
`80962A20`. The original 34 rows and code remain, with eight checked table-reference
groups pointing to the expanded 50-row table. Materialising the original sixteen
BSS bytes preserves their linked offsets. Appended cover models total 35,616
bytes; the complete owner is 41,424 bytes. Native overlay allocation includes
the complete image, without adding a permanent model buffer.

The room constructor uses 108 checked fixups to rebase the **loaded** model
resources and flush the changed cache range. ROM commands retain segment-six
pointers so normal catalogue DMA reads the same complete resources. No unknown
VROM fallback or second copy of the artwork is required. The source-derived
50-category rotation flags preserve original categories and all diary styles.
The 1,648-byte adapter at `806E0800` and configuration at `806E3000` use existing
diary packet padding. Original room helper addresses retain eight-byte dispatch
entries; all their other bytes and existing lifetime state remain.

`--diary-catalogue` connects furniture-page ordering, ownership, selected profile
loading, names, parent prices, and the donor's diary preview framing: scale 1,
model Y 0, and height 36. Representation rows are checked against the complete
donor table and initializer; they do not invent ordinary furniture stock.
All sixteen HRA/feng-shui metadata rows use the existing category conversion.
The donor does not score carried diaries as ordinary room furniture. Its
upper-layer clutter rule exempts diaries on surfaces while retaining the floor
penalty. A 400-byte adapter at `806E1000`, using the existing full-register
query bridge, replaces only that upper-layer call. Every other scoring query,
including the floor call, is retained.

Catalogue suffix code/data occupies 3,984 bytes. An additional 256-byte menu
allowance is checked together with existing model, clothing, and diary UI
allocations, without double-counting the retained diary reservation. There is
no new permanent RAM or saved-format change in these two installation steps.
The canonical cover profiles and parent metadata stay inactive until selection
is connected. Neither converted art nor an installed catalogue row claims a
usable diary by itself.

`tests/test_v3_diary_room.py` covers complete room models/profiles, actual DMA
indices, relocation at two addresses, retained bytes/exports, all sixteen styles
and rotations, invalid resource gates, actual catalogue/scoring/startup CRCs,
menu allocation, prices/framing, disabled-style handling, and the scoped clutter
query. Four focused cartridge/host checks pass for the connected installations.
No native UI execution, actual catalogue order delivery, save/reload, or hardware
verification is claimed.

## Focused evidence

The current connected native attempt is [inconclusive before menu opening](../docs/checkpoints/V3_DIARY_NATIVE.md).
Both allowed setup attempts are terminal; no title-fixture retry is pending.
All four installed packets match and the initial native fault pointer is zero,
but neither attempt reaches the menu, editor, save codec, or device I/O.

`tests/test_v3_diaries.py` checks all sixteen source records and complete
consumers, changed-source rejection, sanitized editing/access/atomic commit,
all 48 monthly pages, row/buffer limits, proportional cursor movement, source
changes during editing, independent player clearing, compressed migration,
malformed-bank rejection, and an independent Yaz0 decoder comparison. The native
save-adapter test reuses the existing I/O doubles without running historical ROMs:
7,465 assertions cover ordinary shared synchronous writing, probing without live
commit, reload, migration, guards, and edit-capacity rejection with no I/O.

A full 48-page vocabulary fixture plus the existing town fixture and random
console records compresses to 32,403 of 63,850 stream bytes. Incompressible input
rejects before changing output. The changed compressor also passes the existing
446-assertion envelope test, including the dense-town capacity and old-format
round-trip checks. These are host/source/compiler checks, not hardware results.

The focused calendar comparison compiles the actual donor calendar C and marker
reader alongside the port. It covers forward/backward month changes, year resets,
all attendance flag types, and day marks, with 24,420 matching comparisons.
The connected menu/surface test uses every style, all four player identities,
owner/read-only/locked access, month/day/event navigation, confirmation/privacy,
and rejected edits. Native interaction fallbacks, vacant houses, failed menu
opening, and disabled styles are included. The room adapter also compiles as a
VR4300 object; its installed native execution is not claimed.

Three focused UI checks cover the complete host menu/keyboard interaction,
accepted/rejected commit and draft retention, first-A answer reveal, native child
return, ordinary HBOARD fallback, read-only/locked access, invalid-session closure,
and retained-prefix/relocation checks on both prepared native overlays. Host
callbacks model menu lifecycle; they do not execute the game or verify pixels.
