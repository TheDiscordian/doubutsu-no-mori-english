# Ordinary spaces in the name-entry window

## V1-19

V1RC3 correctly inserts ASCII space `20` and advances the proportional caret,
but the shared name-window overlay retains a separate native marker pass.
At linked RAM `808847AC`, instruction `17010030` branches past the marker for
non-space bytes. Spaces instead reach the drawing block at `808847B4`, which
places the `SP` model `0C016E90` at twelve pixels times the byte index. That
position no longer agrees with the proportional text.

The English GameCube `src/game/m_ledit_ovl.c:mLE_set_dl` draws this marker only
for `CHAR_SPACE_3`, a distinct wide-space code (`211`). Its ordinary `CHAR_SPACE`
is `32` and draws blank. Preserve that ordinary-space presentation, not the
native fixed-width marker. The N64 saved encoding is not replaced with GC codes.

## Correction and invariants

Require the exact V1RC3 cartridge. Change only the branch at `808847AC` to
`10000030`, an unconditional branch to the existing next-character block at
`80884870`. Retain the original delay slot, character-loop bounds, segment
restoration, text draw, proportional caret, all five name-window modes, and
all input/save code. This is VROM `0078BFB0`, offset `046C`; its allocation and
relocation resource stay unchanged. No relocated word occupies this instruction.

The replacement disables this name-window-only marker pass for all bytes;
ordinary names have no separate wide-space input encoding. Do not change the
grid's Space key label, mail/notice rendering, saved names, or shared font.
All other DMA resources, including RC3's font and transition fixes, are retained.

## Focused verification

Check the native control-flow binding, original delay slot, branch target,
relocation exclusion, complete overlay/resource retention, and UPS reconstruction.
Exercise the marker branch with spaces at the beginning, middle, and end of
bounded names and mixed-width text, preserving the input. Confirm that the
original branch reaches its marker only for spaces and the corrected branch
does not. Keep actual native drawing and hardware results distinct from these
instruction checks. Saved formats remain unchanged; no completed ordinary
save/restart test is implied by a drawing-only correction.
