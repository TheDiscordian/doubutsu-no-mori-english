# English keyboard

## Implemented: English-first native editor

The production option is `tools/build.py --english-keyboard`; opening and pilot
Makefile targets enable it. The layout remains the native radial keyboard.
English letters are selected initially. The other modes remain available through
the original Z-button cycle; no Japanese characters or saved-name encodings are
removed.

| Resource | Virtual ROM | Linked RAM | File size |
| --- | --- | --- | --- |
| Character editor | `0x78CB80` | `0x80885140` | `0x39B0` |
| Name-entry window | `0x78BFB0` | `0x80884340` | `0xB20` |
| Keyboard object | `0xA40000` | Segmented graphics resource | `0x17140` |

Original resources have pinned SHA-256 guards in `tools/keyboard.py`.
Replacements retain their lengths. The editor relocation file at `0x790530`
remains unchanged; the name-window relocation file at `0x78CAD0` drops only two
obsolete cursor-constant relocations, retaining its size and other records.

### Default mode

Editor initialisation writes its input mode at state offset `+4` and dial scroll
at `+5`. The retail modes are hiragana=0, symbols=1, katakana=2, English=3, and
digits=4. File offsets `0x76C..0x773` change from two byte stores of zero
(`A0600004 A0600005`) to `addiu t9,zero,0x0300; sh t9,4(v1)`
(`24190300 A4790004`). This sets the same two bytes to 3 and 0. Register t9 is
overwritten before its next use. No pointer or jump relocation touches the patch.

English mode uses its original 30-byte character table at file offset `0x3454`:
A–Z, comma, period, newline, and space. Retail conversion and symbol modes retain
their original behaviour. This does not introduce a different character set.

### Name-entry prompts

Five prompts share the existing 56-byte region `0x9E0..0xA17`. Translated strings
are packed into that region. Each existing 40-byte window record, beginning at
`0xA18`, receives its updated pointer, explicit length, and centred horizontal
position. Existing pointer relocations remain valid. Retail title scale is 0.875.

Prompts are “Your name?”, “Destination”, “Catchphrase”, “Say it!”, and “Request a
song!”. The destination suffix becomes “town”, and its guarded immediate length
changes from three to four. Input limits remain six characters for player/town,
four for catchphrases, and ten for apology/song input. These are storage limits,
not widths to increase simply because Latin letters are narrower.

The separate [owner-message editor](HBOARD_EDITOR.md) installs a complete English
draft, proportional layout, and save-safe confirmation. Its native execution
acceptance remains. Its saved custom-message field stays 64 bytes. The
GameCube-style input grid must use the same verified
field-specific editing and confirmation operations, not bypass their limits.

### Name-entry cursor

The native cursor's fixed `12 * (index - 0.7)` calculation is replaced by
`mFont_GetStringWidth(input, index, TRUE) - 8.4`, so mixed-width text and the
cursor agree. This changes no font pixels and retains the original cursor
graphic's origin adjustment. The 24-instruction patch occupies the same range at
linked RAM `0x80884A20..0x80884A7F`. The existing function prologue preserves the
return address and saved registers for the added call to `0x800902CC`.

`tools/keyboard_cursor.s` is assembled using the pinned toolchain. Its verified
encoding is embedded in `tools/keyboard.py` so ordinary builds need no compiler.
`python3 tools/check_keyboard_assembly.py` checks source/encoding agreement.
Name-window relocation records `0x450006E4` and `0x460006E8`, which formerly
addressed the old floating-point constant, are removed. Every other relocation
record, the section sizes, and the relocation file's final length word remain.

### Texture labels

Five 48×16 I4 tab textures at `0x1848`, `0x19C8`, `0x1B48`, `0x1CC8`, and
`0x1E48` become Hira, Kana, Sym., ABC, and 123. IA8 textures at `0x1FC8`, `0x5448`,
`0x5848`, `0x5A48`, and `0x15048` become Confirm, Cursor, Del, Done, and Case.
The Del label is 32×16; the other IA8 labels are 64×16. Display-list texture
formats and tile sizes verify these spans independently of legacy notes.

Labels are composed locally from unscaled retail glyphs, removing empty outer
columns only. No glyph is resized. The font atlas is not modified by this module.
Generated Nintendo-derived graphics remain in ignored build outputs.

## Stretch implementation: GameCube-style grid

The pinned GameCube `src/game/m_editor_ovl.c` and `include/m_editor_ovl.h` define
a 10-column, four-row keyboard, with QWERTY and alphabetical arrangements,
lower/upper case, and separate symbol/mark pages. Those source files are the
layout and interaction reference. Raw GameCube character values cannot be copied
to N64: punctuation and symbols use different encodings.

Target behaviour:

- A 10×4 QWERTY grid with lower/upper case, space, newline where permitted, and
  an explicitly mapped N64 punctuation page.
- Stick and D-pad navigation, A to enter, B to delete, a clear finish control,
  and labelled case/page controls adapted to the N64 controller.
- The same field restrictions, string-edit callbacks, cancellation behaviour,
  cursor accounting, and save structures as the N64 editor.
- Name, catchphrase, song, mail, and board editors must all share the new input
  implementation; a name-screen-only mock-up is not a replacement keyboard.

Required engineering before enabling the grid:

1. Map the N64 editor's movement, command dispatch, state fields, and drawing
   callbacks against the decompiled GameCube equivalents.
2. Implement grid selection and character mapping independently of string edits,
   with tests for boundaries, held-input repeat, case, restricted fields, and
   transitions between pages.
3. Compile the new movement/drawing code with the pinned MIPS toolchain. Replace
   or extend the overlay deliberately, regenerating affected relocation records;
   never repurpose unverified RAM or assume Expansion Pak memory exists.
4. Supply a readable grid/panel using N64 display lists and existing font drawing,
   and budget both graphics commands and overlay memory in four-MiB mode.
5. Exercise all editor callers and save/reload paths in the emulator, then on
   original hardware. Keep the native English-first variant for comparison.

The grid is designed but not implemented. The current option does not claim a
GameCube-equivalent layout or the GameCube's larger saved-name capacities.
