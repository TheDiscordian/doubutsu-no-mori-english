# Compact keyboard tray and attached controller sections

## Scope

Build on the exact V2-08 cartridge, retaining the museum and credits corrections.
The centre grey GameCube-derived frame contains only the unchanged forty-key
grid. Controller artwork lives on distinct attached sections around the tray,
not inside one enlarged rectangle. Keep the N64 palette, directional stick,
pressed-button feedback, optical letter alignment, sounds, and all bindings.
The attached parts remain N64-inspired, with grey shells, blue A, green B,
four yellow C buttons, native shoulders, and the N64 stick. The GameCube
reference guides the separated layout, not the controller design.

Remove the visible `L+A: Alter` and `L+Z: ABC` combination hints. Keep those
shortcuts operational, along with ordinary case/page controls and the current
page indicator. This is presentation work, not an input or save-format change.

## Drawing and ownership

Reuse the verified GC frame textures without pixel edits around the key grid
at `(52,128)`, width 184 and height 76. Seven code-drawn grey shells support the
stick, case/page shoulders, page indicator, typing/deletion buttons, caret
buttons, and space/completion controls. Rounded shoulders and tapered left,
centre, and right grips use sixteen contiguous shaded bands each; one-cycle
RDP rectangles have exclusive lower/right edges. Draw shells before the key
tray so their joins sit underneath its rim. All parts follow the existing
menu slide coordinates and reject out-of-screen rectangles.

Preserve all 30,272 input/editor prefix bytes except its existing four-byte
drawing hook. Recover the checked prefix solely for suffix compilation. Retain
every unrelated resource, including V2-08 credits and museum code. No original
save or preceding build is overwritten. Stay within the existing 8-KiB rounded
suffix reservation and drawing-buffer budget; fail rather than silently grow.

## Verification

Bind the exact current ROM, editor, relocation, retained font metrics, native
button artwork, complete input prefix at multiple load addresses, size metadata,
and full original-ROM UPS reconstruction. Inspect the new layout in ordinary
name entry on the new build, including neutral, held controls, and another
page. Use one bounded native batch and one justified setup retry if needed;
do not rerun old candidates or the completed K.K. performance. Saved formats
stay unchanged, with expected compatibility in both directions and no migration.
