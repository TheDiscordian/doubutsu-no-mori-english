# Bounded GameCube-style festival stall

Replace the native Japanese-lettered stall with the supplied GC left-hand model,
using a reflected instance for the second placement. Retain both original actor
entry points, the native object slice and streamed size, collision, shadows,
goods, prices, calendar rules, and saved formats. This is a deliberate compact
GC-style adaptation, not a claim that the GC right-hand mesh is identical.

The exact source and native ownership are in `docs/ARTWORK_REMAINDER.md`.
`tools/stall_model_source.py` resolves all 46 actual GC material/vertex fixups,
parses both complete models, and checks their 133 triangles per variant. The
models' reflected surfaces have the same boundaries on every shared geometric
plane, including texture coordinates, colours, and normals. Sixty-seven complete
triangle faces match; the remaining sixty-six use different triangulation.
Four plane keys differ, corresponding to the small non-coplanar source detail.
Do not label this reflected layout an exact import of both GC meshes. Ordinary
appearance and lighting remain acceptance work.

The complete native slice is `92A98..95478` of object `D5E000`, 10720 bytes.
Preserve both native roots at `93348` and `95440` (56 bytes each). Both seasons
use this one slice, copied into the current `03D00000` object. No range table,
loader, object extent, or allocation changes are needed if the layout fits.

| Object offset | Planned content | Bytes |
| --- | --- | ---: |
| `92A98` | Three RGBA5551 palettes | 96 |
| `92AF8` | Native fixed-point X-reflection matrix | 64 |
| `92B38` | GC 64×64 CI4 awning/panel atlas | 2048 |
| `93348` | Left entry | 56 |
| `93380` | GC 64×32 CI4 balloon atlas | 1024 |
| `93780` | GC 128×32 CI4 pinwheel/fan atlas | 2048 |
| `93F80` | GC 32×16 CI4 wood atlas | 256 |
| `94080` | All 226 source vertices, native flags zero | 3616 |
| `94EA0` | Complete native shared model | At most 1440 |
| `95440` | Reflected right entry | 56 |

Convert all pixels and visible palette colours losslessly; do not resize the
source textures. Use explicit native texture/TLUT loads, source wrap/mirror modes,
bounded TMEM, native vertices and triangles, and independently compiled F3DEX2
commands. No Dolphin commands execute on the N64. Decode the actual source
geometry flags: lighting is `20000`, and back-face culling is `400`.

The left entry sets normal culling. The right entry pushes the fixed reflection
onto the model-view stack, selects front-face culling for reflected triangles,
draws the shared model, pops the matrix, and restores back-face culling. The
shared model changes only lighting when processing source geometry modes, so
the chosen culling survives both materials. Keep matrix push/pop balanced and
preserve the caller's model-view transform. The native actor's preceding matrix
command loads without pushing, leaving room for this single balanced push.

Compile and verify command size before installation. Reject overflow rather
than expanding a shared building slot silently. Bind the exact source slice,
both native roots, actor/relocation, current seasonal readers, palettes, and
object ownership. Preserve every unrelated byte/resource, including the earlier
fortune, countdown, fishing, dump, and Nookington batches. Reconstruct the UPS.

Japanese lettering disappears through the explicit GC artwork adaptation.
Tiny source labels without reliable transcriptions receive no invented counter
weight. This inventory limit is distinct from whether the complete replacement
model is installed. No installation or ordinary-scene acceptance is claimed
until the corresponding checks actually pass.
