# Development scene-selector text

## Scope and source

Translate the native scene-selector owner's complete Japanese display text,
without enabling the menu, changing scene destinations, or invoking its actions.
The registered gamestate is not proof of ordinary player access. Its initializer
changes player state, including the loan, so do not enter it on a user save merely
to inspect wording. The normal player selector and accepted gameplay fixes are
separate implementations.

The pinned N64 `ovl_select/m_select.c` supplies the original strings and readers.
The available GC `src/game/m_select.c` also contains Japanese scene/loading
strings; this batch uses original English translations, not an invented GC
English payload match. Native BG/FG/NPC abbreviations, original scene numbers,
and existing English strings retain their meaning. Do not substitute GC-only
destinations or append GC's extra scenes.

## Bound resource and encoding

- Owner: VROM `0073F4D0`, linked RAM `80800000`, 9,584 bytes.
- Owner SHA-256: `74df018bd0d06fa32f112469292af90ca49a7613d31dcd25448a069850846208`.
- Relocation: VROM `00741A40`, 1,120 bytes.
- Relocation SHA-256: `bc96e465cc5cb9483d6822b2c7da52de2624cbff1193c72195d97b3ccc94bc44`.
- Sections: text 7,008, data 736, rodata 1,840, BSS 0; 274 relocation entries.
- Gamestate metadata: `80106E50`, 48 bytes; instance size remains `0x240`.
- String region: owner offsets `1E40..2533`, 1,780 bytes. Following jump tables
  and padding remain unchanged.

This is the native eight-pixel graphics-print font, not the game's proportional
dialogue encoding. Halfwidth kana use EUC-JP `8E` prefixes, which the printer
ignores; `8C/8D` select katakana/hiragana. Printable ASCII is drawn regardless
of that kana flag. New strings use ASCII plus explicitly checked newline breaks.
NUL termination and four-byte string alignment remain required. Unrepresentable
text, unexpected source words, unsupported controls, and changed printf
arguments are errors, never reasons to truncate.

## Complete translation

There are 101 source strings: 76 contain Japanese and 25 already have English,
formatting, or neutral content. All 76 receive English. The 35 scene entries
contain 32 Japanese labels and three existing English labels. The other 44
Japanese strings comprise twelve loading messages plus 32 setting labels and
values, including retained event types not currently selected by the drawer.

`tools/scene_menu_text.py` records every original/English pair, and the generated
receipt lists every original and installed string offset. The translations
include full field/test/indoor/river/shop destinations, weather, gender, clothing,
sting/decoy state, face types, and event types. `Bﾒﾝ` in the loading joke is
translated as `Side B`, not the source comment's `B menu`. The final loading
message preserves both repetitions of the no-rush and take-a-break phrases.
Already-English display strings, scene IDs 0–34, and callbacks remain intact.

Repack the string region to 1,520 bytes, leaving 260 zero-filled bytes in the
same allocation. Update all 101 actual string references: 69 data words and
32 instruction HI16/LO16 pairs, retaining their existing relocation records.
Reject an interior pointer or an unreferenced/missing source string rather than
guessing a target. No section, owner, relocation, BSS, or instance grows.

## Layout

The only non-pointer instruction change is at `80800F6C`:
`24050005 → 24050001`, moving the scene-list origin from column five to one.
Complete labels, including three-character numbered prefixes, occupy at most
22 columns and end before the unchanged settings column 23. Fifteen visible
rows, selection colours, scrolling, and controls remain native.

Settings retain their original origins. Full weather/face/gender values fit
their existing rows. The event value is on the following row, beginning at
column 23, to accommodate complete values such as `Black Panther` and
`General Store`. The runtime still selects the native first event entry;
translation does not activate unfinished event controls.

The long repeated loading message uses two lines at column ten. Gfxprint resets
X to its offset on newline, so the second line includes ten leading spaces.
The other loading messages keep their original single-line origin. No message
selection, randomization, timing, or game-transition instruction changes.

## Verification and limits

Check complete source text, format arguments, direct native readers, all source
references, original callbacks/destinations, and grid bounds. Check relocation
at `801A6010`, `802F8010`, and `803D0010`, including signed-low-half carry.
Full ROM reconstruction retains every other resource and the RC7 corrections;
the original-ROM UPS must reproduce the entire image.

These are construction and grid-layout checks, not actual native drawing or
ordinary menu-access proof. Keep the user's accepted save/reload and reported
fixes closed. Do not launch the debug initializer or create another gameplay
harness solely for these labels. This patch adds no save-format, save-reader,
menu-access, allocation, or control-flow change.
