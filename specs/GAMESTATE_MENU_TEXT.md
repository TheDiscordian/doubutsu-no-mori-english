# Native gamestate menu text

## Scope and provenance

The player-selection and save-menu gamestates at VROM `00747AA0` and `007486E0`
retain nine Japanese labels. They are distinct from the ordinary scene actor's
already-corrected `I'm new` option and from dialogue-driven saving. Both remain
registered as gamestates six/seven in `game_dlftbls` at `80106E20` and in the
native graph dispatcher. Their ordinary accessibility is not established by
registration; do not enable or invoke them just to translate their text.

Use original English translations of their native labels, not unrelated GC
menu records. Keep existing English A/R/B hints, native zero-based slot numbers,
player identities, destination choices, save actions, and error handling.

| Native label | Complete English |
| --- | --- |
| Unregistered player slot | `Unregistered` |
| Away status | `<Away>` |
| Home status | `<Home>` |
| Visiting from another place | `Visitor` |
| Player-selection heading | `Select a player` |
| Resident row prefix | `Resident `, native slot digit, then a space |
| Save-menu heading | `Save Menu` |
| Save to cartridge flash | `Save to FlashRAM` |
| Save to Controller Pak | `Save to Pak` |

`tools/gamestate_menu_text.py` binds complete original owner/relocation hashes
and the source definitions in the pinned N64 decompilation. Read-only native
disassemblies are retained under `build/gamestate-text-player-inspect-01` and
`build/gamestate-text-save-inspect-01`. No copyrighted asset is committed.

## Player-selection layout

Owner RAM `80828830`, 2,896 bytes; relocation `007485F0`, 240 bytes; sections
`(2768,112,16,0,52)`. The runtime gamestate instance remains 648 bytes.

Repack only the original forty-four-byte label region `80829300..8082932B`:

- `Select a player` at `80829300`, fifteen bytes.
- `<Away>` plus four spaces at `8082930F`, ten bytes.
- `<Home>` plus three spaces at `80829319`, nine bytes.
- `Visitor` plus three spaces at `80829322`, ten bytes.

`Unregistered` occupies all twelve bytes of the old heading/padding at
`80829358`. The resident prefix becomes eleven bytes `Resident   ` at
`80829364`, with one unused zero before the unchanged float constants.
The native handler table and colour arrays between those regions do not move.

Initialization copies twelve unregistered-label bytes into each existing
sixteen-byte display row, then pads offsets twelve through fifteen. Existing
registered names remain six bytes, followed by the same ten/nine-byte padded
status. Visitor initialization still copies ten bytes and pads the rest. None
of these buffers is a saved player-name field; saved identities remain untouched.

The resident drawer retains its 200-byte stack frame. Its combined display
buffer moves from `sp+A4` to `sp+A0`, with length 27 rather than 24. Saved
registers end at `sp+90`, and the next local is at `sp+BC`; the full new buffer
ends at `sp+BB` (exclusive). Replace the copied eight-byte prefix local with
one relocated source pointer stored at `sp+BC`. The existing concatenator copies
eleven prefix bytes plus the same sixteen-byte display row. Write the unchanged
native slot digit at combined offset nine (`sp+A9`). All four resulting labels
are complete `Resident 0 ` through `Resident 3 ` before the name/status.

The title's direct font count becomes fifteen. Original X/Y positions, scales,
colours, navigation, constructors' choice logic, and font calls remain. English
heading width is 86 pixels before the native 1.2 scale. The longest complete
row, including a six-byte Japanese saved name, remains within the screen at
the original 0.8 scale; do not narrow or translate a user's saved name.

## Save-menu layout

Owner RAM `80829470`, 2,848 bytes; relocation `00749200`, 224 bytes; sections
`(2560,256,32,0,50)`. The runtime gamestate instance remains 560 bytes.

Repack only the original hundred-byte text area `80829F0C..80829F6F`:

| Source address | Text | Counted length |
| --- | --- | ---: |
| `80829F0C` | `Save Menu` | 9 |
| `80829F18` | `Push A Button` | 13 |
| `80829F28` | `Select R Button` | 15 |
| `80829F38` | `Push B Button to EXIT` | 21 |
| `80829F50` | `Save to FlashRAM` | 16 |
| `80829F60` | `Save to Pak` | 11 |

All word-copy source addresses remain aligned. The unchanged hint text and
counts use their updated source pointers. The heading's old eight-byte stack
copy becomes a relocated source pointer stored at `sp+4C`, then loaded by the
font call with count nine. Its 88-byte frame is unchanged.

The two save choices occupy 27 contiguous source bytes plus one zero. Their
existing 112-byte-frame drawer copies 28 rather than 26 bytes by changing its
last halfword load/store to word load/store. Its buffer is `sp+50..sp+6B`, below
the frame end `sp+70`, and saved registers end at `sp+50`. The second choice
starts at `sp+60` rather than `sp+5D`; counts become sixteen/eleven. The native
save-destination selector, save functions, error dispatch, and game transition
code are not modified or executed by the translation checks.

## Validation and limits

All existing HI/LO relocations are retained and verified at three lower-memory
load bases. Both resource sizes, BSS sizes, gamestate metadata, and allocation
requirements stay unchanged. Complete cartridge reconstruction retains the title
warning, all RC6 corrections, and every other resource. Original ROM and UPS
reconstruction checks remain mandatory.

Focused checks cover complete text, all changed pointer/count/copy instructions,
stack and display-row boundaries, unchanged names/actions/metadata, relocation,
and altered-input rejection. They do not prove ordinary reachability, native
rendering, saving, or hardware appearance. Do not trigger Flash/Pak writes or
construct another save-confirmation harness for these label corrections.
