# Home-mailbox artwork review

The home mailbox's sixteen summer/winter textures match the supplied English
GameCube artwork in every visible pixel and alpha value. Preserve the native
object, palettes, geometry, animation tables, and actor. This closes a scoped
artwork review; it applies no new English text and changes no ROM or save.

Direct inspection finds mailbox surfaces, a stylised number-like side marking,
a blue flag support, and envelope images for the flag animation. The side mark
is also present in the English GC donor; it is not an omitted English replacement.
No exact transcription or Japanese-character weight is invented for that mark.
This home mailbox is distinct from the post-office building and the previously
translated postal bag. The lucky-bag retention decision is unchanged.

## Bound source images

Original ROM SHA-256:
`d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
GC REL SHA-256:
`29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837`.
GC symbol-map SHA-256:
`e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87`.
The twelve static candidates come from `build/artwork-matches-01.json`, SHA-256
`424fb279c90e7ac27a30ecbdf6c578b58cdfaeb3cd8549148a2d866816ad276f`.
Four additional flag-animation images use separately checked actor/table bindings.

All native addresses below are VROM; GC addresses are REL `.data` offsets.
All images are CI4. Native owner `01103000` is object ID `1A` (`OBJECT_26`),
9,456 bytes, SHA-256
`e4a5890abc83ce1c2844c73b3153508cc426a02125218623713a7db5d15d387f`.

| Role | Size | Native summer / winter | GC summer / winter |
| --- | --- | --- | --- |
| Side | 32×32 | `01104088` / `01105198` | `29C2A0` / `29D140` |
| Leg | 16×16 | `01104288` / `01105398` | `29C4A0` / `29D340` |
| Interior | 16×16 | `01104308` / `01105418` | `29C520` / `29D3C0` |
| Front | 16×32 | `01103E88` / `01104F98` | `29C0A0` / `29CF40` |
| Open front | 16×32 | `01103F88` / `01105098` | `29C1A0` / `29D040` |
| Flag support | 16×32 | `01103B88` / `01104C98` | `29BDA0` / `29CC40` |
| Flag image 2 | 16×32 | `01103C88` / `01104D98` | `29BEA0` / `29CD40` |
| Flag image 3 | 16×32 | `01103D88` / `01104E98` | `29BFA0` / `29CE40` |

Native summer/winter palettes are `01103B68` and `01104C78`; GC palettes are
`29BD80` and `29CC20`. The other fifteen entries match exactly. Entry zero is
fully transparent in both formats, with decoded RGB `632929` versus `662222`.
A raw RGBA comparison therefore differs for textures using entry zero, while
the visible-pixel comparison passes. No palette correction is appropriate.

The native static material's palette load is forty-eight bytes before each
texture command and points to the corresponding palette above. Actual GC
same-module data relocations bind the textures and palettes in these models:
summer main/front/flag-support at `29C8F0`, `29C9B8`, `29CA50`, and winter at
`29D790`, `29D858`, `29D8F0`. Their texture command dimensions agree with the
complete native image ranges. This verifies colours as well as matching indices.

## Animated flag binding

The native MailBox actor at VROM `00861420`, linked RAM `8096C7E0`, is 3,712
bytes with SHA-256
`8997f31ed042593a101cb61ef027a85dd9e514bb55001bd45c6248870b04276a`.
Its 320-byte relocation file at `008622A0` has SHA-256
`3d427d7ff94fb66c1c80070d77b36d630c5adbd296e20e0e0666c947ded299dc`.

The static flag texture table at `8096D650` selects segment-six offsets `0C88`
and `1D98`. The animation table at `8096D658` selects `0318` and `14E8`.
Those descriptors point to `0308`/`14D8`, whose two-image tables are at
`02E0`/`14B0`, selecting offsets `0C88,0D88` / `1D98,1E98`. The actor's
season comparison and draw path use these tables; the material commands at
`8096D5B0` and `8096D608` load the two dynamic segments as 16×32 CI4.
The corresponding GC texture-table relocations at `29BC70` and `29CBD0` bind
the four donor images listed above. No animation timing or delivery rule changes.

## Inspection, retention, and limits

Fourteen decoded views are inspected under `build/home-mailbox-review-01/`:
twelve native views covering every distinct role and both seasonal fronts,
sides, and flag frames, plus two direct summer GC comparisons. The other four
static winter views are verified against their complete named GC images, not
claimed as separately viewed. The existing decoder preserves source pixels;
no artwork is generated or redrawn. A selected view is reproducible with:

```sh
python3 tools/texture_preview.py --address 01104088 --palette 01103B68 --width 32 --height 32 --format ci4 --scale 8 --output build/home-mailbox-review-new/side-s.png
```

The actor disassembly is retained in `build/home-mailbox-review-01/actor/` and
uses the existing pinned Docker toolchain. The complete mailbox object, actor,
and relocation file remain identical to the native source in RC4, SHA-256
`5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067`.
All sixteen native/donor visible-pixel comparisons pass with the verified
palettes. Earlier ROMs, saved data, packages, and source assets are untouched.

This is asset/source review, not fresh mailbox animation, gameplay, or hardware
acceptance. It does not close other dynamic materials or remaining artwork.
Do not repeat this mailbox inspection or count retained English-donor markings
as newly applied translation.
