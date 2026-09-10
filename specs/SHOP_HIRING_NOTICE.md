# Nook 'n' Go hiring-notice artwork

The normal native shop room `013B6000` contains a Japanese hiring notice at
`013B8EF8`, 48×32 CI4, palette `013B8878`. Its complete 17,696-byte owner has
SHA-256 `35f448bc7cf009995ea91ea6b760c2ed9e8de580a6ff68c7543cce0614342a1f`.
The source-bound native material at `013B7ED0` loads that texture. Four vertices
at `013B7A80` form a separate overlay in front of the wall: X 5910..6890,
Y 1220..1940, Z 840. Its sole triangle command at `013B7F10` draws
`(0,1,2)` and `(0,2,3)` after the four-vertex load. It is not the wall itself.

The supplied English GC `ac_shop_indoor.c` binds the corresponding room to
`rom_shop2w_model` and `rom_shop2w_modelT`. Its complete vertices are at
`.data:0094DBA0` (0x1340 bytes), and models at `0094EEE0` (0x68) and
`0094EF48` (0x458). The English room omits this notice rather than supplying
an English version of it. Do not invent a translation asset from another shop's
poster or import unrelated room geometry.

The bound English background uses palette `0094C2A0`, texture `0094D3A0`, and
25 wall vertices at `0094DE20`; actual pointer fixups are `0094F15C`,
`0094F164`, and `0094F174`. Its complete 16×128 CI4 texture matches the
native `013B9C78` after GC tiling conversion, with equivalent used palette
colours. The native 25 vertices at `013B69C0` retain the corresponding UVs and
lighting at the native-to-GC position ratio 5:4. The 28 packed English wall
triangles start at `0094F178`. Background faces at Z 640 cover all four scaled
notice corners. Other GC trim at Z 672 lies entirely left of the notice's
X range 4728..5512; it is not a replacement notice in that position.

`tools/shop_notice_fix.py` changes only the eight-byte native notice triangle
command to the SDK's `gsSPNoOp()` encoding, `E0000000 00000000`. Reuse the
existing `overlays/fishing/artwork.c` no-op section, independently compiled in
the pinned Docker toolchain. The notice's now-unused texture, palette, and
vertices remain in storage; they no longer draw. All wall surfaces, other
triangles, texture state, CPU code, DMA identities, allocations, gameplay, and
saves stay unchanged.

Require the supported original ROM, exact V1RC1 predecessor, complete supplied
REL/symbol map, native material/owner checks, donor model/vertex checks, and
background coverage proof before installing the omission. Reconstruct a new
32-MiB cartridge and prove UPS application and complete unrelated-resource
retention. Preserve the existing V1RC1 handoff and earlier artifacts. Ordinary
room appearance remains playtest work; this data-only correction makes no
claim of new native gameplay or hardware validation. Percentage-tool integration
is deferred and is not part of this artwork correction.
