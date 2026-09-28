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
native FlashRAM timing, ordinary gameplay, or hardware compatibility. ABI 315
contains menus, resident packets, room/visit hooks, save dispatch, carried readers,
complete room covers, and catalogue/scoring integration at
`build/v3-diary-category-work-01/tortimer-dialogue-02/`. Neither patcher changes.

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

Three installation services remain unresolved:
`af_holiday_npc_bind`, `af_holiday_npc_event_world`, and
`af_holiday_npc_unregister`. Binding must supply the actual event owner,
special dates/vacation state, cleanup, and validation of the active outdoor clip.
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
- Reuse the installed native event directory/campsite infrastructure. Its index
  has 128 entries, but the event-manager dispatch and 16 today slots still need
  checked ownership/capacity when extending it. Camper event 70 stays reserved.
- Port shared shrine and wandering owners from `ac_event_manager.c`
  (`soncho_start/stop/in`, `sonchowandar_start/stop`). New Year's, sports,
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

## Serialized diary state

`AFDiary` is a 48,048-byte, endian-independent byte array:

| Offset | Content |
| --- | --- |
| `0..3` | `AFDY` |
| `4..5` | Big-endian diary schema 1 |
| `6..15` | Reserved zero |
| `16 + player × 12008` | Complete 104-byte calendar |
| Player record + `104 + month × 992` | Complete monthly page, months 0–11 |

The calendar uses source big-endian field order. Invalid reserved bytes, lock
values, day high bits, and month metadata reject. Text layout is validated before
editing or drawing; arbitrary saved glyph data must not index outside the
font/line buffers. Player deletion clears only that player's calendar and pages.
New towns/reset initialize all pages to spaces. All covers access the same data.

## Save envelope and edit admission

The optional `AF_V3_DIARY_STORAGE` build extends the shared compressor, retaining
its old API for console-only envelopes. Format eleven contains:

- The complete canonical format-eight, registry-five town: 65,536 bytes.
- All four existing console records: 6,528 bytes.
- The complete diary state: 48,048 bytes.

Decoded size is **120,112 bytes**. Stored size remains one 65,536-byte bank;
both independent FlashRAM banks remain. The existing stream area, town header,
town-ID mirror, native checksum, disk CRC, canonical CRC, and console CRC remain.
Envelope word `F9A4` (header offset 36) contains the diary CRC in format eleven;
older envelopes retain zero there. Format eleven requires canonical format
eight/registry five, the exact expanded size, and a valid diary schema. Unknown
formats, corrupted streams, padding, lengths, and checksum failures reject.

`af_v3_save_expand_diary` reads existing supported compressed formats and
initializes only the newly introduced diary state. The canonical decoder still
validates/migrates the complete town/profile. Older save readers reject format
eleven. **New saves require this or a newer compatible V3 build;
V2 and earlier V3 cannot load them. Preserve backups.** Only the experimental
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
| `80670000` | `6000` hex, including end guard | Code reservation |
| `80676000` | 48,048 + 16 | Live diary state and guard |
| `80682000` | 120,112 + 16 | Expanded save workspace and guard |

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
