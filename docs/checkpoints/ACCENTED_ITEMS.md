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

The catalogue-five core and treasure-notice adapters are implemented in
`overlays/accent_mail/`. Seven focused host tests pass: exact capture, full
assembly/restoration, accented capitals/articles, old interpretation retention,
malformed-input rejection, atomic generation/startup, line widths, and complete
treasure packing/reading. The native 122-byte mail snapshot and 96-byte notice
envelopes remain unchanged. All sixteen catalogue-two sale templates are verified
identical to their catalogue-five counterparts before allowing an accent upgrade.

`build/accent-mail-font` is the production-validated compiler artifact, not an
installed ROM. Two independent candidate compilations match it. Its image is
11,344 bytes, with 672 relocation bytes; the existing loader needs 12,031 total
allocation bytes. Image SHA-256 is
`f2bbd23684cb682ef38712e6d2dc5b5b971b5f8ec2c1e2feb756b09631078d98`;
relocation SHA-256 is
`6c9fda4a52beb4dfbe5aa57e1e39693f2ce2d67be8edcc26e24048216a11d657`.
This includes shared capture/generation and four startup-installed resident mail
hooks; treasure-specific adapters remain on-demand integration work. Both
compiler-profile/article-resource tests and three preceding accent-font tests
pass. No native execution of this new mail core is claimed yet.

`build/accent-mail-catalog` retains every catalogue-four payload and registers
catalogue five/semantics three. SHA-256 is
`26b2e95b10b8ae049853ecc6180e41c12b86efc677e39ee03f9742077e9005be`.
`build/accent-item-articles` changes only the five accented-name article/checksum
rows and their bound full-name hash. SHA-256 is
`b218119460fdbb472e641cbbc6d77ff809d489bda8b8622f0157562294d575ff`.
All existing catalogues, source translations, and article rows remain intact.

Next connect the shared creator's capture/generation entries, its treasure
packer/validator/decoder and article resource, the separate sale-event creator,
and the notice reader. The actual preceding creator is `build/design-items-creator`,
not the older seasonal prototype. Preserve its full 58,144-byte prefix except
the exact new entry/data patches. The current board reader is 24,304 bytes;
retain its native owner/cache and update the checked submenu-pool budget for any
appended code. Complete combined installation/resource verification before
enabling the eight full item fields. Do not globally permit pairs in custom input.
