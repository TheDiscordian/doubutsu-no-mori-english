# Shared GameCube-style festival stall

`build/stall-artwork-01` replaces the Japanese-lettered native stall with the
supplied GC left-hand model and a reflected second placement. The four exact
source atlases and all visible palette colours are retained without resizing.
One 226-vertex mesh draws 133 triangles per placement. The complete 1392-byte
native display list fits with 48 bytes spare. The original 10720-byte slice,
both root addresses, actor, relocation, collision, shadows, goods, calendar
behaviour, shared palettes, and saved formats remain unchanged.

The reflected variant is a compact adaptation, not an exact import of the GC
right-hand mesh. The source audit resolves all 46 actual pointers and compares
both variants: 67 triangle faces match exactly under reflection, while 66 use
different triangulation. All shared-plane surface boundaries match including
UVs, colours, and normals; four plane keys differ on the small non-coplanar
detail. Ordinary appearance, lighting, shadow fit, both placements, and event
gameplay remain unverified. Do not claim those checks from host graphics tracing.

Untitled ROM SHA-256:
`84852fae59184d6eb97d2ee94cbb44ea913680b22a31156287d5a604c048d3d3`.
UPS SHA-256:
`cc152688df6f5b39138241f395d8fabc4b5d87a3cd0b6ccea9122227abb2550d`.
The title combination is
`build/title-stall-combined-01/animal-forest-title-preview.z64`, SHA-256
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`;
its UPS SHA-256 is `600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0`.
The combination requires an Expansion Pak and preserves all earlier translation,
conversation, keyboard, title, menu, and building-artwork batches. The combined
cartridge is included in `build/releases/v1-artwork-playtest-03.zip`; the
[package checkpoint](V1_PLAYTEST_PACKAGE.md) records its standalone patcher check.

Three focused tests pass in 8.660 seconds. They independently compile the native
macros, trace all source-equivalent triangles through both installed roots,
check source colours/pixels, bound texture/vertex reads and memory, verify the
balanced reflection matrix stack and culling restoration, reject bad commands
and missing installation, retain all other resources and 92 building streams,
and reconstruct the complete cartridge from UPS. Prior Nookington, dump,
fishing, fortune-table, and countdown accounting remains valid. The complete
title combination passes in 8.447 seconds.

The full counter accepts the cartridge and verifies the installed stall. Its
recorded total remains 752,021 replaced characters out of 752,043, with twenty-two
structural-tail characters. The tiny original stall labels lack reliable
transcriptions, so they remain an explicit character-inventory gap rather than
invented weight. Their full model is replaced; that installation fact does not
make an uncertain transcription reliable.

The [controlled native preview](EVENT_ARTWORK_PREVIEW.md) renders both installed
placements with intact memory guards and checkpoint restoration. The visible
surfaces and lighting are inspected, but its framing clips the lowest model
edge. Native seasonal appearance, shadows, and event acceptance remain.
Continue the lucky-bag design decision and concrete playtest feedback; do not
repeat the passing controlled graphics probe for unchanged models.
The [specification](../../specs/STALL_ARTWORK.md) documents native memory layout,
source constraints, and the reflected-placement trade-off.
