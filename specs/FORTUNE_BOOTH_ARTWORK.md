# GameCube fortune-booth artwork

Port the supplied English GC New Year fortune-table design within the existing
N64 Mikuji structure allocation. This is the matching New Year table, not
Katrina's tent, and does not replace the town shrine or alter fortune outcomes.
The native booth's readable `おみくじ` label disappears with its source-matching
GC design. Decorative source shapes without a reliable textual transcription
are not assigned invented character counts.

## Native ownership

The original Mikuji slice is `21EE8..23BA8` of building object `D5E000`, 7360
bytes, SHA-256 `0c547c6a0e81556f63dba55d0eaa5805142c4ae7ea7414b8069b53c9e29a8ca3`.
Both seasons use structure type `20` and the same native range. The current
loader reads its copied prefix at `03D00000`. Keep the range tables, streamed
size, `2E00` slot, ordinary heap, and all other building reads unchanged.

Actor `9428A0`, RAM `80A82600`, is 1456 bytes, SHA-256
`f703f3c123d8a1433af942970bae72c8592ea7d53c608a9c608b26a6ff7d8b0d`;
relocation `942E50` is 144 bytes, SHA-256
`d599b128dae9e9a5046981273458dc40fb3c84ee172665be07b134ca31457ee2`.
The complete actor stays unchanged, including collision, interactions, shadow,
placement, object/palette selection, and its call to model `06022388`.

The original 32-byte model entry at object offset `22388` calls three native
child lists. Replace that entry with a call to the new complete model, an end
command, and two unreachable no-ops. Keep all preceding vertices/child lists;
they are no longer called by this actor. Only the original texture storage
beginning at `223A8` holds the new data. Preserve its unused trailing bytes.

## Exact GC model

GC `.data:53E910` contains two materials and thirty triangles. Actual REL fixups
bind palettes `53DBC0`/`53DBA0`, textures `53DDE0` (64×64 CI4) and `53DBE0`
(32×32 CI4), and vertex arrays `53E5E0` (27 vertices) and `53E790` (24 vertices).
All opaque colours are exactly representable in native RGBA5551; alpha is only
zero or 255. Convert texture storage and palette encoding without colour loss.
Retain vertex positions, texture coordinates, and normals. Set the unused native
vertex flag to zero rather than importing GC's format marker.

Decode the actual packed five-bit GC triangle commands, including their declared
counts and zero padding, and compare with the native triangle order. Independently
compile all native graphics macros. Do not execute Dolphin display lists on N64.
The first texture mirrors both axes with six-bit masks; the second clamps both
axes with five-bit masks. Each texture occupies at most 2048 TMEM bytes and each
TLUT has sixteen entries. Keep the source combiner, fog/cutout rendering, culling,
lighting, and primitive colour, with explicit pipe/load/tile synchronization.

Layout in the reused native texture area:

| Object offset | Data | Bytes |
| --- | --- | ---: |
| `223A8` | First palette | 32 |
| `223C8` | Second palette | 32 |
| `223E8` | 64×64 texture | 2048 |
| `22BE8` | 32×32 texture | 512 |
| `22DE8` | All 51 native vertices | 816 |
| `23118` | Native complete display list | 416 |

The packed replacement ends at `232B8`, before the original `23BA8` slice end.
Its visible bounds fit the native booth: GC X `−1643..5643`, Y `0..2000`,
Z `2357..9643`, versus native X `−1777..5643`, Y `0..3960`, Z `2357..9662`.
The native collision footprint and shadow remain, without new invisible reach.

## Verification and accounting

Bind source identities and actual six REL pointers; verify all converted colours,
pixels, vertices, triangles, native commands, address bounds, TMEM limits, exact
root redirection, and the unchanged actor/relocation. Install in both original
and active copied object. Preserve all other bytes/resources and reconstruct
the complete UPS. Keep current Nookington, dump, and fishing verifiers passing.

The single original `おみくじ` artwork record contributes four source characters.
Both seasons and storage copies share that ID. Source-matching model replacement
receives explicit verified GC artwork-omission credit; do not fabricate an
English text string. Ordinary scene appearance, shadow fit, and event acceptance
remain human playtest work. No new exhaustive native gameplay matrix is needed
for unchanged actor and event code.
