# English Controller Pak labels

Done, Free, Notes, and Pages replace four native Japanese images using complete,
unscaled native Latin glyphs. All fit their original 32×16 or 48×16 I4 slots.
The GC editor is an unused stub without matching donors; the existing UI label
compositor supplies these N64-specific words. No font atlas, graphics command,
geometry, Pak operation, filename reader, numeric field, or save format changes.
See [the specification](../../specs/CONTROLLER_PAK_ARTWORK.md).

Three focused checks pass in 6.868 seconds: independent pixel-column comparison
for every complete glyph, unchanged readers and all other asset bytes, exact
installed-text credit and rejection, and complete cartridge/UPS retention.
Sixteen counter unit checks pass in 0.027 seconds. The title combination check
passes in 8.396 seconds, retaining the English birthday renderer and every
earlier fix, with identical title/Expansion Pak warning code and assets.
This data-only change does not require repeating unchanged native storage or
drawing probes. Ordinary Controller Pak navigation remains playtest work.

Untitled ROM: `build/controller-pak-artwork-01/animal-forest-halfwidth.z64`.
ROM SHA-256:
`e6511dfe0a51b75f8764eeed0159a31ee651f6d650075f42501977b0ea1d8483`.
UPS SHA-256:
`688309d3ead8defe2cf2164526b65831611b57d4093bf73462c2381bb3b6b135`.

Combined ROM: `build/title-pak-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256:
`d74b8999ed97206f9358597d66de105677af41ee4d4dbd9fcdbff467e38e23d4`.
UPS SHA-256:
`6bb899264b10fb0f59bb8dc1c9c2e843a8984c82b1bdb7948a6e26d4b61ae7ef`.
The combined 32-MiB cartridge requires an Expansion Pak. The ordinary four-MiB
heap, both Nook conversation corrections, Shrine wording, birthday window,
complete earlier English, and corrected grid are retained. Older candidates
and user saves remain untouched.

Continue embedded menu text and remaining decorative artwork. The old radial
keyboard's ten labels already have English replacements in the assembled ROM;
Japanese images decoded from the original cartridge are not evidence that
those labels remain untranslated. Do not repeat that completed label work.
