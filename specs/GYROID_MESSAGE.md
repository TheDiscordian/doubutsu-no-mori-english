# Home-gyroid owner-message display

## Verified scope

The routine called `mMsg_Set_mail_str` at `8009DA94` is not a stored-letter
reader. Its two identified direct callers supply sixty-four ordinary text bytes:

| Caller | Call address | Actual source |
| --- | --- | --- |
| `ovl_Sample` | `809340EC` | Static demonstration text at linked address `80934660` |
| `ovl_Haniwa` | `8096B368` | Home-gyroid owner message at `house_haniwa+18` |

The gyroid obtains its home record from the actor's home index, saves that
pointer at `sp+20`, and reloads it into `a2`. The call's delay slot adds `18`.
Neither call passes `Mail_c` or an NPC's stored letter. Snapshot decoding must
not be attached to this routine based on its name.

`tools/gyroid_message.py` checks the complete caller-file hashes, both argument
instruction sequences, the complete native setter hash, and individual native
capacity instructions. The broader mail audit independently inventories the
two direct calls and aligned literal references. Neither inventory claims to
prove all indirect or inline uses.

## Native and English contracts

The N64 setter accepts slot zero, writes exactly sixty-eight bytes at message
window offset `132`, preserves explicit `CD` newlines, and pads with spaces.
It clamps the source length to sixty-eight; zero/negative lengths clear the
destination to spaces. Invalid slots or null source pointers do not write.
Its original automatic wrapping inserts a newline every sixteen characters.
Both identified callers pass only sixty-four bytes. The saved owner message
and its editor still have that limit.

The supplied GAFE01 setter uses a 132-byte destination and measured glyph
widths. It appends a glyph, then inserts a newline when accumulated width is
strictly greater than 186 pixels. An explicit newline also resets width.
Both engines stop at their destination limit or fifth line break. Those limits
are not a word-reflow algorithm, and they do not remove manual line breaks.
Disassembly of the supplied 300-byte PowerPC function confirms the 132-byte
capacity, width call with proportional mode one, strict 186-pixel comparison,
and five-break limit.

The resident `af_set_gyroid_message` implements the GameCube width rule within
the unchanged sixty-eight-byte N64 destination. It uses the actual native font
width routine, so the approved proportional metrics determine wrapping. At
most twelve pixels per ordinary glyph means at most four automatic newlines
for the real sixty-four-byte sources, fitting the original destination.
No saved field, editor, asset, or font metric changes. The native row limit is
preserved; longer source imports remain disallowed.

Output is staged in sixty-eight stack bytes before publishing, also making
overlapping source/destination safe. Invalid widths publish nothing. A null
window is additionally rejected. There is no mutable resident display state.
The compiled function's frame is 128 bytes; its native width calls add their
own frames. This is not a measured whole-game stack limit.

Installation changes only the original setter's first two instructions to an
entry jump and empty delay slot. The whole original function is checked for
external interior references. The native dialogue insertion at `8009F670`
continues reading the same sixty-eight-byte field and retains its existing
trailing-space trim. Its saved text is not rewritten.

## Reference and test evidence

Native setter SHA-256:
`76b06b4d5b721d9f68e5bcf38dd64d3624743d7a0080af6d2a8f06cabdf9e998`.
GAFE01 setter executable SHA-256:
`0afbe1fcd52acfe582012d9d1aedbd41dfc6e4a898d4638dd3a86f5d15ab19d5`.
Pinned reference function source SHA-256:
`06cccec1dfb711fa72b731063f8eeb11d08b32665292e9439d6cd889bc9d7ab0`.

Host tests cover all 256 source bytes, every source length through sixty-eight,
manual/blank lines, spaces, exact width thresholds, invalid inputs, source
overlap, and independent instruction-guard mutations. Three thousand varied
cases compare against the extracted, unchanged GameCube C function, compiled
locally with the native destination layout/capacity and a controlled width
provider. This is a source-level comparison, not execution of the GameCube CPU
code. Extracted reference source remains ignored and temporary.

`tools/gyroid_message_test_scenario.py` checks the installed N64 entry and real
dialogue insertion, full destination/source guards, exact message-buffer
capacity, and checkpoint restoration. Actual executed results and hashes live
in the work log. Ordinary other-owner gyroid interaction and saved custom editing
remain required. The installed complete English
[default-message design](GYROID_DEFAULT.md) uses the four strings actually
selected by GameCube initialisation, not the older same-ID eighty-eight-byte
concatenation. Default substitution preserves saved storage; owner-editor
presentation and the larger custom-message representation remain unfinished.
