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

The current development proposal is ABI 355 at
`build/v3-carried-runtime-work-01/storage-connected-06/build-lock.json`.
Its ROM SHA-256 is
`3494ba7a2519718166b20e5b592c47b3a3ebe13a01a34adb8378685fdaab21c5`.
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

Code occupies `80771000..80771EE0`; the 864-byte table starts at `80773800`.
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

The loaded packet extends the unchanged 64,064-byte festival prefix to 105,904
bytes and ends at `8077AD90`, adding 41,840 resident bytes. It uses the same
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

1. Connect the remaining actual item interactions: sign-board placement/design
   handling; card stamping/menu behaviour;
   Harvest cutlery interaction; coconut eating/planting and tree behaviour;
   cedar planting/growth; spirit capture/release and field behaviour.
   Preserve the installed event/card/cutlery paths. Item-specific behaviour is
   part of importing, not an exception to defer automatically.
2. Verify actual native item-type/menu routes across all families. The shared
   registry's drawing categories do not themselves widen native type switches.
   Reuse the installed inventory, collection, catalogue, and save adapters;
   do not rescan the unchanged native owners or recompile prepared artwork.
3. Bind independent parent selections in both experimental composers, preserve
   empty-selection V2-14, and verify the changed readers and save/profile bounds.
   Acquisition follows primary importing. Gold-tree work remains required after
   primary imports, along with any unfinished golden-tool behaviour.

### Inventory and hand actions

The same `--carried-items` route continues the inactive installed batch without
reconverting resources. `carried_actions.c` maps quantities through the registry,
not donor paper-ID arithmetic. Complete pinned donor functions describe the
menu, single pickup, both stack merges, hand drop, and confirmed letter saving.

The tag owner gains four menus, indices `47..50`, for outdoor paper, outdoor
paper with burial available, the player's room, and other interiors. Counts are
`5/6/5/4`. Every existing word, handler, and final `Quit` position remains; the
additional `Grab One` word reuses existing English and binds the shared splitter.
The predecessor still supplies gift/quest restrictions and ordinary field rules.
The actual menu call at `80875834` uses the new adapter. Single sheets retain
their native menus; ticket menus and their handlers remain unchanged.

The native hand call at `8087B184` redirects to the shared paper/spirit merge
adapter. Its matching JAL relocation is removed; every other hand instruction,
relocation, data field, and BSS size is preserved. Both source and target must
be ordinary items of the same selected family, below that family's stack limit.
The original drop routine performs the actual swap/animation and refresh:
the combined stack goes into the pocket, overflow remains in hand, and a full
stack or unrelated item follows the unchanged native exchange path. The common
single-pickup handler fills native hand fields and decrements the pocket without
passing a donor quantity into native ticket arithmetic. Spirit field interaction
and its eventual menu admission remain pending; stack helpers alone do not
make spirits usable.

Only the letter confirmation branch's inventory-setter call at `80889434` uses
the paper-consumption adapter. It subtracts one sheet from all four imported
quantities; a singleton clears its slot. Original paper keeps the original
setter, and cancel/rewrite branches are unchanged. This preserves letter timing
and the installed complete editor. Collection, catalogue, and saved-profile
validation share the installed identity path below.

The action code preserves the entire preceding reader prefix and every public
entry, fitting the existing reservation with no added resident bytes. The tag
owner grows to 45,744 bytes and adds 512 menu-pool bytes. Allocation validation
checks successive descriptors for the same owner before comparing the final
descriptor with the actual parent; an earlier allocation is not mistaken for
the current one. All seven readiness/selection bits stay zero.

### Saved profiles, collection, and catalogue

The complete 11,648-byte save adapter occupies `80778000..8077AD80`, followed
by a 16-byte guard. Thirty public entries in the preceding save owner redirect
to it, including card access/clear, compression, load validation, live commit,
save preparation, and diary capacity checks. Earlier callers retain their
addresses. Canonical town format eight, registry five, the original FlashRAM
banks, and the 120,336-byte scratch plus its 16-byte guard remain unchanged.

The compressed envelope is format 16. Its existing 48-byte `AFHC` allocation
uses wire version three, retaining every card-stamp record at `16 + player*8`:

| Header offset | Meaning |
| --- | --- |
| 4 | Wire version 3 |
| 7 | Required exercise-card/cutlery bits, matching carried bits 2/3 |
| 8 | Seven required carried-family bits in the shared registry order |
| 9..12 | One orange-paper ownership bit for each of four players |
| 13..15 | Reserved zero |

