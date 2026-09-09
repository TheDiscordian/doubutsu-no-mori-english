# Complete English owner-message editor

## Current implementation and save contract

`runtime/hboard_editor.c` implements an overlay-owned editing core, separate from
the visitor-message formatter. It is compiled and host tested, but not installed
in the current cartridge. The [checkpoint](../docs/checkpoints/HBOARD_EDITOR.md)
records the evidence and remaining integration. The complete project still needs
normal editing, persistence, gameplay review, and hardware acceptance.

The native home-gyroid message occupies exactly 64 bytes. Held Bells immediately
follow it; enlarging the existing write would corrupt that value. Do not borrow
unknown home bytes or silently truncate custom text. Keep the original save
format and native 64-byte custom-message capacity. This capacity is independent
of the keyboard grid and the proportional font.

The complete GameCube default is the source-bound 92-byte greeting in
[GYROID_DEFAULT.md](GYROID_DEFAULT.md), with three manual newlines and no trailing
space after its final period. A private 128-byte, space-padded draft holds the
entire greeting. Exact matching of all 64 saved default bytes selects that draft;
every custom byte, including non-Latin text and padding, prevents substitution.
Opening, cursor movement, and editing do not write to saved memory.

Confirmation has two permitted representations:

- The exact complete English default maps back to the canonical native default.
  The visitor selector and subsequent editor opening recognise that representation.
- Custom text fits in the native 64-byte field after removing only its unused
  trailing spaces. All internal spaces and explicit newlines remain. The field
  is space padded, without altering adjacent data.

A changed default longer than 64 bytes remains a draft until the user shortens
it or restores the complete default. The editor must label the custom capacity
and explain a rejected confirmation. A 128-byte draft is not a promise of
128-byte custom saved messages. No failed confirmation closes the editor,
discards the draft, or saves a shortened version. Exiting without successful
confirmation discards the private draft; it does not modify saved text. The
native editor normally edits the save field directly and has a Done transition,
not a separate saved-text cancellation transaction.

`af_hboard_commit` also compares all saved bytes with the opening snapshot.
If another path changed that field while editing, confirmation refuses to
overwrite it. The core exposes an explicit conflict result for the UI.

## Layout and commands

The window retains four rows, 16-pixel row spacing, and a 192-pixel line limit
from the supplied GameCube editor. Draw at scale one, using the installed native
proportional advances. These rules do not change font pixels or message timing.

`af_hboard_layout` returns complete source spans, cursor column/row/pixel offset,
and the end-marker position. An explicit `CD` stays in the source and ends its
row. A glyph whose advance would exceed 192 pixels starts the next row; no
automatic break is inserted into the draft. The cursor looks ahead at the next
glyph so it agrees with the drawn row. At the end it uses a virtual padding space,
avoiding an out-of-bounds read at the 128-byte limit. There is no word reflow.
Overflow and invalid advances return errors without publishing partial layout.

The core uses native command numbers: left=1, down=2, up=3, right=4, Done=5,
backspace=6, case/ornament exchange=7, and insert=8. Done calls the separate
confirmation operation. Right at the end inserts a space; down at the end of
the final occupied row attempts a newline. Vertical movement selects the nearest
insertion boundary by pixel position, choosing the following boundary on ties.
Insertion and exchange reject a fifth row without changing the draft. Backspace
can shorten an existing overlong or malformed row arrangement. No input command
can introduce reserved bytes `7F` or `80`; existing saved bytes are preserved.

## Verified native ownership and hooks

`tools/hboard_editor.py` binds the full original files, adjacent relocation
records, submenu-owner metadata, source default, supplied executable, and
reference C sources. Generated default bytes remain ignored local resources.

| Resource | VROM | Linked RAM | File bytes | BSS bytes |
| --- | --- | --- | ---: | ---: |
| Owner-message window | `0078A560` | `808828D0` | 2,144 | 0 |
| Shared character editor | `0078CB80` | `80885140` | 14,768 | 48 |
| Submenu owner | `007749C0` | `8085BAC0` | 12,016 | 67,376 |

The window relocation at `0078ADC0` has sections `(2096,32,16,0,19)`;
the editor relocation at `00790530` has `(13248,1440,80,48,212)`.
Owner metadata rows are at offsets `2A50` and `2B50`, respectively. The exact
allocation words and all resource hashes are pinned in the audit module.

The window's opening call at `80883054` invokes `800C4DB0` with program 10,
editor mode 1, sixteen columns, and the original saved message pointer. The
owner index is submenu overlay offset `10154`. The saved message is
`80126EA0 + 4080 + owner * B48`.

The shared editor's state pointer is submenu overlay offset `106E0`.
Its native state is at linked `80888AF0`:

| Offset | Field |
| --- | --- |
| `11`, `13`, `15` | command, selected byte, command processed |
| `16`, `18`, `1A`, `1C` | cursor index, columns, maximum rows, text length |
| `1E`, `20`, `22` | exchange byte, cursor column, cursor row |
| `24`, `28`, `2C` | input pointer, end-marker callback, cursor callback |

Do not copy GameCube structure offsets: its added width fields move several
members. The native constructor's `80888484` call invokes initialization at
`8088587C`. The mode table at `80888824` selects `808862EC` for **both modes 1
and 2**; changing that shared function globally would also change notice editing.
The per-frame `808869A4` call recomputes fixed-column cursor coordinates at
`80885AEC`. Case selection at `80886168` and all other editor modes must remain.

The window's existing text/cursor renderer is `80882D08`. Its text helper
`80882B2C` caps rows at sixteen glyphs and draws without proportional mode.
The renderer calls that helper at `80882DAC`, then uses fixed twelve-pixel
cursor steps. Redirecting only the text draw cannot make editing correct.

## Remaining atomic integration

Append the core, bridge functions, source-bound defaults, width cache, and draft
to the owned character-editor allocation. Preserve the original 48-byte BSS
addresses when laying out the extension. Redirect initialization, only the mode-1
table entry, and the per-frame cursor call through scoped bridges. Other modes
retain native input, capacity, palette, and cursor behaviour. The window must
call the loaded editor's drawing bridge through a verified owned pointer, not
through its link-time RAM address after relocation.

The new renderer must use one layout for text, cursor, and end marker; retain
the native frame and portrait; and display the capacity warning without covering
the four message rows or keyboard. Only successful confirmation may invoke the
native Done transition. Initialize and clear extension ownership on every editor
entry/destruction; do not reuse a draft from a previous field or home.

Regenerate affected relocations and update the editor allocation metadata.
Audit simultaneous submenu allocations before choosing the additional pool
reservation. The seasonal notice reader already reserves an additional 20 KiB;
that reservation is not automatically spare editor memory. Its existing editor
audit accepts only the native English-first prefix, so extend verification to
recognise the exact new owned image while preserving the palette/conversion
exclusion of `7F` and `80`. Install all affected parts together and reject partial
or overlapping patches. Do not change the resident module or saved layout just
to accommodate this on-demand editor.

Native acceptance must exercise normal initialization and closing, loaded
relocations, the full default, custom message edits, every home, cursor and
display agreement, rejected over-capacity confirmation, unchanged adjacent
Bells/save bytes, cleanup, and persistence. Host comparisons and a compiled
object do not establish those results.
