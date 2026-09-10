# Accented item implementation

## Completed foundation

The exact separate sixteen-cell font resource is built in `build/accent-glyphs`.
Its SHA-256 is
`24ae623d2917a2370ec70504daf372be327c830d24fb37bacc68ad84f0bbe90e`.
The fourteen preceding cells and every original native atlas pixel remain
unchanged. Added ñ/Ñ cells use the verified donor codes `87/12` and six-pixel
advances. Existing five/fourteen-cell profiles still validate independently.

The complete font/world-label artifact in `build/accent-font` is 4,576 bytes,
with a 464-byte relocation table: sixteen additional image bytes. Independent
builds agree. Its image SHA-256 is
`f6fc16ac0f62ad4f6be19bd372dc45fcac35b0810d6e9a23ac71a5a4c09addff`;
relocation SHA-256 is
`0f137f772732eeef360aecb807de2b1e0f5f1b720db040c96799d13ccaca8d61`.
The pinned profile verifies source/imported world-name code, complete hook tables,
resource mapping, relocation bounds, and prior font capabilities. Candidate-only
compiler measurements carry a marker that production validation rejects.

`tools/accent_items.py` prepares all eight source-bound fields: café shirt and
its four placed rotations, Pokémon Pikachu, Café K.K., and Señor K.K. It verifies
the actual donor table bytes, exact native hashes, full spelling/encoding, and
the placed/carried conversion. All 4,536 preceding English resource fields stay
unchanged. The candidate resource SHA-256 is
`693ef2c0749822d07062114ffff0b35b4bb8a56d3b2617c932d9220dcc92165b`.
It is deliberately not installable through the ordinary resource installer.

Three font tests and two item-candidate tests pass, including sanitizers,
complete cell comparisons, all byte-code bindings, old-profile rejection, full
resource retention, and capacity/source failures. Eight of nine existing glyph
regressions pass. The remaining legacy fixture rejects its obsolete
`build/runtime-module` source inventory before constructing a native scenario;
no resident source changed in this batch. Do not rebuild an obsolete prototype
or repeat that fixture instead of completing the current integration.

## Active integration

Accented fields remain uninstalled and receive no translation credit. The
current playable build remains `build/apology-input-pilot`.
The [accent specification](../../specs/ACCENTED_ITEM_NAMES.md) requires a new
immutable letter-assembly identity for captured accent pairs, complete restoration
and line widths, and a matching creator extension. Existing catalogues and their
saved meaning remain unchanged. Add these consumers in checked owned code before
enabling the full item resource, then verify the actual combined installation.
Do not globally permit glyph pairs in player/town/custom editor input.
