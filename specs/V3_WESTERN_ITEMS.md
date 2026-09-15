# Western furniture imports

## Scope and source identity

Seven GAFE01-r0 furnishings have complete native graphics conversion and
source-verified metadata. Runtime installation remains work. Neither served
patcher changes; the import-free cartridge remains V2-11.

`tools/v3_furniture_art.py --batch western` verifies both furniture-quality
tables, exact profiles, names, model bindings, and every graphics relocation
against the pinned donor REL and symbols. `tools/v3_western_items.py` binds
prices, catalogue modes/positions, full scoring properties, and unique membership
across all 23 donor acquisition lists. The pinned identity worksheet corroborates
that the seven lack native AF IDs, names, models, and textures; the actual donor
tables, not worksheet names alone, establish profile identity.

| ID | Index | Name | Price | Acquisition | Object bytes |
| --- | ---: | --- | ---: | --- | ---: |
| `32B0` | 1196 | tumbleweed | 520 | ordinary C | 3,296 |
| `32B4` | 1197 | cow skull | 1,020 | ordinary A | 3,632 |
| `32BC` | 1199 | saddle fence | 2,180 | event reward | 5,216 |
| `32C0` | 1200 | western fence | 880 | ordinary A | 1,920 |
| `3328` | 1226 | desert cactus | 890 | ordinary B | 2,320 |
| `3330` | 1228 | wagon wheel | 1,230 | ordinary B | 2,720 |
| `3334` | 1229 | well | 2,700 | event reward | 5,088 |

These are proposed additive runtime identities until installed in the fixed
registry. Selection order must never assign IDs or repurpose an existing item.
The well is decorative furniture, not a replacement for the town's shrine.

## Complete graphics and exact model slots

The seven objects retain all 463 vertices, 295 triangles, 23,808 CI4 texels, and
112 palette entries. Total converted size is 24,192 bytes. Each profile uses
scale 0.01, shape 4, collision type 0, lighting flag 0, and no callbacks,
skeleton, texture animation, or interaction. Heights are 18, except desert
cactus and wagon wheel, whose height is 42.43.

Saddle fence has **two opaque lists** at donor profile offsets 0 and 4.
The second is not a translucent list despite its `_model_a_model` suffix.
Preserve the actual four-slot model layout when producing the native 68-byte
profile: opaque0 at 16, opaque1 at 20, translucent0 at 24, and translucent1 at 28.
Both saddle-fence parts remain opaque, in their original order, sharing the
complete palette, textures, and vertex array.

Converter revision 4 adds an explicit Western material mode. It accepts only
the reviewed clamp, S-mirror, and double-mirror descriptors. The well's
`D2F0FA00` mirrors S and T; its three 16×16 textures extend over 32×32 tiles.
Native masks remain 4 on both axes, with mirror/wrap flags on both. Preserve
the explicit following `F2` extent instead of widening the source image or
discarding the material update. Unsupported descriptors, non-power-of-two
repeated axes, extra relocations, and model-slot mismatches remain errors.

Tumbleweed uses `int_iku_tumble_tex_txt`, and cow skull's large texture uses
`int_iku_cow1_tex_txt`. Resolve those explicit symbol exceptions without guessing
different resources from a naming convention. Existing converter batches retain
their default symbol naming and material restrictions.

## Scoring and acquisition

All seven belong to donor Western theme 55, type 2, with donor surface index 18.
Install its definition and complete English score-letter name. A donor surface
index is not automatically a verified native wall/floor mapping.

| Name | Donor HRA | Native layout | Feng shui |
| --- | --- | --- | --- |
| tumbleweed | `DC050200` | `DC050400` | `0000` |
| cow skull | `DC050080` | `DC050100` | `0000` |
| saddle fence | `DC050300` | `DC050600` | `0000` |
| western fence | `DC050000` | `DC050000` | `0000` |
| desert cactus | `DC050100` | `DC050200` | `0400` |
| wagon wheel | `DC050100` | `DC050200` | `0000` |
| well | `DC050300` | `DC050600` | `0000` |

Cow skull retains surface type 2. Desert cactus retains green colour 4. The
saddle fence and well belong only to `ftr_listEvent`, birth category 3; do not
put either into an ordinary A/B/C stock list. Their native event-acquisition
and catalogue-order routes require actual consumer review and installation.
Selected-only theme counting must exclude unselected imports.

## Capacity and remaining installation

Saddle fence exceeds the current 5,120-byte bank by 96 bytes; it must not be
installed with that limit. Well fits the bank with 32 bytes spare but also needs
a ROM span larger than the preceding batches' 4-KiB slots. Preserve complete
models, allocate non-overlapping storage, and resolve native capacity first.

The native My_Room allocator at `80938D44` uses bank-count multiplication at
`80938DA8..80938DB0`, contiguous-bank stride at `80938E78`, and separate heap
allocation size at `80938EA8`. The shared DMA adapter independently checks
`BANK_BYTES`. Altering only the adapter would permit an out-of-bounds transfer;
altering only the allocator would leave the import rejected. Review every
allocation/stride consumer, catalogue preview, and worst-case live memory before
changing capacity. No capacity increase is implemented by source conversion.

Install fixed profiles, item records/readers, true stock routes, catalogue and
scoring tables, English theme naming, and selected saved dependencies. Add the
individual offline composer options after installation. Run one bounded combined
check for the changed capacity, second opaque part, and native reward route;
reuse existing evidence for unchanged systems. Ordinary placement, acquisition,
persistence, and hardware appearance remain required playtest work.

The [checkpoint](../docs/checkpoints/V3_WESTERN_ITEMS.md) records generated hashes
and executed checks. No ROM or generated game asset is committed or published.
