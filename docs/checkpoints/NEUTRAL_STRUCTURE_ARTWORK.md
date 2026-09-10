# Remaining structure artwork inspection

## Scope and result

Direct decoding and inspection cover seventeen distinct native structure textures
in twenty-three views, including both train palette selections, both vacant-lot
signs, both Katrina-tent variants and window-light masks, and Gracie's car.
No readable Japanese wording is identified in these images. The train's marking
is Latin/numeric; the small papers on the vacant-lot signs contain abstract marks
without reliably transcribable wording. Tent ornaments are decorative patterns,
and the car textures contain bodywork and upholstery. Preserve these native
images. This review adds no English text or character credit.

The separate 208×16 I4 region-warning image at `A21000` is already English:
"This game is not designed for use on this system". Its complete 1664-byte
source SHA-256 is
`1d972c31291fe7d1c207fc186613c82a7a87d5a49015c2baf8090ef6ce392e9c`.
It remains unchanged in the current combined candidate.

This is a scoped direct-image inspection, not full-game artwork completion,
ordinary scene acceptance, a furniture/clothing review, or a claim to have
transcribed tiny unreadable marks. Do not rerun the same image batch unchanged.
The accepted Japanese lucky-bag decoration is outside this batch and remains
the user's resolved choice.

## Native bindings

The pinned native `ac_structure.h` identifies structure types `10`/`11` as the
two train sections, `15` as reserve signs, `18` as the fortune-teller structure,
and `19` as the designer's car. The pinned GC `ac_buggy.c` identifies the buggy
actor as the fortune tent; it is not the separate New Year fortune table.

Native model-table owner `DF4000` supplies seasonal start arrays at `8`/`178`
and end arrays at `C0`/`230`. The loader reads each model at its table offset
plus eight, rounding its size to sixteen bytes. Palette-table owner `D5D000`
supplies seasonal arrays at `8`/`174`, with palette indices `39`, `3A`, `3E`,
`41`, and `42`. The actual palette pointers are resolved from those arrays,
not inferred from an index-times-stride formula. The complete 736-byte palette
table has SHA-256
`76ff36c9a7ccd0ad3def96bf3125e1db4fe8e5cdbf1cea2a9f98c96ac505c052`.

Texture addresses and dimensions below come from the native texture-load and
tile-size commands within those bounded model sections. The two 16×16 I4 masks
also match the format in the pinned GC `obj_s_uranai.c` source. Source ROM
identity is checked by `texture_preview.py` before decoding.

| Structure | Texture VROMs and dimensions | Actual palette VROMs |
| --- | --- | --- |
| Train section `10` | `DDF6D0` 128×32; `DDFED0`, `DE06D0` 64×64 | `D5BE88`, `D5BEA8` |
| Train section `11` | `DE1FA8`, `DE27A8` 128×32; `DE2FA8` 256×16 | `D5BEC8`, `D5BEE8` |
| Vacant-lot sign, summer | `DB3808` 32×64 | `D5BF48` |
| Vacant-lot sign, winter | `DB3D78` 32×64 | `D5BF68` |
| Katrina tent, summer | `D61C60` 128×32; `D624E0` 64×64 | `D5BF88` |
| Katrina tent, winter | `D63658` 128×32; `D63ED8` 64×64 | `D5BFA8` |
| Katrina window masks | `D62460`, `D63E58` 16×16 I4 | None |
| Gracie's car, both seasons | `DB4BE0`, `DB53E0`, `DB5BE0` 128×32 | `D5BFC8` |

All entries except the window masks use CI4. Local inspection PNGs are under
`build/artwork-inspection/remainder-*.png`; the warning is
`build/artwork-inspection/region-warning-native.png`. These files are ignored.
The existing decoder reproduces a view with its recorded address, dimensions,
format, and palette, for example:

```sh
python3 tools/texture_preview.py --address DB3808 --palette D5BF48 --width 32 --height 64 --format ci4 --scale 4 --output build/reserve-inspection.png
```

Use a fresh output file; inspection does not edit the ROM or textures.

## Current-candidate retention

The inspected candidate is
`build/title-stall-combined-01/animal-forest-title-preview.z64`, SHA-256
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`.
All ten seasonal table entries retain their native starts/ends. Each complete
loaded section below matches both its retained `D5E000` copy and its actual
streamed `03D00000` copy in that candidate. Duplicate seasonal selections do
not create additional unique images or translation credit.

| Section | Native VROM | Bytes | SHA-256 |
| --- | --- | --- | --- |
| Train `10`, both seasons | `DDEA98` | 10784 | `6ecc37b7155c522fbde68086089d19e818bd85c83398845fcdb037c919b00e27` |
| Train `11`, both seasons | `DE14C8` | 9584 | `2b003f329e948f9cdeecabe53ab117ee1e2ba4731b81bbcfe8f6be22921899fc` |
| Reserve, summer | `DB36A8` | 1376 | `acc37b86c998e1c26caa55c6e5e0b60b4e4b767aa3b17c0833dfcf4379c5729c` |
| Reserve, winter | `DB3C18` | 1376 | `3cad7b4da52cb2af3ee5bad18de4986aabb867513954828f49878fd4d2a42d1c` |
| Katrina, summer | `D61448` | 6640 | `42fb6b197a36930802bca51ce84a777f699f48aea2709cd4495075314bb5b189` |
| Katrina, winter | `D62E40` | 6640 | `fa7c9040fce24fee019c76188f20bd19024403b498fb69bad6c793cfc158d9aa` |
| Gracie's car, both seasons | `DB4188` | 8800 | `a62225f0e4aef23c91a75654838c5cc86945e0bce2b523519b6a28d127cb6480` |

The nine specifically selected palettes and the palette-pointer table are
unchanged. This is not a claim that the entire shared palette object is native:
an unrelated existing translation changes the eight-byte span at `D5BA60`.
No renderer, allocation, event, collision, shadow, save, or output-ROM change
is made by this inspection. No emulator scenario or compiler build runs.
