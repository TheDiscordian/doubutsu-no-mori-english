# Matching room and prop detail review

Direct inspection covers 35 previously unreviewed CI4 images selected for
possible small labels: a handheld phone, police furniture/books, postal scales
and envelopes, Redd's display objects, shop sign edges/registers, and shelf books.
Their visible pixels already match the supplied English GC release. Preserve
these native images; copying the donor would not add English wording.

No readable Japanese wording is identified in this selected set. Redd's box
has a small circular decorative seal, also present in English GC; no reliable
transcription is assigned. The tiny police-book label is likewise not treated
as a transcribed word. Other surfaces contain numeric/indicator-like marks,
plain frames, buttons, furniture, and object illustrations. This is scoped
asset review, not complete game-artwork coverage or ordinary scene acceptance.

## Source and installed checks

The read-only decoding receipt is
`build/matched-details-review-01/inspection.json`, SHA-256
`cacf0f48eb6c933b8a3e0557494884dd362130b7139522fd91ec14da66c7c093`.
The local extraction script `review.py` in that directory has SHA-256
`5c7e2bce0072ffa9fc1b2b5d5ec5308a68100e39e8879a9b5d03c99b6d54e0a3`.
The receipt records decoding/source checks; the completed visual findings are
recorded here. The 35 local PNGs are named by native texture address.

The original cartridge is verified before decoding. The existing inventory has
SHA-256 `424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.
Every selected original owner, complete texel range, and short material sequence
is rechecked against that bound inventory. The actual native palette load is
`FD100000` at texture-command minus `30`, followed by the sixteen-entry TLUT
load. No palette is inferred from colour or nearby storage.

English GC texture and palette addresses come from actual same-module `.data`
relocations inside the named source model. The last bound palette load before
the texture has no intervening display-list call or return. The full REL and
symbol-map hashes are checked. Comparison uses decoded visible RGBA values,
not only CI indices; fully transparent RGB is immaterial. All 35 comparisons pass.

The checked V1RC4 cartridge has SHA-256
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
All selected textures and 104-byte palette/texture/tile sequences remain native.
All selected visible pixels remain native too. One shared palette differs:
`013CF698` includes the existing welcome-sign correction. The selected sign-edge
image `013D1C58` uses none of that changed colour, and its full decoded RGBA
still matches the native image and the donor. This agrees with the existing
shop-interior installer's separate edge-retention check; do not undo that palette fix.

## Selected images

Native addresses are VROM; GC addresses are relative to the supplied REL's
`.data` section. Every row is CI4. Repeated palettes do not imply that every
user of that palette is reviewed.

| Native texture | Dimensions | Native palette | GC texture | GC palette |
| --- | --- | --- | --- | --- |
| `01127808` | 16×32 | `011275E8` | `005C61E0` | `005C5FC0` |
| `01127908` | 16×32 | `011275E8` | `005C62E0` | `005C5FC0` |
| `01127608` | 16×32 | `011275E8` | `005C5FE0` | `005C5FC0` |
| `01127708` | 16×32 | `011275E8` | `005C60E0` | `005C5FC0` |
| `012B1168` | 16×16 | `012AEA28` | `0093C1E0` | `00939AA0` |
| `012AEAE8` | 32×32 | `012AEA28` | `00939B60` | `00939AA0` |
| `012B04E8` | 32×32 | `012AEA88` | `0093B560` | `00939B00` |
| `012B07E8` | 32×16 | `012AEA88` | `0093B860` | `00939B00` |
| `012B18E8` | 32×64 | `012AEAC8` | `0093C960` | `00939B40` |
| `012AF068` | 32×16 | `012AEA48` | `0093A0E0` | `00939AC0` |
| `012B1368` | 32×64 | `012AEAA8` | `0093C3E0` | `00939B20` |
| `012C0658` | 32×16 | `012BDA98` | `00612760` | `00610700` |
| `012C05D8` | 16×16 | `012BDA98` | `006126E0` | `00610700` |
| `012C0A58` | 16×32 | `012BDAF8` | `00612B60` | `00610740` |
| `012BF958` | 16×32 | `012BDA98` | `006125E0` | `00610700` |
| `012C4970` | 16×16 | `012C3BD0` | `0060DB20` | `0060CD80` |
| `012C4870` | 16×32 | `012C3BD0` | `0060DA20` | `0060CD80` |
| `012C58F0` | 32×48 | `012C3CB0` | `0060EAA0` | `0060CE60` |
| `012C5BF0` | 32×48 | `012C3CD0` | `0060EDA0` | `0060CE80` |
| `012C53F0` | 16×32 | `012C3C70` | `0060E5A0` | `0060CE20` |
| `012C52F0` | 16×32 | `012C3C70` | `0060E4A0` | `0060CE20` |
| `012C4FF0` | 32×48 | `012C3C50` | `0060E1A0` | `0060CE00` |
| `012C49F0` | 32×32 | `012C3BF0` | `0060DBA0` | `0060CDA0` |
| `012C4BF0` | 32×32 | `012C3C10` | `0060DDA0` | `0060CDC0` |
| `012C4DF0` | 64×16 | `012C3C30` | `0060DFA0` | `0060CDE0` |
| `013D1C58` | 16×32 | `013CF698` | `009551A0` | `00952BE0` |
| `013D0E58` | 16×16 | `013CF638` | `009543A0` | `00952B40` |
| `013D2158` | 16×32 | `013CF6B8` | `009556A0` | `00952C00` |
| `013D2058` | 32×16 | `013CF6B8` | `009555A0` | `00952C00` |
| `013D1D58` | 32×48 | `013CF6B8` | `009552A0` | `00952C00` |
| `013D0ED8` | 32×32 | `013CF658` | `00954420` | `00952B60` |
| `013C31B8` | 16×16 | `013C2B98` | `00965300` | `00964CE0` |
| `013C3138` | 16×16 | `013C2B98` | `00965280` | `00964CE0` |
| `013C30B8` | 16×16 | `013C2B98` | `00965200` | `00964CE0` |
| `0151EB18` | 32×16 | `0151E578` | `009ABF60` | `009AB9C0` |

No cartridge, patch, source asset, or save is modified. No compiler build,
emulator run, percentage calculation, or repeated review of the completed
Japanese-sign replacement batches is needed for these findings.
