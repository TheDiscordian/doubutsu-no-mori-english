# V1 keyboard follow-up

## Scope

Correct V1-14: GC frame corner placement/orientation, hints outside the visible
frame, key-label positioning, and two sparse symbol pages. Retain accepted
sounds, all forty GC key positions, native controls, the proportional editor,
saved capacities, and font pixels. The grey N64-controller design and stick
image belong to [V2](KEYBOARD_V2.md), after V1 completion.

## Frame and hints

Use the exact supplied GC `kai_sousa_mojiban_tex` and `kai_sousa_mojiban2_tex`,
converted from tiled IA8 to native IA8. Keep GC colours, transparency, clamping,
and the native 236×114 adaptation. Bind all sixteen donor vertices at
`.data:0041FFF0`, not only their triangle indices.

| Corner | Texture | Native bounds | Initial S/T | S/T direction |
| --- | --- | --- | --- | --- |
| Lower left | B | 42,170–160,227 | 0,0 | positive, positive |
| Upper right | B | 160,111–278,168 | 2048,1024 | negative, negative |
| Lower right | A | 160,168–278,225 | 2048,1024 | negative, negative |
| Upper left | A | 42,113–160,170 | 0,0 | positive, positive |

The donor's right pair is one pixel higher at its 73-pixel height. Round its
scaled displacement to two pixels. Both bottom hints are centred at X=160,
at Y=200/212 and scale 0.75; measure their complete native-encoded text. Check
the visible glyph ink against frame alpha, not merely its outer rectangle.
Keep page/case/order hints, accepted N64 bindings, and native plus encoding.

## Key labels

Derive origins from the installed native font and installed extended sun/skull
pixels. Centre the intensity-weighted horizontal ink at key X=7.5, rounded to
quarter pixels, with bounds constrained inside the key. This moves `0` right
and the right-heavy `1` left relative to advance-based placement.

Preserve vertical punctuation relationships. Use the original GC Y origin for
ordinary glyphs and lift low marks only as needed to fit. Underscore's native
rows 14–15 move to rows 13–14; they remain below letters, not vertically centred
like a hyphen. Full-height symbols retain every row. Do not resize or edit
global font artwork. The table contains two signed quarter-pixel coordinates
for 256 native and two existing apology-only extended glyphs.

## Page consolidation

The two original symbol tables contain 24 distinct supported codes. Keep their
donor ordering, deduplicate, and pack the non-space/non-return keys first.
Return stays at cell 29 and space at cell 39. Unsupported cells remain disabled;
sun/skull remain restricted to apologies, and Return to multi-line editors.

Only two controller instructions change: validity `8088AC0C:2C630003` becomes
`2C630002`, and modulo divisor `8088B074:24030003` becomes `24030002`.
The existing division/branches and every function address stay. Patch the
80-byte table at editor offset `27776+320`; retain the now-unreachable marks
storage so all following code/data addresses remain unchanged. The transient
page index resets if invalid and is not a saved field.

## Ownership and verification

Recover the verified 30,272-byte prefix from the current editor by restoring
its original draw call and retaining its 542 relocations. Replace the owned
background suffix instead of appending a second copy. The finished owner remains
at VROM `03E70000`, with relocation `03E80000` and linked RAM `80885140`.
Its metadata remains in `007749C0+2B50`. Growth fits the existing 8,192-byte
reservation; do not change the pool immediate `25CE7620` or consume another
reservation. Confirm retained editor behaviour at load bases `80200010` and
`80378010`, including the low-half carry.

Build after the complete text/HUD follow-up. Reconstruct the whole cartridge,
retain every unrelated resource and DMA identity, and verify UPS application.
Focused tests compile independently, exercise page input with address/undefined-
behaviour sanitizers, bind actual pixels/placements, and check complete retention.
A bounded native drawing probe checks emitted rectangles/materials, native
loading/matrix calls, graphics limits, save data, and memory guards. It does not
replace ordinary screen appearance or original-hardware acceptance.
