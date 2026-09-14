# V3 complete islander accessory assets

## Artifact

`build/v3-accessory-art-03/` contains all sixteen converted accessory objects,
40,480 bytes total. Manifest SHA-256:
`a721b129f98959916d0d7cd6c73c9d60d8e2db9f815fcd832f4dfe3b3cac808c`.
Generated native command-source SHA-256:
`4e948dcdb7c9731cb1233cf2829d0b92230099d0fd72a9e07c671820dd888f86`.
Each object's complete source/resource/output hashes, consumer joint, profile,
actual draw-function binding, and compiled display-list bounds are in the
ignored manifest. No ROM, save, extracted asset, or generated object is committed.

Construction reads the supplied English disc through the existing pinned donor
checks. The actual tool/profile table, actor profiles, callback relocations,
PPC model-address pairs, and all model resource pointers are verified before
native compilation. One compiler source contains sixteen independent sections;
the existing pinned Docker toolchain compiles them together.

## Implementation findings

All sixteen separate accessories are accounted for: flowers, bags, hats, leis,
and Ankha's cobra. The consumer table and attachment requirements are in the
[specification](../../specs/V3_VILLAGER_ACCESSORIES.md). Existing villager body
conversion continues to reject unconnected accessory dependencies.

The new explicit accessory parser mode preserves mirrored texture wrapping,
opaque/texture-edge modes, the grey flower primitive colour, and explicit tile
extents. Unknown graphics states still fail. Static furniture and speed-bag
parsing retain their own bounds and allowed states; neither implicitly accepts
accessory-only commands. Complete vertices, textures, palette alpha, and face
order are retained. No generic replacement flower/hat is substituted.

The `...-01.log` construction stops before output because the initial profile
check omits the donor's destructor relocation. The `...-02.log` check identifies
the correct destructor address but expects a one-instruction return. Inspection
of the actual symbol and code establishes the complete eight-byte zero-return
function, which the corrected build verifies. These are converter source-binding
corrections; no emulator or game save is involved. The final construction passes.

## Verification

`build/v3-accessory-art-tests-01.log`: fifteen tests pass in 12.183 seconds.

- Five accessory checks cover explicit parser modes and rejection, packed-data
  bounds, all sixteen actual villager/profile/draw bindings, full object hashes,
  and independent native-command decoding.
- Independent GX block addressing compares all 25,088 source texture pixels.
  Every palette entry and all 1,156 vertices retain their expected native data.
- Native command decoding compares all 820 triangles, every material pointer,
  vertex load, render/colour/geometry state, texture dimension, mirror/repeat
  mask, explicit tile extent, and complete display-list terminator.
- Seven existing static-furniture checks and three speed-bag parser/identity
  checks pass, preserving their existing converted assets and accepted settings.

No historical ROM is executed. No native renderer, ordinary accessory animation,
hardware appearance, or gameplay integration is claimed. This is verified asset
conversion, not a playable islander release.

## Next integration

Read-only comparison of the actual species vertex arrays identifies a separate
Yodel requirement: the donor gorilla model has 429 vertices, with 313 position
differences and 365 non-position-field differences after matrix-flag
normalisation. It cannot use Pigleg's coordinates-only adaptation or be treated
as a proven shared native model. The other newly reviewed islander species retain
all vertex fields against their native species arrays. This is a vertex review,
not complete model/rig conversion or topology proof.

Penguin, bird, horse, chicken, and tiger rows have no mouth-frame pointers, like
the wolf format. Their complete native texture objects are 4,128 bytes. Lion,
penguin, bird, horse, chicken, koala, and tiger donor body arrays are larger than
1,024 bytes; do not force these into the cat/cub body layout or discard the
extra source data. Derive their individual body-piece mappings from the actual
draw commands before claiming complete texture conversion.

Finish the other sixteen islanders' body layouts and any required coordinate
conversions, bind these exact accessory dependencies, and assign stable additive
model storage. Implement joint attachment and its draw/lifetime rules without
overrunning the native NPC buffers or leaving accessory palette/state active
for later body drawing. Then connect voices, text/defaults, houses, explicit
town-compatible behaviour, and persistence.

The current ABI-50 pilot cartridge, all original saves, both V2 patchers, and
the trailer stay unchanged. V3 source is tracked on `v3/optional-imports`;
user testing and explicit approval remain required for either patcher switch.