Current selection validates the entire `AFCP` header, readiness, mask bounds,
and agreement with the existing event-item selection. Required selections are
conservative: discarding an item does not remove its dependency. Ownership
without paper selection, unknown bits, invalid records, or missing required
families fail before live state/output commit or device writes. Valid format-14
and format-15 records migrate with empty paper ownership, preserving attendance,
diaries, fishing, and console data. Adding supported selections preserves
ownership; removing a required family rejects the save. Player deletion clears
only that player's paper ownership and card stamps. Card updates preserve paper.

The existing native record/owned entries use `carried_collection.c`. All four
paper quantities share the same saved style; other reserved carried identities
never reach short native catalogue arrays. Original identities delegate through
the complete existing reader chain. Nonresident ownership queries return false;
an attempted nonresident record retains the existing save-error boundary rather
than crediting a resident. This is not new carried-item passport support.

The native letter collection call at `808734F8` supplies `2000 + style`;
style 64 consequently reaches the same ownership path. The catalogue has one
additional entry, index 67/item `2043`, for a four-sheet pack. The `B78` paper
bitset query uses separate ownership for that entry, never reading past the
native eight-byte array. All original 64 indices retain native/debug behaviour;
other pages retain the installed surface/furniture reader.

The 320-byte catalogue adapter fits at `80771EE0..80772020`, inside existing
carried-code padding. The actual paper-initializer call at `808A6B80` skips DMA
only for selected imported paper, uses style 64, the original `-93` height and
`0.28` scale, and the quantity's checked source price. Unrelated paper invokes
the complete relocated native initializer. Both original 64-entry model tables
gain the full resident background/line model. The original drawing function and
its mask/material commands remain intact. The catalogue owner is 63,888 bytes;
its relocation is 736 bytes, and its menu-pool allowance grows by 704 bytes.
The shared resource planner consumes each checked catalogue placement once,
preserving source resources instead of allocating duplicate copies.

These changes add no new translated wording. All prepared artwork is retained;
the new requirements are not used to enable incomplete field behaviours.

## Verification and limits

`tests/test_v3_carried_items.py` covers complete state discovery, official names,
source prices, all pocket bindings, unchanged event-icon output, reusable
category integrity, nested stationery geometry/resources, and rejection of
recursive models, changed price code, invalid offsets, or unknown UI state.
Existing source-category and UI-state rejection checks cover the changed shared
converters. No emulator, old candidate, or hardware test is implied.

`tests/test_v3_carried_runtime.py` supplies seven focused checks for the current
cartridge's full packet/records/artwork, original identities and reader chains,
seasonal descriptors, native letter tables, interior vertex bounds, and sanitized
state/constructor/stack-action readers. It checks every paper/spirit stack-count
pair, protected and unrelated items, single-sheet consumption, menu contexts,
actual installed callers, and retention of the hand's native sections/relocations.
The host relocation model explicitly accounts for the original hand's indexed
money-table base (`808742A8 + 2100*4`), binding both instructions and its complete
four-entry table; it does not permit arbitrary out-of-owner pointers.
The existing browser/offline comparison passes empty,
all-supported, unrelated, one-diary, all-diaries, calendar-only, and tournament-only
profiles. Empty remains exactly V2-14. The ROM checksum and reconstructed UPS
also pass the ordinary builder checks.

`tests/test_v3_carried_storage.py` covers the changed actual save transaction with
native I/O doubled: all seven missing-family cases, unchanged output/live state
on rejection, format-14/15 migration, four-player ownership and deletion,
retained card/diary/console state, and old-reader rejection. Sanitized real
carried readers cover all paper quantities, catalogue ownership/preview fields,
and disabled/native delegation. Current cartridge checks verify all thirty
redirects, collection/caller bindings, both complete preview tables, original
owner preservation, full packet contents/checksums, and patch reconstruction.
The current seven-profile browser/offline comparison and allocation chain pass.

The current build uses saved format 16. Compatible older saves migrate forward;
V2 and format-15-or-earlier V3 cannot read new saves. Profiles missing required
carried families or diary styles remain incompatible. No ordinary save/reload, native
letter rendering, or carried-item gameplay is claimed. Ready/selected masks stay
zero until the missing consumers are connected. Both stable V2-14 deployments
and the main build lock remain unchanged. Native diary/creature fixture budgets
stay exhausted; this work does not restart them or clear their uncertainty.
