# Shared diary imports

## Scope and current boundary

All sixteen GAFE01-r0 carried styles, `2B00..2B0F`, share one diary system.
`tools/v3_diaries.py` binds their official names, prices, collection/display
aliases, and complete diary consumers to the actual checked donor. The styles
remain unavailable for selection until the complete native path is installed.
A converted cover is not a working diary.

The reading/editing/storage core and shared native-save adapter are implemented
in source and compile for VR4300. Host checks cover the connected edit → capacity
check → save → probe → reload path. They do not establish in-game UI operation,
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
The source `m_calendar.c` defines the exact forward/backward-time, event, and
year-change rules; native event/date integration remains required.

Collection aliases are `30FC..3138` in steps of four. Ordinary room placement
retains the carried diary identity instead of substituting a catalogue cover.
Do not install those aliases as independently selectable furniture.

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
The in-game rejection prompt and return-to-editor binding remain unfinished.

## Memory and prepared code

`build/v3-diary-category-work-01/prepared-01/diaries.json` binds the complete
17,571-byte code module to ABI 308 and current source hashes. Preparation uses
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
| Carried/collection artwork | Reuse prepared cover conversions; install the carried diary model and correct room/collection contexts |
| Calendar entry | Bind the actual interaction caller, owner, selected month, calendar art, controls, played-day/event updates, and lock confirmation |
| Reading/editing | Full buffer, access rules, commands, wrapping, scrolling, and transactional commit implemented; native keyboard/view/end-confirmation callers remain |
| English UI | Extract official diary/calendar/lock resources and credit them in the single provenance catalogue; capacity-error wording needs an explicit authorship record |
| Persistence | Shared reset, clear, probe, pack, commit, forward migration, and preflight implemented/tested on host; startup loading and stable native dispatch still need installation |
| Selection | Bind carried/display profile dependencies, catalogue/scoring, and independent/all choices only after the complete path is connected |
| Verification | Run bounded combined current-ROM UI/save checks after integration; no separate style-by-style native scenarios |

Resume this same connected category at native inventory/interaction and
calendar/editor bindings. Reuse the prepared core and source catalogue, and
retain passing save evidence unless those paths change. Do not redirect to
acquisition, gold-tree work, or replay exhausted creature/console fixtures.

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
