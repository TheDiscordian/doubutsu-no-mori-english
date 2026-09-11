# Controller Pak note-deletion heading

## Scope

The native Pak manager keeps Japanese `コントローラパックのきろくをけします`
at owner `007A10E0:171C`, even with the four English label images and the
separate English status/error windows installed. This is a static instruction
above the note list, not the in-progress deletion message. The manager lists
individual notes; it is not a whole-Pak formatting operation.

Translate the instruction as `Erase a Pak note` (16 counted bytes). This is an
explicit N64-specific translation. The supplied GC `m_cpedit_ovl.c` retains an
empty counterpart, so no English GC heading exists to import. Keep the N64
note/page terminology and its Controller Pak operations.

## Binding and replacement

Owner `007A10E0`, RAM `808A4780`, is 5,952 bytes, SHA-256
`f9a10c58f1e989df18a9f0b5ab6622792e0f01b50a56336711f54ca5950bf22f`.
Relocation `007A2820` is 208 bytes, sections `(5808,144,0,368,44)`, SHA-256
`1ff54bf2a6f16665ae24a532b3d3e50fbdc1ba3cd568bc230b0c86f09300f02d`.
The eighteen Japanese bytes and two padding bytes occupy `171C..172F`.
Replace these twenty bytes with the complete English instruction and four
zero padding bytes. The asset pair at `1730` remains unchanged.

The actual reader uses HI16/LO16 at `808A5B4C` / `808A5B7C` and font call
`808A5B98`, targeting `808A5E9C`. Keep that pointer and both relocation entries.
Only the length immediate at `808A5B84` changes from 18 to 16. No string copy,
new allocation, reader hook, or saved data is introduced.

The native heading uses origin `(65 + menu_x, 27 - menu_y)` at 0.875 scale.
The original eighteen fullwidth glyphs occupy 189 pixels; the complete English
width is 96 unscaled, 84 displayed. Keep the original centre X 159.5 by changing
the X increment at `808A5B0C` from 25 to 77.5, making the final origin 117.5.
The two instruction replacements are `24060012 -> 24060010` and
`3C0141C8 -> 3C01429B`. Y, scale, colour, and all other drawing code stay native.

## Verification and limits

Require the exact committed town-tune correction as the preceding cartridge.
Verify the original ROM, complete owner/relocation, installed font widths,
source Japanese bytes, actual reader instructions, centred full English width,
and existing asset pair. Compare complete relocated owners at several valid
load addresses. Preserve every other resource, all RC5 and tune corrections,
note names, selected indices, deletion/confirmation/error code, BSS, and saves.
Require complete UPS reconstruction. Do not invoke Pak deletion or repair as
an automated test. Focused data/reader checks do not establish ordinary screen,
Pak operation, save/restart, or original-hardware acceptance.
