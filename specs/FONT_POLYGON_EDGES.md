# Polygon font filtering borders

## V1-17

The user reports clipped left-edge columns in names/options and extra bottom
pixels on descenders such as `g`, while speech generally looks correct.
Names/options reach native polygon drawing at `800911E8`; speech reaches
rectangle drawing at `8009113C`. They share glyph pixels and measurement but
do not share rasterisation. The narrowed Latin atlas places ink in column zero;
some descenders occupy row fifteen. The native polygon bounds provide no
transparent margin at these edges. Fractional placement/scaling can clip the
left filter footprint and clamp the descender's last row.

An isolated comparison with unchanged glyph pixels shows improved edges when
polygon samples include a transparent border. Simple S/T half-pixel offsets do
not establish a matching correction. Preserve native projection and caller
matrices; do not change animation, text origins, or character advance widths.

## Correction

Append immutable 16×18 I4 copies for the 81 halfwidth Latin glyphs and sixteen
installed extended glyphs to the existing persistent font owner. Copy each
12×16 glyph into columns 1–12 and rows 1–16; every other sample is zero. There
is no resampling, changed ink, or modification to the original atlases.

Hook only polygon drawing. Grow its quad by one source texel on each side,
using the caller's X/Y scale, and sample the bordered texture with clamping.
Retain four vertices and nine graphics commands per glyph; no extra per-frame
texture allocation is permitted. The caller's measured advance remains exact.
The original polygon routine is retained as a checked fallback for other
native glyphs and nonstandard dimensions. Its copied instructions must contain
no internal absolute jumps or PC-relative branches.

Preserve the complete previous font owner and relocation records, changing
only its entry jump to a chained installer. The installer verifies the native
polygon entry before calling the previous installer and adding its own hook.
The existing CRC-checked font loader owns the enlarged persistent image. Raise
only its image-size limit from `3000` to `7000` hex, retaining alignment, CRC,
relocation, heap bounds, allocation failure, and cache-maintenance checks.
The new limit must fit a positive signed MIPS immediate. Do not alter saved
formats or require a new per-frame heap allocation.

## Verification

Bind the exact V1RC2 input, current font, complete native polygon function,
module limit word, font configuration, and source glyph hashes. Reconstruct
the complete cartridge and UPS without changing other resources. Independently
relocate the retained prefix and new installer at two load addresses. Check all
97 padded glyph interiors and borders, installed code/data, and unchanged
speech and measurement paths. Use one bounded native check of installation,
both drawing paths, emitted vertices/commands, memory guards, and save retention.
Ordinary appearance and original-hardware acceptance remain separate.
