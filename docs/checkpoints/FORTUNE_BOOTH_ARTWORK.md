# GameCube New Year fortune booth

The separate `build/fortune-booth-artwork-01` candidate installs the supplied
English GC fortune-table model in the existing N64 texture storage. Its two
textures, two palettes, 51 vertices, and thirty triangles fit without changing
the streamed allocation. The native actor, collision, shadow, fortune outcomes,
calendar rules, and saved formats remain unchanged. The town shrine remains
the native shrine.

Untitled ROM SHA-256:
`69c695c746959f9c3f5b2bda3d56020ce24fdd7a1ec341285ea9696f0738c7c4`.
UPS SHA-256:
`478c69fdb810e60a9b7aac2cc514144340db143de6a39624065b9447bf7432b7`.
The title combination is
`build/title-fortune-booth-combined-01/animal-forest-title-preview.z64`, SHA-256
`a4e6f42db32af3031b630decfd73ea0c42b6cb910d02b15a6a4d9eb9c5acbf7a`;
its UPS SHA-256 is `91fc03cae191f1328115bf02fcb1fac7137b5fc4b81976221e16912b60f74a3a`.
The combination requires an Expansion Pak and retains the conversation fixes,
complete prior translation, menu/keyboard/title work, and all earlier building
artwork. The packaged playtest remains separate during this artwork batch.

Three focused tests pass in 7.782 seconds. They cover independent MIPS graphics
compilation, source fixups and packed triangle decoding, exact visible palette
colours, every texture pixel and vertex, bounded segmented pointers, unchanged
actor/relocation and other resources, all 92 seasonal building streams, negative
source/installation cases, prior artwork accounting, and complete UPS recovery.
The title combination check passes in 8.277 seconds. Ordinary booth appearance,
shadow fit, event gameplay, and original-hardware acceptance remain unverified;
these host checks are not relabelled as gameplay evidence.

The full combined counter verifies the candidate and records 752,014 replaced
source characters out of 752,036, with the same twenty-two structural-tail
characters remaining. One original four-character `おみくじ` label receives
explicit source-matching GC artwork-omission credit. Neither seasonal aliases
nor extra object copies multiply its weight. Uncertain decorative shapes have
no invented transcription or count.

Continue the festival stall and remaining seasonal-prop inspection. The matching
GC festival stand has different geometry and language-neutral awnings rather
than directly interchangeable native food signs. The
[fortune-booth specification](../../specs/FORTUNE_BOOTH_ARTWORK.md) records this
completed conversion's exact source bindings and native limits.
