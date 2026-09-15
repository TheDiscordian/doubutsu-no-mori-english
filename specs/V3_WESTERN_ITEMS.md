# Western furniture imports

## Scope and source identity

Seven GAFE01-r0 furnishings have complete native graphics conversion,
source-verified metadata, and experimental runtime installation. The
[full-sized additions](V3_WESTERN_LARGE_ITEMS.md) complete the ten-item theme.
Neither
served patcher changes; the import-free cartridge remains V2-11.

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

These additive runtime identities are installed in the fixed registry.
Selection order must never assign IDs or repurpose an existing item.
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
put either into an ordinary A/B/C stock list. Both use native event list 3,
whose 64 original entries all carry birth category 3. Its first terminator is
at `2E4`, followed by two padding bytes; append before that first terminator.
Catalogue availability admits the selected rewards in list 3, not ordinary
stock. The native event selector and pocket-ownership path pass for the well.
Selected-only theme counting excludes unselected imports. Ordinary event
conversations and deliveries remain unverified.

## Dedicated model banks

The [bank owner](V3_FURNITURE_BANKS.md) reserves 100 complete 9,216-byte banks
in unused Expansion Pak RAM. The 5,216-byte saddle fence fits without truncation
or overflowing the native 5,120-byte allocation. The shared DMA limit and actual
constructor bank table use the same enlarged capacity. Native cleanup never
passes these fixed banks to the ordinary heap allocator. Catalogue preview
already owns independent `0x2400`-byte buffers and needs no increase.

Each Western model has a fixed 8-KiB VROM slot, beginning at `0238C000` and
ending with the well's slot at `02398000`. Complete converted models remain
within their own slots. The current shared 25 static 80-byte rows begin at RAM
`80482000`; the 26 shared 32-byte item records begin at `80482800`, ending at
`80482B40`. The expanded package end guard is at `80483FF0`.

The actual furniture catalogue has 462 rows, with all 248 clothing rows retained.
Its conservative complete allocation is 280,128 bytes within the existing
280,704-byte menu pool. Catalogue code occupies 3,280 of its 3,664 reserved bytes;
further additions require another capacity review. HRA installs all seven theme
55 records, the English `western` name, and the donor properties. The score-letter
table contains 58 logical 26-byte rows followed by 12 padding bytes. Appending
a name must replace prior end padding, not insert padding between records.

All seven identities are optional in the offline composer. Shared saved format 2
is unchanged, but selected dependencies change. An older/smaller profile rejects
these saves; ordinary cross-profile gameplay reload is not established.

The [source checkpoint](../docs/checkpoints/V3_WESTERN_ITEMS.md) and
[runtime checkpoint](../docs/checkpoints/V3_WESTERN_RUNTIME.md) record generated
hashes, executed checks, and incomplete native model/cleanup verification.
Ordinary placement, acquisition, persistence, and hardware appearance remain
required playtest work. No ROM or generated game asset is committed or published.
