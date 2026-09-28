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
native FlashRAM timing, ordinary gameplay, or hardware compatibility. ABI 308
remains the current cartridge; this preparation does not change either patcher.

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
The menu-open and selected-style exports still need real native bindings; no stub
or unfinished hook is installed in the cartridge.

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
bindings and installation remain unfinished. Eight official prompt strings
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
provides projection/animation positions; actual event labels/day types remain a
required native provider. Paper and text use the same absolute scrolling offset,
including during transitions. Native cursor/end-marker callbacks use proportional
positions and explicitly bind the keyboard's marker assets before drawing. These
functions are not an installed or visually verified screen. The compiled largest
draw frame is 304 bytes; engine callees and actual stack high-water use remain
installation checks.

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
owner, and input-buffer checks. Its native init/update hooks remain uninstalled.
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
`build/v3-diary-category-work-01/ui-04/`: 12,496 code bytes, SHA-256
`3066fc1fe6ee8588c4f43db37b73422c9db2f7079a62f77bdd58a7c39f59bc0d`,
and 2,240 bytes of screen state. Planned code/state/art reservations start at
`806A0000`, `806A8000`, and `806B0000`; each has a guard and is checked against
existing reservations plus the prepared diary save workspace. No mutable state
is hidden in the linked code packet.

The prepared HBOARD overlay is 2,304 bytes and the keyboard is 39,936 bytes.
Together they require 1,600 additional aligned menu-arena bytes. The current
arena term is `8089A860`, not an older keyboard build's bound; the proposed term
is `8089AEA0`. The accepted keyboard lives at VROM `03E70000`, with relocation
`03E80000`. The builder preserves its complete previous prefix, including accepted
graphics, changing only the init call and PLAY dispatch entry. HBOARD changes
only its constructor's init/set-proc calls; prepared owner metadata also replaces
set-proc and destructor so native child return cannot restore house-message
handling. Complete retained-prefix checks pass at two real relocation bases.
Installation must reserve DMA storage and apply owner/arena updates together;
these prepared overlays are not installed in ABI 308.

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
eleven. **Once installed, new saves require this or a newer compatible V3 build;
V2 and earlier V3 cannot load them. Preserve backups.** The preparation itself
has not changed any cartridge's save format or the user's save files.

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
The controller implements rejection and return-to-editor; the in-game warning
renderer and native keyboard binding remain unfinished.

## Memory and prepared code

`build/v3-diary-category-work-01/prepared-04/diaries.json` binds the complete
22,588-byte save/calendar/menu module to ABI 308 and current source hashes. Preparation uses
the existing Docker toolchain and checks the current report's RAM reservations.
These are checked **planned** allocations, not installed startup reservations:

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
The prepared packet has no mutable globals or unresolved symbols.

## Connected consumer map

| Consumer | Current implementation / remaining work |
| --- | --- |
| Category identity/data | All sixteen donor IDs, names, prices, and aliases bound; additive native identity/readers still required |
| Carried/collection artwork | Shared carried model converted with the general split material/geometry converter; reuse cover conversions and install correct room/collection contexts |
| Calendar entry | Surface A-tap adapter, house-owner resolution, controller/markers, privacy, native drawing, and owned native menu linked; actual room entry, event/date callers, and installation remain |
| Reading/editing | Controller, ownership, wrapping/scrolling, cursor, keyboard child, confirmation/privacy, transitions, and atomic commit linked; overlay/DMA/arena installation and native execution remain |
| English UI | Official prompts, project errors, and all screen textures extracted/credited/checked; actual native event labels remain in screen integration |
| Persistence | Shared reset, clear, probe, pack, commit, forward migration, and preflight implemented/tested on host; startup loading and stable native dispatch still need installation |
| Selection | Bind carried/display profile dependencies, catalogue/scoring, and independent/all choices only after the complete path is connected |
| Verification | Run bounded combined current-ROM UI/save checks after integration; no separate style-by-style native scenarios |

Resume this same connected category at the real native date/event provider and
room-entry binding, followed by resident/startup/save dispatch, prepared menu-hook
installation, carried readers, and selection. Reuse the prepared
core, screen packet, linked UI, and source catalogue, and
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

## Focused evidence

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
