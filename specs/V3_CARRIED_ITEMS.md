# Shared carried-item and stationery imports

## Source and preparation

The general importer supports `--representation carried`. It reads the pinned
identity worksheet and the selected current build's installed catalogue, then
prepares every remaining addition in the paper, miscellaneous, food, plant,
and insect item groups together. Equipment, clothing, surfaces, and diaries
retain their existing importers. No item name selects a converter or installer.

The current complete prepared bundle is
`build/v3-carried-batch-prepared-05/`. It contains seven parent identities and
26 source states:

| Parent | Complete state family | Source drawing category |
| --- | --- | --- |
| Orange paper | Four quantities, `2003/2043/2083/20C3` | 44 |
| Sign board | `251E` | 19 |
| Exercise card | All thirteen stamps, `2523..252F` | 47 |
| Knife and fork | `2530` | 52 |
| Coconut | `2807` | 28 |
| Cedar sapling | `2901` | 17 |
| Spirit | All five counts, `2D28..2D2C` | 18 |

These are **source IDs**, not automatically safe N64 destinations. Prepared
records deliberately leave `native_item_id` unset and remain unavailable for
selection. Preparation does not establish runtime integration or gameplay.

All names, categories, pocket icons, and prices come from complete relocated
donor tables. The complete price function is checked, including the sign board's
500-Bell base value and paper quantities multiplying their 40-Bell base value.
These are source base prices, not a promise that the shop buys items for those
amounts. The five newly encountered names have official-disc references in the
single `translations/provenance.json` catalogue; card/cutlery names reuse their
existing entries. Every source state retains its exact name-table index/hash.

The 8,064-byte pocket packet contains fourteen complete CI4/RGBA5551 icons.
Paper selects its icon by quantity, not by style. Card stamps share their icon;
each spirit count has its own icon. The event-item importer uses this same
converter and preserves its existing icon bytes and binding records.

Seven complete handover/police material/geometry pairs occupy 5,712 bytes.
Source pointer relationships, every texture/palette/vertex, compiled commands,
and all four seasonal owners are checked. Spirits have a cage handover model
but no matching direct seasonal-ground descriptor; the importer records that
absence without inventing a dropped cage. The runtime category installer still
requires complete ground bindings. This distinction does not waive the actual
spirit release behaviour.

The orange-paper display packet is 3,088 bytes, with twelve complete resources,
eighteen background triangles, two line-layer triangles, and official text colour
`75,115,215,255`. Both donor letter owners must agree on the models. The shared
UI converter expands nested display lists through the existing checked model
graph, retains both material passes and the line-layer state, and rejects
recursive calls, missing resources, unsupported states, or incomplete geometry.
It does not rescale the source artwork or replace it with an approximation.

Category reuse verifies source/model/resource/command identity while allowing
different parent items to share the same complete model. Whole carried bundles
also reuse checked stationery commands/resources. The current bundle reuses all
seven prepared category objects and the prepared paper packet without launching
another compiler. Initial missing category/paper commands use the existing MIPS
Docker toolchain. Generated assets stay ignored.

```sh
python3 tools/v3_furniture_pipeline.py convert --representation carried \
  --assets-only \
  --base-lock build/v3-diary-category-work-01/admission-connected-04/build-lock.json \
  --reuse-assets build/v3-carried-batch-prepared-05 \
  --output build/NEW-UNUSED-CARRIED-DIRECTORY
```

## Remaining connected runtime path

Continue the shared importing task without rescanning or recompiling these
unchanged resources:

1. Resolve additive N64 destinations against the actual native readers. Donor
   `2003` overlaps native stationery, and `2901` overlaps a native flower. The
   native paper encoding must be derived from its actual quantity/style readers,
   not assumed to use the donor's 64-style stride. Existing native items stay.
2. Extend the installed shared name/type/price/display/pocket/icon readers,
   canonical saved identities, and parent-owned profile selection for the whole
   batch. Card/cutlery readers, controls, and format-15 fields already exist;
   reuse them. Source category 17 already has the diary-specific native mapping
   44, so a cedar seedling must not accidentally draw a diary.
3. Connect the actual item interactions: paper split/merge/use and letter-style
   readers; sign-board placement/design handling; card stamping/menu behaviour;
   Harvest cutlery interaction; coconut eating/planting and tree behaviour;
   cedar planting/growth; spirit split/merge/catch/release and field behaviour.
   Preserve the installed event/card/cutlery paths. Item-specific behaviour is
   part of importing, not an exception to defer automatically.
4. Bind independent parent selections in both experimental composers, preserve
   empty-selection V2-14, and verify the changed readers and save/profile bounds.
   Acquisition follows primary importing. Gold-tree work remains required after
   primary imports, along with any unfinished golden-tool behaviour.

## Verification and limits

`tests/test_v3_carried_items.py` covers complete state discovery, official names,
source prices, all pocket bindings, unchanged event-icon output, reusable
category integrity, nested stationery geometry/resources, and rejection of
recursive models, changed price code, invalid offsets, or unknown UI state.
Existing source-category and UI-state rejection checks cover the changed shared
converters. No emulator, old candidate, or hardware test is implied.

The bundle does not modify the ROM, saved format, import selections, main build
lock, or either stable V2-14 deployment. The current playable experimental
proposal remains ABI 352. Native diary/creature fixture budgets stay exhausted;
this work does not restart them or clear their recorded uncertainty.
