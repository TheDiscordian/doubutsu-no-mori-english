# Shared English keyboard grid

## Scope and native editing contract

Replace the shared native radial input/drawing interface with the supplied
GameCube 10-column, four-row QWERTY/alphabetical layout. Keep every installed
name, catchphrase, song, letter, notice, and owner-message editing handler.
Do not change saved capacities or replace complete hboard/apology adapters.
The grid selects a key and emits the existing native command; the existing
handler decides whether that edit fits and whether Done may close the editor.

The [native direction ABI](KEYBOARD_CURSOR_ABI.md) fixes the emitted cursor
numbers at right=1, left=2, up=3, and down=4. Controller enum names alone are not
evidence of compatibility; regression checks bind the numbers to the original
ROM's selector. The corrected controller preserves the complete installed layout.

The current full editor is the 23,168-byte apology image at VROM `03940000`,
adjacent relocation `03948000`, linked RAM `80885140`. Its 48-byte original
state and earlier hboard/apology contexts retain their addresses. Append owned
grid code/state and explicitly enlarge the shared submenu reservation as needed.
Do not put new grid files in `runtime/`: that directory is the source-hash-bound
resident module, which stays unchanged. New sources belong in
`overlays/keyboard_grid/`.

## Verified integration points

| Native address | Existing purpose | Grid integration |
| --- | --- | --- |
| `80888484` | Init call to the installed apology wrapper | Call that wrapper, then reset grid ownership/selection |
| `808867B8` | Call to radial stick detector `808851D8` | Prepare neutral radial state; retain the containing native update |
| `808868D8` | Command-selection call `808857F8` | Grid movement/buttons emit the existing command and key byte |
| `808882D8` | Keyboard drawing call `80888024` | Draw the shared grid; retain the preceding caller-window draw |

All four are existing relocated calls, with their original delay slots retained.
The native update at `80886724` already clears `processed`, handles the waiting
letter-window branch, advances the text-cursor blink, dispatches the current
mode handler via the table at `80888824`, performs existing feedback/exchange,
and calls the installed proportional cursor wrapper at `808869A4`.
Preserve that logic. Preparing state byte `03` as zero skips only radial dial
scrolling and goes to `808868D8`; state halfword `06` stays -1. No grid selection
uses or expands saved input fields.

The original draw wrapper at `80888294` calls the current caller-window renderer
first, then the keyboard draw, and retains the address-book overlay continuation.
The replacement must retain the original segment-12 setup: CPU segment entry
`801458D0` and an RSP segment command use the current menu's asset pointer at
`+28`. Text drawing uses the current submenu `+2C` overlay's `+106B4` matrix
callback. The editor pointer is overlay `+106E0`. Menu position floats are
`+18/+1C`. Graphics opaque head/tail are `+298/+29C`; font head/tail `+2B8/+2BC`.
Bound command reservations before drawing and preserve both streams.

## GameCube reference and character adaptation

The supplied `.data` tables are each 40 bytes:
`0007F5D8` lower QWERTY, `0007F600` lower alphabetical, `0007F628` upper QWERTY,
`0007F650` upper alphabetical, `0007F678` symbols, and `0007F6A0` marks.
Verify the complete REL/symbol identities before translating byte encodings.
The upper-case layouts map exactly to native letters, digits, newline, and
space. Lower case and symbols require explicit native-code mapping; never copy
GC byte values blindly. The GC spare cell is not an insertable character.
Characters without a supported native input encoding remain disabled, not
silently replaced with a different typed character.

The installed apology editor specifically maps native symbol-page keys `84`
and `81` to complete Sun/Skull tokens; its `85` key maps to equals. Retain that
scope and use its existing key drawer/command adapter. Ordinary saved names
must not gain unrestricted two-byte glyph insertion. The grid must not claim
full GC accent/symbol support when those underlying input formats cannot store it.

GC key-text origins are X `60+16*column+row_slide+2`, Y `133+16*row`, with
row slides `0,3,7,10`, plus the native menu's animated X/-Y position. Use the
same cell arrangement and centre the installed narrower glyphs within cells.
The reference uses 16 held frames before repetition, then four at 60 Hz; the
equivalent native 30-Hz timing is eight then two. Clamp grid edges as in the GC
reference. Stick/D-pad moves the grid; C-buttons retain text-cursor movement.
L changes case, R inserts space, Z changes page, L+Z changes QWERTY/alphabetical,
A types, B deletes, and Start finishes through the original handler. Labels must
describe these N64 mappings, not show nonexistent GameCube X/Y buttons.
L+A invokes the retained native case/ornament exchange for the character before
the text cursor. Initialization opens the uppercase QWERTY table.

## Implementation sequence and bounded checks

Build the encoding-bound layout resource and pure grid controller, then append
the native input/drawing bridges to the complete existing editor. Preserve and
verify preceding hooks, regenerate all added relocations, and update exact owner
metadata/allocation checks. Keep a separate candidate until all those parts are
installed together. Rebuild the combined title on top only after the keyboard
candidate's complete resource-retention checks pass.

Focused checks cover key mappings, boundaries/repeat, case/page/arrangement,
disabled/newline restrictions, native command values, preserved capacities,
independent MIPS compilation, relocation and allocation, and complete cartridge
retention. Reuse existing editor fixtures for a bounded name/letter/owner-message
native batch; do not repeat the entire tutorial or build a per-character native
matrix. Normal save/restart and hardware interaction remain human playtest work.

## Installed image and allocation

The compiled grid image is 28,656 bytes. Code ends at image offset `6C80`,
the 480-byte mapped tables start there, the keycap follows at `6E60`, and the
36-byte private context starts at `6FC0`, followed by zero alignment padding.
The relocation resource is 2,096 bytes and preserves every preceding record.
All four hook targets and the metadata destructor are relocated within this
complete image; imports outside it are restricted to pinned native routines.

The shared submenu allocation instruction at `800C4B10` is `25CE2220`, adding
5,632 bytes to the complete preceding reservation. Rounded image growth is
5,504 bytes, and the combined 253,056-byte pool exceeds the conservative
252,736-byte bound. Editor VROM/relocation identities remain `03940000` and
`03948000`, and the original DMA indices are retained. The image ends before
the adjacent relocation range. The resident translation module and ordinary
four-MiB heap ceiling are unchanged.

`tools/keyboard_grid_overlay.py` checks exact compiled code/resource identities,
restores and verifies the complete preceding apology/owner editor, compares
relocated prefixes at three native heap locations, and binds owner/pool edits.
Shared inventory/letter checks accept the new pool word only through that
complete verification. Current-route progress checks validate the grid too.
