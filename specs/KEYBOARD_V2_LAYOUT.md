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
R Space occupies the upper-right shoulder, with Z Page below the key tray.
The C-button cluster and Cursor caption sit above the A/B Type/Del section on
the right. Captions and button-letter press feedback move with their artwork.

## Drawing and ownership

Reuse the verified GC frame textures without pixel edits around the key grid
at `(52,128)`, width 184 and height 76. Seven grey shells support the stick,
case/space shoulders, page indicator, typing/deletion buttons, caret buttons,
and page/completion controls. Each uses a shared 16×16 I4 quarter-circle
generated analytically with 8×8 coverage samples per texel. Nine-slice drawing
and bilinear filtering retain smooth curves at each shell's corner radius.
The native I4 combiner uses the sixteen coverage levels for soft alpha and
edge shading, without a separate bright top stripe. The shells and tray use
primitive `(223,226,230)` and environment `(174,177,181)` for grey plastic.
No native button, font, or tray pixels are edited.
Draw shells before the key tray so their joins sit underneath its rim. All
parts follow the existing menu slide coordinates and reject off-screen shapes.

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
