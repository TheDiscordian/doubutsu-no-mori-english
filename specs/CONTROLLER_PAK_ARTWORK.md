# Controller Pak label images

The native Pak editor displays four Japanese label images. Replace them with
Done, Free, Pages, and Notes. The supplied GC `m_cpedit_ovl.c` has no corresponding
screen implementation or English image donors. Preserve N64 note/page terminology;
do not substitute GC Memory Card handling or terminology.

Asset `00B1A000`, 65,440 bytes, SHA-256
`b8c26e67da2581f021d4bc24c91d7870e87bb628f1f4cd89e5c395e0dd31b1bc`.
Owner `007A10E0`, RAM `808A4780`, 5,952 bytes, SHA-256
`f9a10c58f1e989df18a9f0b5ab6622792e0f01b50a56336711f54ca5950bf22f`;
its asset start/end pair is at offset `1730`.

| Japanese | English | Image offset | Dimensions | Load / quad offset |
| --- | --- | --- | --- | --- |
| オワリ | Done | `7560` | 32×16 | `6BA8` / `5D70` |
| のこり | Free | `BAE0` | 48×16 | `7270` / `60B0` |
| ページ | Pages | `B960` | 48×16 | `72C0` / `60F0` |
| ノート | Notes | `76E0` | 48×16 | `7370` / `61F0` |

All images are I4 with a single texture reader. Use `keyboard.label_pixels`,
the existing deterministic UI label compositor, with the verified original
Latin glyphs. Remove only empty outside columns, retain every ink pixel, insert
one empty column between characters, and centre the complete word. No scaling,
font-atlas changes, or new font assets are needed. The words occupy 31, 28, 36,
and 37 pixels, respectively, and fit their existing allocations. The donor font
at `00BCD000` has SHA-256
`dbb3590b722a4cc463f40288d93c2978a12156ec697439e0d3b0d1f985ae43f4`.
This donor does not replace the installed halfwidth font or alter its spacing.

Keep every display-list command, vertex, colour, numeric position, separator,
existing No. label, and Pak filename font unchanged. Done retains its native
36×18 display quad; the other labels retain their 36×12 quads. All Pak listing,
selection, deletion, note/page counts, save operations, CPU code, and loaded
allocations remain unchanged. Cartridge retention and patch reconstruction must
pass. This data-only batch reuses unchanged native drawing/storage behaviour;
it does not imply ordinary menu or hardware acceptance.

The four visually transcribed source labels join the shared text inventory.
Bind original texture hashes and require the complete installed English asset,
profile, and unchanged owner before granting credit. Earlier builds retain all
twelve Japanese source characters without receiving installation credit.
