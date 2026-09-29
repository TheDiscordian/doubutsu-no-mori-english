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
absence without inventing a dropped cage. The ordinary category converter still
requires complete ground bindings. The carried runtime's explicit native-category
bitmap excludes the spirit handover-only category. This does not waive actual
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

## Installed shared runtime

The current development proposal is ABI 353 at
`build/v3-carried-runtime-work-01/readers-connected-12/build-lock.json`.
Its ROM SHA-256 is
`a76fc718d82567fd313fc4d9a4ea916ae210b0fdaefeae2faedbdcd72aa36aa9`.
This is an inactive carried integration, not a new playable-import claim.

`v3_furniture_install.py --refresh-runtime --carried-items PATH` installs the
complete checked bundle through the existing guarded runtime builder. It
preserves original native type tables and uses these fixed destinations:

| Source family | Native destination | Native drawing category |
| --- | --- | --- |
| Orange paper quantities | `2040..2043` | 49 |
| Sign board | `251E` | 46 |
| Exercise-card stamps | `2523..252F` | 45 |
| Knife and fork | `2530` | 47 |
| Coconut | `2807` | 50 |
| Cedar sapling | `290A` | 48 |
| Spirit counts | `2D28..2D2C` | 51, handover only |

The native paper type table has 64 entries, and its letter constructor stores
the original item's low byte directly as the paper style. Native `2003` is
therefore retained, not overwritten or reinterpreted as a donor quantity.
The checked ten-entry native plant table also remains unchanged. Registry
destinations do not depend on selection order.

Code occupies `80771000..80771940`; the 864-byte table starts at `80773800`.
The eight-word header identifies 26 records of 32 bytes and separate seven-bit
readiness/selection masks, both zero. Names, categories, base prices, room/pocket
conversions, icons, and quantity helpers use the same bounded record lookup.
Unrelated identities delegate to the existing readers. Disabled reserved IDs
never index the short native tables. Card/cutlery admission also requires the
existing event reader's matching selection, preserving its controls.

Fourteen icons occupy `80774000..80775F80`; four newly needed handover models
start at `80776000`, while sign/card/cutlery reuse their existing models. The
ground bitmap at `804AA250` preserves source category 17's diary mapping and
adds cedar independently. Only the common descriptor constructor is redirected;
the four existing seasonal entry wrappers and scenery remain unchanged.

The loaded packet extends the unchanged 64,064-byte festival prefix to 94,240
bytes and ends at `80778000`, adding 30,176 resident bytes. It uses the same
startup slot: twenty descriptors, 676 of 688 bootstrap bytes. The builder checks
the prior packet, every resource, memory spans, physical placement, and guards.
The complete original cartridge/save files are never overwritten.

### Stationery window

The full 3,088-byte orange-paper packet resides at `80777000`. Its complete
models and resources use physical segment-zero pointers, including both interior
vertex slices. The shared rebasing helper checks each slice against its complete
vertex resource; it does not drop vertices or reconstruct approximated artwork.

The native letter owner `03B60000`, linked at `80888E90`, retains its complete
original code/data. Its 64-entry background, line, and colour tables each gain
one entry through checked relocated references. The added style is 64, with the
official colour and both full models. The enlarged owner uses 768 additional
menu-pool bytes. The ordinary source artwork, editor, text positions, and timing
remain unchanged.

The constructor's call at `8088A760` uses the shared carried adapter. New letters
normalize quantity states `2040..2043` to style 64. Imported artwork needs no
native paper DMA; the adapter leaves the native buffer and offset untouched.
Putting a resident-art pointer in that buffer would allow a later native paper
load to overwrite the shared packet. Native styles retain the complete original
loader through its actual relocated constructor address.

### Next consumers

Continue the shared importing task without rescanning or recompiling these
unchanged resources:

1. Connect native inventory action/hand consumers to the installed state helpers,
   including paper/spirit split/merge and letter consumption. The source
   `mTG_1catch_proc`, `mHD_prepare_drop_paper`, `mHD_prepare_drop_wisp`, and
   `mTG_select_tag_decide_item_normal` describe the shared interactions. The
   current tag owner is `03950000`, linked at `8086F310`. Its native letter
   collection call at `808734F8` uses `2000 + saved style`; style 64 needs the
   new collection/profile path, not the original short catalogue bitset.
2. Connect the remaining actual item interactions: sign-board placement/design
   handling; card stamping/menu behaviour;
   Harvest cutlery interaction; coconut eating/planting and tree behaviour;
   cedar planting/growth; spirit split/merge/catch/release and field behaviour.
   Preserve the installed event/card/cutlery paths. Item-specific behaviour is
   part of importing, not an exception to defer automatically.
3. Extend canonical saved identities, parent-owned profiles, and paper collection/
   catalogue bindings for the whole batch. Reuse format-15 card/cutlery fields;
   drawing support alone does not establish safe persistence or consumption.
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

`tests/test_v3_carried_runtime.py` supplies six focused checks for the current
cartridge's full packet/records/artwork, original identities and reader chains,
seasonal descriptors, native letter tables, interior vertex bounds, and sanitized
state/constructor readers. The existing browser/offline comparison passes empty,
all-supported, unrelated, one-diary, all-diaries, calendar-only, and tournament-only
profiles. Empty remains exactly V2-14. The ROM checksum and reconstructed UPS
also pass the ordinary builder checks.

The current build preserves saved format 15 and the existing selected profile.
V2 and format-14-or-earlier V3 cannot read format-15 saves; older profiles missing
selected diary styles remain incompatible. No ordinary save/reload, native
letter rendering, or carried-item gameplay is claimed. Ready/selected masks stay
zero until the missing consumers are connected. Both stable V2-14 deployments
and the main build lock remain unchanged. Native diary/creature fixture budgets
stay exhausted; this work does not restart them or clear their uncertainty.
