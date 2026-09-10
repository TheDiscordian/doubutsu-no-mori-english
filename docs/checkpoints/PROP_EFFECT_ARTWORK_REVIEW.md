# Additional prop, shadow, and effect artwork review

Direct inspection covers 34 native textures selected from unmatched entries in
`build/artwork-matches-01.json`, plus the English GC umbrella counterpart.
Thirty-three images contain no readable wording: nests, ball surfaces, shadows,
gradient masks, architectural light patterns, reaction marks, highlights, and a
fish. One umbrella panel contains a stamped decorative motif retained by the
English GC release. Preserve these native images; this review does not apply
new English text or declare every game image reviewed.

Decoded views are local in `build/prop-effect-review-01/`, named by texture VROM.
The native input SHA-256 is
`d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
The checked V1RC3 SHA-256 is
`b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0`.
The input inventory SHA-256 is
`424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.

## Native bindings

All addresses are VROM. The existing inventory binds each listed image to its
load command and complete dimensions; its texel hashes are rechecked. Selected
CI4 palettes are bound by the material's `FD100000` load, not guessed from
neighbouring colours. A dash means an intensity image with no palette.

| Texture | Format/dimensions | Palette | Finding |
| --- | --- | --- | --- |
| `00D30A10` | CI4 32×32 | `00D309F0` | Nest |
| `00D3BA10` | CI4 32×32 | `00D3B9F0` | Nest |
| `00D46430` | CI4 32×32 | `00D46410` | Nest |
| `00D50430` | CI4 32×32 | `00D50410` | Nest |
| `00DF6410` | I4 32×32 | — | Soft-edged shadow |
| `00DF8468` | I4 32×32 | — | Building shadow |
| `00DF8940` | I4 32×32 | — | Building shadow |
| `01100338` | CI4 16×16 | `01100318` | Basketball surface |
| `011016E8` | CI4 16×16 | `011015C8` | Coloured ball panel |
| `01101668` | CI4 16×16 | `011015C8` | Coloured ball panel |
| `011015E8` | CI4 16×16 | `011015C8` | Coloured ball panel |
| `011028D8` | CI4 16×32 | `011028B8` | Soccer-ball panel |
| `011206B0` | CI4 16×32 | `01120590` | Umbrella decoration; GC comparison below |
| `01136108` | I4 128×64 | — | Oval title mask |
| `01138B70` | I8 32×32 | — | Gradient mask |
| `01139550` | I8 32×32 | — | Gradient mask |
| `0113A0B0` | I8 32×32 | — | Gradient mask |
| `0113A810` | I8 32×32 | — | Gradient mask |
| `0113B070` | I8 32×32 | — | Gradient mask |
| `0113B8D0` | I8 32×32 | — | Gradient mask |
| `013A4238` | I4 16×16 | — | Flat rectangular mask |
| `013A51F0` | I4 16×16 | — | Fading rectangular mask |
| `013A5270` | I4 32×32 | — | Geometric window/light pattern |
| `013A6248` | I4 32×32 | — | Two rectangular light panels |
| `013AB1C0` | I4 32×32 | — | Circular mask |
| `01408240` | I4 64×16 | — | Small highlight/splash marks |
| `014090E8` | I4 16×16 | — | Circular glow |
| `0140A0F8` | IA8 16×16 | — | Circular glow |
| `0141AE78` | IA8 16×16 | — | Two curved reaction lines |
| `01421AD8` | IA8 32×16 | — | Staggered vertical reaction lines |
| `01421DD0` | IA8 16×16 | — | Star highlight |
| `01424BF8` | IA8 32×32 | — | Curved shine trail |
| `014254A8` | IA8 32×32 | — | Diagonal shine trail |
| `01876740` | CI4 32×32 | `01876720` | Fish image |

All 34 complete textures, selected palettes, palette load sequences, and 56-byte
texture-load/tile sequences retain their native bytes in V1RC3. This is a
selected-range check, not a claim that all containing owners are unchanged:
`01136000` also contains the already corrected Press Start image outside these
selected ranges. That existing English image is not reopened or overwritten.

## Umbrella donor

Native `011206B0` is `tol_umb_26_kasa2_tex_txt`. Its material reuses palette
`01120590`, loaded at `011203C8`, before the texture load at `01120470`.
The intervening commands contain no replacement palette load or nested call.

The supplied English GC REL and pinned symbol map bind
`tol_umb_26_kasa2_tex_txt` at `.data:005D9800`, 512 bytes, with palette
`tol_umb_26_pal` at `005D96E0`. Actual source material `kasa_umb26_model` loads
this texture at `005DA028` as CI4 32×32. The equivalent shop model loads
`obj_shop_umb_26_kasa2_tex_txt` at `003ADBA0` through `003AE3C8`.
Both GC texel hashes are
`c12ba881a62499d433ca0920e54abc538d9d738c0d63d6079702b5b0a039d1f1`.

Direct inspection of `gc-umbrella-26.png` shows the same circular/stamped motif
and surrounding stripe design. Native and GC widths differ; do not copy the
512-byte donor into the 256-byte native slot. Retaining this motif follows the
English source's artwork intent. No invented transcription or translation
credit is assigned.

## Decoder and limits

The inspection decoder supports native and GC I8 in addition to its existing
CI4/I4/IA8 formats. I8 uses all eight intensity bits with no IA nibble exchange.
Three focused tests check all 256 native levels, independent two-tile GC order,
existing intensity formats, and invalid sizes/formats/palette arguments.
This is inspection tooling only; no ROM, texture, gameplay code, save, or patch
changes result from this batch. V1RC3 remains the current packaged candidate.

Dynamic-palette candidates remain outside this completed review. The player
images `00D28180`, `00D28380`, and `00D2BEE0` select palette segment 12. Effect
image `01411760` points to palette RAM `80120F70`, which is in BSS rather than
file-backed main code. Do not read an unrelated cartridge address as that
palette or invent colours. These bindings need separate resolution before
claiming their visible artwork reviewed. Existing completed neutral/decorative
reviews and the tiny unresolved igloo label are not repeated here.
