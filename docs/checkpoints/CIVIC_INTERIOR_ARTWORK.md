# English police and post-office interior artwork

## Implementation and artifacts

The [civic-interior builder](../../tools/civic_interior_artwork.py) installs the
matching English GC wanted poster, recruitment poster, and postal mailbag
texture. Their lettering reads `WANTED!`, `I want U!`, and `MAIL`. The
[specification](../../specs/CIVIC_INTERIOR_ARTWORK.md) records source/native
addresses, actual donor bindings, geometry comparison, and counting rules.
Lucky-bag decoration is a different asset and remains Japanese.

Untitled complete build: `build/civic-interior-artwork-01`.

- ROM SHA-256: `f3cf110b4a0609af42ed06ac739abd8e9b50de44db250d6e7e0df9c58b979f51`.
- UPS SHA-256: `34db96c8e3104b341135a4c4ae8d893185a0b766eea66e536a63197e1ae5685a`.
- Report comparison SHA-256: `c6563548be3b387ae578e8b18b5affd2438618be4fd877b1faebb25b11947d19`.

Combined title build: `build/title-civic-interior-combined-01`.

- ROM SHA-256: `a8072a76783317215ae85afbf31cca77422d5b783512194d8269004f31073780`.
- UPS SHA-256: `7398d8d3c3bd3b7e234057daabbf61684811e367be583ec4d82045dae2d624bd`.
- Canonical title report SHA-256: `f851e26b4b448f030b0431e9245f6c6ba675a4cdca0d34368ad4f9ddbde57e19`.

The complete modified room hashes are:

- Police, `012AC000`: `5af206c43df22cf314b47a7244da27c19ea8f81eba8e6e2fd646d187c5c8248b`.
- Post office, `012BB000`: `b3cc4ec16c0f26e87976381be72d79ef7db00b16f79c005452eec2198f489f96`.

## Focused verification

Four asset/reconstruction/counter/rejection tests pass in 7.693 seconds; the
subsequent title-retention test passes in 1.614 seconds. Seventeen shared counter
unit tests pass in 0.033 seconds, including the new Japanese postal-symbol rule.

- Decode and inspect the three complete native and English donor images.
- Verify all seven actual REL texture/palette/vertex bindings and pinned sources.
- Require every installed visible pixel and alpha value to match the donor.
  Preserve all native palette bytes, including unused and transparent entries.
- Verify both native four-vertex posters against their respective halves of
  the GC eight-vertex load, and all ten mailbag vertices/six triangles. Native
  and GC UV/lighting bytes match. Native geometry and commands stay intact.
- Reconstruct the UPS and verify all DMA identities, sizes, and unrelated
  resources. Only the three texture slots change inside the two room owners.
- Compare the complete title-combined candidates: only those two room owners
  and rebuilt DMA-table owner `00019D40` differ. Physical boot, title, keyboard,
  runtime, earlier artwork, conversation fixes, and saved-format code remain.
- Reject altered texture, palette, vertex, native reader, source, and report
  data; an English-looking report cannot credit an unchanged Japanese room.
- Count 19 original source characters once across the three images, with zero
  new credit in the predecessor and complete credit after verified installation.
  The Japanese postal marker U+3012 contributes one character, not the English
  word's length. Arbitrary Latin/symbol images remain rejected by the counter.

No new native harness, emulator launch, desktop preview, audio, or user-save
mutation is used. Ordinary room appearance remains human playtest work.
The GC post-office card reader has no matching native feature in this batch;
inspected native counter/wood panels remain unchanged. Tiny lower poster marks
are retained as in the English donor, without invented transcriptions.
