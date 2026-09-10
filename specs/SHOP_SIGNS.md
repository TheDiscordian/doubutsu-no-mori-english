# Small shop signs and keyboard hints

## SOLD OUT

The supplied English GameCube asset is `.data:00399280`, 32×32 tiled CI4, with
palette at `00399260`, twelve vertices at `00399480`, material at `00399540`,
and geometry at `00399588`. The native destination is VROM `0140F6D0` inside
`0140C000`, a 16,144-byte shared item object. Native palette `0140F6B0`, vertices
`0140F520`, texture load `0140F638`, and vertex load `0140F688` bind the reader.

All twelve positions, texture coordinates, and lighting values match the donor;
native vertex flags remain unchanged. Every visible used palette colour matches.
Losslessly untile and replace only the 512 texture bytes. Do not replace models,
palettes, or neighbouring items. The native loose seed packet at `0140F000` is
already identical to GameCube `.data:0088F2E0` and is not an untranslated change.

## Grid hints

The compiled grid contains ASCII control hints, but the native font uses `2B`
for a heart, `2F` for a music note, and `5C` for plus. Convert only two bound
label strings at overlay offsets `6F00` and `6F4C`. Replace the two plus bytes
with `5C`, and replace the slash between `Stick` and `D-pad` with a space.
All string lengths, positions, code, and allocation remain unchanged.

`tools/keyboard_grid_labels.py` binds both complete image hashes. The shared
grid verifier recognises only that exact corrected image, restores its three
reviewed data bytes for compiled-profile verification, and retains every other
check. An unknown changed image is never normalised into an approved one.

The completed shop-sign candidate retains all Nookington, screen, keyboard, and
conversation work. Verify all current resources, actual shared grid ownership,
native glyph meanings, rejected unrelated changes, and UPS reconstruction.
Further ordinary appearance and input acceptance remain separate from these
host checks. The keyboard's incomplete native test is not promoted by this
data-only label correction.
