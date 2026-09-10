# Native house artwork review

Direct inspection covers 22 previously unmatched native house textures, ten
matching English GC door plaques, and the native crate copyright image.
Twelve house surface atlases contain walls, roofs, doors, windows, grain,
fittings, and geometric decoration without readable Japanese wording. The ten
small oval door plaques retain the same central decorative marks in the
English GC release. Preserve these native images; no English replacement or
translation credit is assigned by this review.

The local decoding receipt is `build/house-artwork-review-01/inspection.json`,
SHA-256 `e1cfc89f5d007494bc44d0a8b4a71f66745a8e6202f22a798d41bc7c5c75d49b`.
Its initial status precedes direct inspection; this checkpoint records the
completed inspection. Native images, selected palettes, their hashes, material
load addresses, and both cartridge copies are bound in that receipt. All views
use the existing texture decoder, with no redraw, resampling, or invented
transcription. PNGs remain local in the same directory.

## Selected native textures

Addresses are VROM. All selected house textures are CI4. Surface atlases are
128×32. Plaques are 32×32, except house 1's 32×24 texture.

| Season/type | Surface textures | Plaque | Selected palette |
| --- | --- | --- | --- |
| Summer 1 | — | `00D84058` | `00D5B008` |
| Summer 2 | `00D84EE8`, `00D85F68` | `00D86768` | `00D5B128` |
| Summer 3 | `00D875D8` | `00D88E58` | `00D5B1C8` |
| Summer 4 | `00D89C08` | `00D8B488` | `00D5B268` |
| Summer 5 | `00D8C510`, `00D8CD90` | `00D8DD90` | `00D5B308` |
| Winter 1 | — | `00D905E0` | `00D5B328` |
| Winter 2 | `00D91470`, `00D924F0` | `00D92CF0` | `00D5B448` |
| Winter 3 | `00D93B60` | `00D953E0` | `00D5B4E8` |
| Winter 4 | `00D961D0` | `00D97A50` | `00D5B588` |
| Winter 5 | `00D98AD8`, `00D99B58` | `00D9A358` | `00D5B628` |

The pinned native asset symbols bind these to `obj_[sw]_house1_t4_tex_txt`,
`obj_[sw]_house[2-5]_name_tex_txt`, and the corresponding `t1`/`t3` atlases.
Palettes come from the native asset YAML's `_a_pal` entries. This selected-set
review does not claim inspection of every palette variant or game image.

## English GC plaque comparison

All GC plaques are 32×32 CI4. Addresses below are relative to the supplied
verified REL's `.data` section. Actual load commands bind each texture; models
are in `local/ac-decomp/src/data/model/obj_s_house1.c` at the pinned revision.

| Season/type | Texture | Palette | Load command |
| --- | --- | --- | --- |
| Summer 1 | `546F00` | `500720` | `547930` |
| Summer 2 | `549560` | `500840` | `54A070` |
| Summer 3 | `54BB40` | `5008E0` | `54C600` |
| Summer 4 | `54E0C0` | `500980` | `54EAD0` |
| Summer 5 | `5505A0` | `500A20` | `551268` |
| Winter 1 | `552D20` | `500A40` | `553750` |
| Winter 2 | `555380` | `500B60` | `555E98` |
| Winter 3 | `557980` | `500C00` | `558440` |
| Winter 4 | `559F00` | `500CA0` | `55A938` |
| Winter 5 | `55C400` | `500D40` | `55D0C8` |

The central plaque patterns agree visually, not as complete texture equality:
shading differs, and house 1's native slot is smaller. Do not copy a 512-byte GC
plaque into the 384-byte native slot or replace the marks with invented wording.

## Retention in V1RC2

The checked cartridge has SHA-256
`7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb`.
All 22 selected textures and palettes retain their native bytes. Both building
owners `00D5E000` and `03D00000` preserve the ten complete native house slices,
including their geometry and drawing commands:

| Season/type | Slice VROM | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Summer 1 | `00D81BB8` | 10192 | `9ae81988b10bbc8ea686ab612f62710676e98d13fc63975b67a7d6132167e0d4` |
| Summer 2 | `00D84390` | 10112 | `3ba8d2b3c0c3077faf3e92608c1f29c45280c99aa473bfbe054db05052d4872f` |
| Summer 3 | `00D86B20` | 9952 | `817a7b5ba7905ff5be7c3f4f53c4ec71b34996e98805fc99680ec8b7a3f31b20` |
| Summer 4 | `00D89210` | 9760 | `b3d35ccbc32e1904eee03421347cba597cea10151b83979b869d1b0c0318524d` |
| Summer 5 | `00D8B840` | 10496 | `2be85b915fab91c33ffb085f4783e7eba4f010460bb975830fc73f0891d9a3dd` |
| Winter 1 | `00D8E148` | 10176 | `351ec973c673a2f574746e378d7be9325eb811e70be1f069899ebb23db60ba25` |
| Winter 2 | `00D90918` | 10112 | `47909fd00c186984e2fdcf66df0556816d7c3011866f112eba85e68c257b58fc` |
| Winter 3 | `00D930A8` | 9952 | `2dc4eafbdbf9ea941fb09d478eb45399e6169a3475d0c0e653b701ed74b69536` |
| Winter 4 | `00D95798` | 9824 | `aee7cb963b9f1fc12f12952997fd1bee32344f77feb38803b26f743d301af826` |
| Winter 5 | `00D97E08` | 10496 | `163be2c6bac89d7df7a5daa9270f8658476c33a1fbf7110196743cfbcf219f58` |

The unchanged table `00DF4000` supplies both seasonal ranges for types 0–4.
The current structure loader at RAM `809E8198` contains
`3C0E03D0 25CE0000`, selecting the retained streamed owner.

The separate 256×16 I4 crate texture at `00D7F660` visibly reads
`©2001 Nintendo`. Preserve the original copyright notice. Its 2048 bytes have
SHA-256 `c82b0caca0f47eb8010d287919224ab050c34f2ebbf204c5b2ed4acabeacbd9a`;
the load at `00D7FE90` is `FD900000 06021660`. The texture and 128-byte model
prefix at `00D7FE60` are unchanged in both building copies.

No ROM, package, loader, geometry, or save changes result from this review.
Ordinary scene appearance remains human acceptance work. The separate tiny
igloo-interior image `0138DA28` remains unresolved; its flat-object geometry
alone is not a reliable Japanese transcription or a completed review.
