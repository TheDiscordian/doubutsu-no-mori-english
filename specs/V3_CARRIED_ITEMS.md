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

The current development proposal is ABI 366 at
`build/v3-carried-field-work-01/quest-manager-03/build-lock.json`.
Its ROM SHA-256 is
`5ae6fe11ae14560c36c53da7f809c14949d26bb96fc8899e4edf69486d140fcc`.
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
adds cedar independently. The common descriptor constructor uses the complete
seasonal allocation, including the installed gold/palm/cedar drawing banks.
Their shared table, four actor index arrays, and local stack are sized together;
growth, planting, collision, shaking, cutting, and complete leaf/cut effects
are connected. Independent selection remains unfinished. See
[shared seasonal scenery](V3_SCENERY.md#palm-and-cedar-dependencies).

The loaded packet extends the unchanged 64,064-byte festival prefix to 105,904
bytes and ends at `8077AD90`, adding 41,840 resident bytes. It uses the same
startup slot. Including the independent tree-effects and quest packets, the startup
has 22 descriptors and occupies 676 of 688 bootstrap bytes. The builder checks
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
   Harvest cutlery interaction; actual Wisp event ownership. Spirit inventory
   transfer restrictions and field/capture/release use the installed
   shared category consumers below.
   Coconut eating/planting, cedar planting/growth, and complete tree leaf/cut
   effects use the installed shared consumers.
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

### Global stationery quantity choice

`paper-quantities` is one ROM-build setting for **all original and imported
stationery**, independent of the orange-paper and spirit inclusion checkboxes.
The default is `N64` (single sheets); `GameCube` creates four-sheet packs.
The same choice governs shops, catalogue purchases and delivery, gifts, event
rewards, and other paper-creation routes. It is not a Wisp-only conversion.
No-import/default builds retain the exact translation-only baseline; a pack-only
build requires the shared stationery runtime without enabling unrelated imports.

Existing native singles `2000..203F` and imported orange states `2040..2043`
retain their identities. Additional native-style quantities use the fixed
`2E40..2EFF` reservation: three rows of 64 styles for quantities two, three,
and four. This is a destination reservation, not a source GameCube ID range.
The builder must verify its absence from original identities before installation.
Names, colours, ownership, and letter backgrounds always resolve to the style;
prices and pocket icons resolve to the actual quantity. Do not multiply a pack
again when picking it up, swapping it, attaching it to mail, or loading a save.
`carried_paper.c` separates creation policy from quantity-preserving operations.

Pack mode includes the shared grab-one, merge/overflow, and confirmed one-sheet
letter-consumption paths for every style. Native and imported paper must use
the same rules. Shop/catalogue descriptions and prices must describe what is
actually delivered. Existing packs are never silently discarded or converted
to a single sheet on load. A mode change needs explicit saved-profile validation
and a warning if the selected build cannot preserve the saved quantities.

`prepare_paper_quantities(output, lock)` in `v3_carried_runtime.py` prepares the
shared implementation from the checked current build. The complete preparation
is `build/v3-paper-quantities-prepared-10/`: 6,304 reader/action/supply/catalogue
bytes at `807B4000`, 32 native-bridge bytes at `807B6800`, 12,304 save-adapter
bytes at `807B7000`, a 13,344-byte letter owner with its complete 464-byte
relocation, and a 64,128-byte catalogue owner. The reservation ends at `807BB000`.
The source identity worksheet and actual native group-14 table retain the two
grab bags at `2E00/2E01`; the pack reservation starts at `2E40`.
Existing reader padding is occupied by live catalogue, food, and spirit code,
so expanded code must use the new checked reservation rather than overwrite it.

Shared name, category, price, display, pocket, icon, collection, menu, splitting,
merging, and confirmed letter-consumption readers have both modes in source.
Original paper does not depend on selecting orange stationery. The native letter
constructor maps the complete inventory ID at `8088A3BC` before storing a style
byte. Its 32-byte appended adapter preserves the live registers and normalizes
all native-style quantities to `0..63`; the existing orange loader keeps style
64. Resolving only the low byte would confuse some packs with orange paper.
Owner preservation and relocation at both existing test bases pass.

The prepared save adapter writes envelope format 18 and AFHC wire 5. The same
48-byte extension records pack mode in byte 15 without moving dates, ownership,
or card stamps. Binding retains required mode conservatively; a pack-dependent
save rejects single-sheet mode without modifying the record. Older supported
records can bind forward. Formats 17 and earlier cannot read new format-18
saves. Focused sanitized checks cover the actual policy/readers/actions and
the complete compressed save transaction with native I/O doubled. Both modes
retain partial quantities in all four players' native saved pockets. Formats
14–17 migrate forward; the older codecs reject format 18. Incompatible pack
mode rejects before output publication, adoption of live town/extension state,
erasure, or writing. Diary, console, card, and ownership data remain intact.
Ordinary native save/restart is not established by this host transaction check.

The preparation is installed in ABI 367 at
`build/v3-paper-quantities-installed-08/build-lock.json`. The existing quest
packet extends from `807AC000` through `807BB000`, with the new `AFPQ` end guard;
all 22 startup descriptors remain. Public reader, catalogue, and save entries
redirect to the new complete modules. Both composers expose the checked mode
word and refresh its containing startup CRC. Eight browser/offline profiles
agree, including four-sheet mode without imports and exact V2-14 for the default
empty profile. Both deployed V2 patchers remain unchanged.

The ROM space planner reclaims only a recorded superseded furniture/audio DMA
copy. Both complete historical hashes, the current live replacement, and absence
of live overlaps are checked before clearing that copy in the output image.
Source ROMs are never modified. Growing shop owners keep their DMA-directory
indices but receive disjoint virtual extents; relocation preserves every original
section and its BSS. The letter/catalogue menu allocations and complete loose-item
owner sizes include all appended adapters.

#### Stationery consumer map

Use this map for the connected installation, retaining the complete current
owners and prepared artwork. Creation is distinct from moving an existing item.

- **Installed shared creation:** `carried_paper_supply.c` wraps native seven-
  argument `mSP_SelectRandomItem_New` at `800BFCF0`. Original RNG, rarity, list
  loading, fallback, and exclusion logic remain intact. Only paper-category
  results get the global creation quantity. `800BF9B0` compares paper exclusion
  entries by style without mutating the caller's saved stock/inventory.
  The two background-only calls at `800A90EC` and `800A938C` bypass creation
  through the preserved native selector bridge. `mNpc_GetPaperType` and mother-
  letter paper selectors return artwork styles, not newly obtained stationery.
- **Installed category and catalogue:** the current `800C05E0` shop-category
  chain gains paper-pack/orange recognition and delegates unrelated items.
  Catalogue row construction at `808A9578` chooses the actual order quantity
  for each stable style index, including orange index 67. The appended adapter
  retains integer registers and HI/LO. The preview-family selector at
  `808A6B6C` recognises the pack reservation; the shared preview adapter gives
  native DMA a canonical style and prices the full actual quantity. The
  catalogue list feeds selected orders, Nook's quote/payment, and pending-mail
  attachments. Do not reapply creation while delivering an existing attachment.
- **Installed shop layout and rendering:** native shop-design owner
  `848BF0` / `80953E20` has paper ranges at `80953E78`, `8095488C`, and
  `80954BE0`, covering reserve positions, floor stock, and sold removal.
  The complete loose-item/shop drawing owner is managed by
  `equipment_resources.room_goods.diary_room_art`; reuse its existing expanded
  model table and loaded-pointer fixups. Its original paper row uses the
  `2000..2040` interval. All orange quantities and `2E40..2EFF` need the same
  native paper model without discarding the quantity stored in the world.
  All three floor branches and three temporary drawing queries now cover those
  ranges. The expanded drawing owner retains all 50 model rows and resources.
- **Installed shop interaction counters:** all five `shop_units.SHOPS` owners
  use `spec.handler` for item/count wording. The native high-byte/low-byte
  counter table cannot accept the new pack range or orange quantities directly.
  Local adapters normalize the counter lookup, not the purchased/sold item,
  preserving full-quantity pricing and non-paper branches. Existing generic
  inventory setters must never become paper-creation hooks.
- **Installed fixed gifts:** source `ac_npc_rcn_guide2_talk.c_inc` has the
  first-job stationery grant table in `aNRG2_set_possession` and its matching
  handover display table in `aNRG2_demo_start_wait_talk_proc`. Repeat-paper
  requests use that same route. The two native give calls and matching handover
  display use the shared policy. Do not rewrite every `mPr_SetPossessionItem`
  or `mPr_SetFreePossessionItem` call, which also handles existing items.
- **Installed selection:** retained reader, catalogue, and save exports redirect
  to the new shared module in the existing quest startup packet. The
  same checked choice record serves offline/browser resolution, including a
  pack-only profile. Default/no-import output remains pinned V2-14. Public
  and local deployments remain V2 until the user's V3 approval.

`test_global_stationery_policy` checks creation, stable catalogue indices,
preview style/price, exclusion matching, actual-quantity readers, actions, and
mode validation across all 65 styles. `test_stationery_native_consumer_preparation`
checks current source identity, native hook guards, all eight native consumers,
and complete letter/catalogue preservation at both relocation bases. Temporary
lookup-register checks cover all quantity identities and nearby unrelated IDs.
These are prepared-code/host checks, not native purchasing or delivery evidence.

Current native checks reach fault-free boot and match the entire new 6,304-byte
resident module. The paper fixture cannot obtain its 86,016-byte isolated scratch
allocation on the title screen: the first attempt calls the town allocator;
its one retry uses the native overlay allocator and also returns null.
No paper function or owner fixture executes. The setup retry allowance is spent;
do not loop on this harness. Ordinary gameplay and native save/reload remain
unverified. Results: `build/v3-paper-quantities-native-02/` and `-03/`.

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
passing a donor quantity into native ticket arithmetic. Spirit field/capture/
release consumers are installed below; actual event ownership and independent
admission remain pending.

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

### Food and planting interactions

The same carried-item refresh extends the complete inventory food category.
The source `mIV_pl_food_item_draw` and `mHD_open_end_proc_item_type3` functions,
both nine-entry drawing tables, native food drawer, and actual hand-index
consumer are checked. Both complete coconut lists reuse the installed category
28 artwork, with physical segment-zero pointers. No graphics are reconverted.

Two nine-entry tables occupy `80772020..80772068`, after catalogue code and
before carried records. Original foods keep indices zero through six, including
the null candy material. Coconut uses source index seven; the original turnip
moves to eight. Four inventory reference instructions point to these resident
tables, and their four internal relocations are removed in place. Only the
turnip index constant changes in the hand owner. Food scale, matrix/position,
frame timing, consumption, clothing/equipment branches, original segmented
artwork, inventory BSS, and owner allocations remain intact.

Packet/checksum receipts share the existing loaded resource; the tables consume
72 bytes of checked zero padding and no additional resident or menu allocation.
Saved format 16, readiness, and selection remain unchanged. Disabled reserved
items still fail the existing item-admission checks; these tables do not make an
incomplete tree family selectable.

The shared scenery adapter owns coconut/cedar burial and direct cedar planting.
The original tag action retains its search, placement, warnings, consumption,
sound, and close-window flow; its six-word seed conversion calls the resident
lazy-loading gate. All four seasonal throw previews preserve native flower
handling, angles, and animation. Source-based growth, actual coastal/elevation
conditions, death, regeneration, collision, and shaking/cutting share the
[tree-family contract](V3_SCENERY.md#connected-family-behaviours).

### Carried creatures and native capture/release

The same field/program converters accept carried-category records without
assigning museum or furniture identities. The complete prepared source and
artwork are in `build/v3-carried-field-prepared-04/`: fifteen pinned `aIHD`
functions and both complete spirit models, 1,440 bytes with four animation
entries (`a,a,b,b`). Native light fields retain the original `0x280` actor size.
The shared update keeps source floating velocity, two donor ticks per native
update, net-held animation, escape/fade, and light cleanup on actor destruction
and scene teardown. All eight preceding imported insect programs are retained.

The 7,536-byte linked field code begins at `80784000`; artwork begins at
`80786400`. Three 41-entry field tables begin at `80786A00`, followed by four
frame pointers and the checked eight-word resource descriptor at `80786C00`.
The `80784000..80787000` span occupies verified padding in the existing tree
startup packet, retaining the original tree code and page directory. The loader
copies the complete spirit resource into the existing native field buffer;
the draw adapter uses the native held transform, billboard, and translucent
command arena. Other insects delegate to the complete relocated native helper.
Twenty-one stable insect entries redirect to the shared extended lifecycle.
The original extra program buffers are reused, not allocated again.

The event bridge accepts the real 44-byte ghost common state and event status.
It checks `RUN` and `ERROR` independently and exposes all five acre records.
No installed event owner calls the bridge yet. Unbound means inactive, never an
invented running event; event ownership remains required before selection.

The 1,872-byte interaction adapter occupies `80772070..807727C0`, inside carried
padding after the food tables. Native menu selection at `80875834` retains the
previous complete reader chain and uses release outdoors/catch-only indoors for
spirits, preserving protected/multi-mark results. Both native release action
pointers use the shared handler; the original handler remains available for
unrelated items. Release decrements a spirit stack by one, keeps the native menu
closing/animation path, and requests insect type 40. Spirits never gain a cage.

The two actual net calls at `808CD518/808CD548` use stack-aware pocket selection
and item insertion. A compatible ordinary stack wins before an empty slot;
protected or full stacks are not overwritten. The complete native insertion
routine performs the mutation. Existing collection/last-catch adapters exclude
type 40. The catch-message bridge at `808CD070` selects the donor's message by
the first ordinary spirit stack already carried, or the initial message when
none is present. Original creatures retain their complete message adapter.

Messages `331A..331F` preserve official donor `2F03..2F08`: five count-specific
messages and the source's empty final record. The single provenance catalogue
credits each record. No words, line breaks, pauses, or colours are rewritten.
The shared text placer first packs displaced complete banks within existing
text ownership, retaining buffered contents before overlapping moves; only a
bank that no longer fits is allocated elsewhere. All old messages and choices
remain intact. No new resident allocation, startup descriptor, owner allocation,
or saved field is needed for these capture/release bindings.

Six native inventory predicate entries at `8010DD38` enforce the full source
transfer policy through the existing card/cutlery chain. Entries 2/4/5/6/8
(entrust, quest, sell, give, take) reject all five spirit states. Entry 13
rejects sign boards but deliberately allows spirits to reach the native
full-pocket release route. Original conditions, money restrictions, empty
storage slots, and fish-water checks remain in their complete predecessors.
Furniture and curator entries are retained. The complete native mailing
function at `80870AC4` already rejects the insect category; its two event-item
callers at `808760AC/80876348` remain intact.

The same installer refreshes the checked interaction reservation and rebinds
all existing native callbacks together. It verifies whole prior owners,
normalizes the three player calls to their checked original bodies, retains
relocation removals, and preserves the complete installed message bank. No
new text allocation, art compilation, resident bytes, or saved field is needed.

### Carried quest owner preparation

The native acre-entry call at `8092AF0C` uses `af_carried_insect_spawn` in the
retained `807AC000..807AE000` prefix of the quest packet. The complete code is
4,496 bytes; the shared startup checks the whole expanded packet. Its original body and relocation
remain unchanged apart from the two-instruction dispatch. The existing ordinary
manager remains the fallback, including its saved season and selected population
policy. No ordinary calendar gains a spirit entry.

Only a selected spirit family with bound RUN status, no ERROR, an active hunt,
and a matching one of the five quest acres enters the quest path. Wild insects,
colonies, offing/island rules, the complete habitat/rank/food filters, group sizes,
native tile positioning, and real creation failure remain in the shared code.
The source's countdown rule moves a lake spirit before ordinary acre spawning,
retaining its random draw order, whole lake-row/column avoidance, and 0/2/4 acre
duplicate check. The existing calendar observer handles native/imported countdown
identity; no donor event number indexes a native table directly.

The installer checks the full native manager and lake lookup, existing insect
packet, complete source calendar and spawn row, retained terrain helper, all
memory reservations, and physical resource allocation. Tree/page directories,
field resources, and old insect code remain unchanged. A nonquest acre delegates before applying quest-only
checks. This connects the spawning consumer, not the missing event owner.
The installed quest-state and manager services below call the field-state bridge; NPC
admission remains off, so the quest stays inactive.

`v3_holiday_participants.py --carried-event --build-lock PATH --output PATH`
uses the shared complete actor importer for the event NPC source directory.
It checks all 48 contiguous Wisp actor functions and four manager callbacks,
including every included conversation/schedule source unit. The complete
VR4300 object and its unresolved services are recorded in
`build/v3-carried-event-prepared-03/`. Only platform drawing submission and
state access are adapted; source logic for dialogue, rewards, roof choices,
weed removal, fade/movement, five unique spirit acres, and cleanup is retained.
Native NPC field access, text, rewards,
and lifecycle services still need real owner bindings. Date/flags, scheduling,
common-state ownership, complete manager callbacks, placement, and the spawning
consumer are installed. The prepared NPC actor object is not installed,
and an unresolved service is not a successful placeholder.

`build/v3-carried-wisp-art-01/` contains the complete draw-index-349 artwork:
6,688 model bytes, 4,128 texture bytes, 26 joints, five visible joints,
186 triangles, eight eye frames, and six mouth frames. The shared streamed
character converter retains source `FC123A0E/FFFFFE38` combining,
`C81049D8` translucent blending, primitive alpha, and LOD fraction. Wisp's
actor must supply the environment alpha through the real translucent renderer;
preparation alone does not establish live fading or drawing. Existing texture
and model limits are sufficient, without cropping or discarding resources.

## Installed hunt and save ownership

`carried_quest.c` maps source event 114 to additive native event 115. Original
native events 0..114 keep their identities. The native daily planner calls the
existing holiday/camper chain first, preserving its return value and job gate.
The hunt then follows `m_event.c`'s weekly Wisp scheduling: retain dates inside
`[today-7,today+4]`, otherwise draw a date two to four days ahead; install the
event when its date falls inside `[today-7,today]`. Month/year wrap and leap
years use the shared complete calendar. The row covers hours 0..3 inclusive;
planning sets EXIST only, never RUN, ACTIVE, or SHOW. The checked directory
append rejects damaged/full indexes before modifying any row. Both native daily
cleanup bounds include the new event, while the original donor-holiday mapping
remains unchanged.

Saved area 54 contains the donor's eight-byte angry-name/flags/renew-date record.
Common area 55 is a native 40-byte lifetime marker, not a truncated GameCube
record. The complete 44-byte temporary record and keep/placement state occupy
56 owned bytes at `807B3F00`. All native area lookups map the source ID explicitly
and require an existing daily row and selected, available quest. Losing the
native marker invalidates the private record and field binding. Binding uses
the actual native row's status address, so the spirit path observes real
RUN/ERROR flags. The separate keep word avoids indexing native bit arrays with
the additional event ID.

The source's town-wide yearless hunt date is stored as month/day at offsets
13/14 of the existing 48-byte card extension. Wire 4 validates the date and
requires the spirit family. It retains the family mask, four paper ownership
bytes, and all stamp records. Player deletion does not clear this town-wide
date. Format 17 carries wire 4; formats 14, 15, and 16 migrate through the actual
save transaction, preserving existing data and starting the new hunt date at
zero. Earlier readers reject format 17. Missing required families reject loading
before output, live state, or cartridge saves are changed.

The shared startup packet spans `807AC000..807B4000`: the complete existing
8-KiB spawn prefix, save code at `807AE000` (12,032 bytes), quest code at
`807B2000` (7,168 bytes including its complete manager), owned state at `807B3F00`, and a final guard. The
old spawn guard remains intact. Thirty-six public entries in the previous
storage module redirect to the new save code, including direct collection
consumers and earlier redirect chains. All other packet content is retained.
The bootstrap remains 22 descriptors / 676 bytes. Two documented obsolete
event/state startup copies are reclaimed only after verifying their complete
live replacement and its installed startup transfer. Original ROMs are never
modified; all current resources are retained.

Availability stays zero until the actual NPC, translucent rendering,
complete official conversations, rewards, and save/travel cleanup paths are
connected. This is an installed state/save path, not a playable Wisp claim.

### Connected event manager and remaining NPC bindings

The importer compiles the complete checked `manager.c` from
`build/v3-carried-event-prepared-03/` into the same quest module, without
reconverting artwork or recompiling the unrelated 48 NPC functions. Source
save/common/keep accesses bind to the installed `af_cw_*` services. The native
control directory gains row 115 with start, stop, in, and out callbacks; the
preceding 73 rows retain their positions, pointers, and relocations. The owner
and its descriptor grow by 32 bytes. The shared 80-reference allocation already
covers all 74 controls. Resident callbacks never relocate with this owner.

The source manager chooses five distinct acres, retains their random draw order,
resumes the current player's hunt only on the matching saved date, and keeps
the returned-spirit branch. Event stop removes every normal-condition spirit
stack through the native inventory API while preserving protected conditions
and unrelated pockets. This is event-end cleanup, not the still-required
successful-save/travel cleanup. Source appearance results distinguish absent,
appeared, and not-in-this-acre; the actual native placement record supplies a
successful result, not the source's developer-display pointer. Culling observes
native STOP status.

The shared placement API accepts the source edge margin explicitly. Ordinary
wandering and shrine owners keep their one-/two-tile margins; Wisp uses five.
The deterministic seed uses source event/name/area IDs even though the spawned
NPC name is additive. The existing native descriptor, landmark, collision,
foreground, height-gap, reserve/reuse, forward-acre, flattening, and spawn
adapters remain the shared implementation.

The NPC connection uses these existing components together:

- Source `Ev_Ghost_Profile` is profile `B7`, name `D06F`, size 2,480 bytes. The
  fixed additional reservation is name `D0CD`, profile `F0`, model bank 456,
  and texture bank 457. `build/v3-carried-wisp-art-01/` supplies every model and
  facial texture; reuse the shared streamed renderer.
- Extend the existing five-record special-character registry and 22-owner
  participant registry, retaining all records. The new owner needs independent
  spirit-family admission: the global participant gate belongs to diary
  holidays and must not become a spirit prerequisite. Reuse the checked NPC
  services and callback/slot lifetimes, with source event 114 routed to native 115.
- The source renderer adds pipe-sync and white environment colour with the
  current alpha to the translucent command stream, then invokes ordinary NPC
  drawing. Retain that sequence and stream-space checks. Source motion
  `GSTWAIT1` / default 126 needs the shared imported-motion provider, not a
  same-number native animation. The NPC's native parameter field is signed
  16-bit at `24`; `carried_event.h` declares the correct pointer type.
- The source actor's explicit platform dependencies remain in its existing
  `prepared.json`. Reuse installed festival/native bindings for ordinary
  conversation, demo, inventory, and field functions where their contracts
  match; provide real schedule/field/roof/weed and message mappings where
  they differ. Preserve all 22 source reward-list categories, including the
  two actor-local gyroid/umbrella lists, with mapped selected-item support.
- Import the complete official conversations and angry-name strings through
  the existing text/provenance pipeline. Actor registration, name/voice/art
  banks, rendering/motion, conversation/reward behaviour, and save/travel
  cleanup must all connect before enabling the spirit selection.

The focused source-manager check covers five distinct acres, repeated starts,
same-player/date restoration, returned spirits, appearance sentinels, culling,
event-end cleanup, protected conditions, and disabled admission. The shared
placement fixture compares 108 cases to the complete donor search, including
margin five. Current cartridge checks cover the exact new row, two relocation
bases, unchanged controls, all retained resources, the complete save/spawn prefix,
22 startup CRCs, and UPS reconstruction. Seven browser/offline profiles agree.
These are host/build results, not native gameplay or hardware verification.

### Connected NPC preparation

`v3_holiday_participants.py --connect-carried-event PATH --build-lock PATH
--output PATH` reuses the complete prepared actor and reference hashes. The
current output is `build/v3-carried-npc-connected-13/`, based on ABI 367. It
compiles every actor function with the shared registry, NPC services, event-save
routing, translucent draw service, imported-motion provider, and text mapping.
The native actor is 2,392 bytes. The object contains 33,192 text/constant bytes,
2,104 data bytes, and 2,262 BSS bytes. All services are bound. The shared linker
retains the entire 37,616-byte module at `807BF000..807C82F0`, including BSS and
guard. The descriptor and guarded actor pool extend to `807C8D70`. Full
character/registry/field/audio/storage installation uses ABI 368 at
`build/v3-carried-npc-installed-08/build-lock.json`.
No successful placeholder fills a missing consumer.

The source paper adapter binds to the installed global quantity provider at its
checked symbol, not a separate Wisp rule. `carried_voice.c` keeps click mode in
owned state and hooks native message initialization (`8009E6F8`) and the
animal-voice predicate (`8009F7CC`). Original prologues and fallback logic stay
in complete bridges. Resetting at message initialization preserves the source's
set-click-before-appear order. The native voice selector retains the player's
silent preference. Donor sound words `6B` and `16C` map to `6F` and `175` through
the shared complete-program converter. The first has two parallel layers;
timing is per layer, not the sum. Priority index 117 is unused in every native
and imported group and changes from 40 to 70 for the new program. Existing
programs and priorities remain unchanged. The generic allocator validates both
73-entry walking groups and every expanded trigger group before reserving a
shared priority; missing group evidence fails closed.

`carried_world.c` queues weed clearing in town storage rather than an ephemeral
event slot. Its native bindings are field renewal at `800561FC`, growth at
`80AB5188`, scene number at `80126EB4`, notification state at `80137922`, and
the loaded growth owner at `80100C5C`. At outdoor renewal it clears only IDs
8–10 across all thirty saved acres, skips weed regrowth for that renewal, and
consumes the flag only outside event-notification deferral. The complete native
renewal retains seasonal clearing, snowmen, trees, and other growth. Player
deletion and clearing the hunt date do not cancel the reward.

Installed format 19 uses AFHC wire 6 without enlarging its 48-byte state. Header
byte 15 retains paper mode in bit zero and uses bit one for pending clearing;
the latter requires the spirit family. The shared save adapter is 12,592 bytes
at `807BB000`, inside a 16-KiB reservation ending at `807BF000`. Both paper
modes pass the real compressed save transaction with native I/O doubled,
pending-reward retention, migration from formats 14–18, and older-reader
rejection. Format-19 saves need this or a newer compatible build; format-18
and earlier readers reject them. Four-sheet saves still require pack mode.
This is not a claim of ordinary native save/reload.

`carried_save.c` stages deletion of all five spirit identities in the active
player's copied inventory. Native save/exit entry `800965F4` distinguishes kind
1/3, mode 0 from the intermediate mode 1. Only pre-call state 8 and return 1
mean full success; error states also return 1. Entry `80096260` prepares the
staged buffer. Player-load/reset-guard preparation at `80095874` is untouched.
Both explicit save-menu calls at `80829584/80829664` use the complete-bank
write contract and clear live pockets only after all 512 pages succeed. Ordinary
save checks do not confuse allocation, FlashRAM, or Controller Pak failure with
completion. The private reset word remains at offset `AE0`.

The native departure path passes a temporary private copy at `801407C0` to the
passport writer. The shared creature adapter resolves that copy by its complete
16-byte identity against residents or the validated visitor. It retains creature
selection/collection data, complete passport checksums, and rejection before
writes. Combined town/Pak transactions defer live cleanup until the outer success;
standalone successful passport writes clear their passed private record. Sanitized
checks exercise both modes, false-success error states, failed allocation/erase/
pages/Pak writes, snapshots, visitors, and disabled-family behaviour.

The two new object banks keep indices 456/457, but use logical addresses
`04800000/04804000` outside the audio archive's `04000000..04800000` reservation.
The shared transfer table holds ten banks; its reader supports sixteen within
the existing 256-byte directory reservation. Both old DMA entries redirect to
the new reader after every startup packet loads. Registry, lifecycle, and save
redirects modify checked function entries, never state or linker boundary symbols.
The entire audio program/font/wave batch is installed. Its 9,232-byte append
relocates three complete 4-KiB tree-art pages, retaining their full hashes and
updating the paged directory and startup CRC. No artwork or sound is dropped.

Current cartridge checks cover all changed hooks, complete resources, text
credits, retained module bytes, 22 startup packets, and patch reconstruction.
Eight browser/offline profiles agree. Silent native boot checks the six-character
registry, ten-bank directory, final packet guard, and absence of a faulted thread.
Carried-family admission stays off pending the category's remaining consumers
and independent selection. Native Wisp interaction and save/travel are unverified.

The shared registry has 23 owners, eighteen temporary resident slots, and 25
live slots. Its 22 retained rows and source callback addresses remain intact.
The new source-event-114 owner uses its own availability and selected-spirit
checks, independently of diary admission. Descriptor identity, construction,
callback admission, destruction after selection loss, and retained-family
lifecycle use the same implementation. The spawn table extends through `D0CD`;
Wisp's saved-area calls route to the installed quest owner, not the older holiday
event map. Installed registry exports redirect so all actors use one state
allocation.

Native actor parameters are signed shorts at `24`; scale begins at `5C`, and
shadow enable is at `108`. Melody is a signed word at `930`, as shown by native
initialization stores and voice readers, rather than the source short or the
earlier unbound byte declaration. The draw service checks available translucent
command space, emits pipe sync and white environment colour with the source
alpha, and invokes the shared NPC renderer.

Source `GSTWAIT1` uses additive motion ID 382. Its complete 26-joint, 65-frame
curve and all 64 header bytes are retained. The shared converter accepts its
ordinary blinking sequence with an unused `-1` stop frame, while still rejecting
a stopped eye that would index an invalid texture. The new motion table keeps
all three installed festival motion pointers without reconverting them. Source
default animation 126 is explicitly mapped to 382 too. The prepared walk-only
schedule preserves source 60% walk / 40% wait decisions, fatigue/sleep checks,
turning, pitfall interruption, and block-edge initialization. Native SPECIAL
holds the callback; donor WALK_WANDER is not passed as an out-of-range native
schedule index. The original Wisp SPECIAL callback remains recoverable.

The complete official message closure is source `2ED3..2F02`, mapped to native
`3320..334F`; sixteen choices start at 524. No branch escapes that closure.
All 32 angry-name strings and the Wisp name are retained, with 97 exact source
credits in `translations/provenance.json`. The long introduction `2EE4` repeats
the same colour between literal lines. Removing ten already-active colour
commands lowers its conservative expanded bound from 1,073 to 1,023 bytes.
Every other command invalidates colour reuse except pauses, so page clears,
insertions, and NPC orders retain their explicit colour commands. No wording,
line/page boundary, colour change, or timing command is altered.

All twenty external reward lists are compiled in bulk, retaining 839 source
entries and their terminators; the actor's gyroid and umbrella lists remain
complete. The shared destination resolver maps all 998 candidates and the two
source fallback fruits through installed import records and the pinned native
identity worksheet. Runtime selected-item filtering covers both uncollected
and all-collected branches. Clothes and umbrellas retain the donor's always-
uncollected treatment. All paper rewards, including orange paper, use the
global quantity choice. Disabled donor identities never become native rewards.

Native message/item-name providers use the source closure and the already-mapped
destination; they do not accidentally use another participant's resolver or
translate an item twice. The actual NPC1 demo-order type is five. A refused
spirit handover does not consume pockets or advance orders, and failed reward
insertion does not advance the conversation. Handover requires the admitted
Wisp actor, local player, actual TALK state, and live handover service. Weed
queries cover the complete saved town/current field. Roof changes write native
current colour at `24`, preserving the unrelated ordered-upgrade colour at `25`.

`tests/test_v3_carried_npc.py` checks the changed shared admission/lifecycle with
diary admission both off and on, native field widths, translucent command bounds,
retained-family lifecycle, complete source/programme retention, official message
closure/bounds/credits, and the twenty source lists. The current complete source/
preparation check passes; unchanged registry checks retain their earlier evidence.
The new conversation fixture has two unsuccessful compile/link setup attempts
and no executed behavioural result. Its corrected source extracts the complete
functions under test without weakening ASan global checks; do not spend another
attempt on it in this batch. No successful conversation test is claimed.
The existing quest manager, artwork, save packet, and cartridges are unchanged;
no native gameplay, new ROM, or hardware result is claimed by this preparation.

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

Three focused `FoodTests` in `tests/test_v3_carried_runtime.py` verify source
bindings/rejection, all food entries, unchanged native instructions, relocation
at two bases, complete packet/artwork/save retention, startup CRCs, and patch
reconstruction. Current seven-profile browser/offline outputs agree. These
checks do not execute an ordinary eating animation or native save cycle.

`tests/test_v3_carried_creatures.py` checks complete source/model preparation,
sanitized full spirit lifecycle and retained eight-species behaviour, both
billboard poses while held/free, native loader delegation, stack-aware net
handover, protected menus, one-at-a-time release, and official message selection.
Changed-cartridge checks cover exact caller/relocation changes, retained tree
and insect packets, all startup CRCs, full old/new text, and UPS reconstruction.
The text-placement fixture covers moving a complete index within its original
owned bank range. Seven current browser/offline profiles agree, including
empty V2-14. No ordinary native capture, release, event gameplay, or hardware
verification is claimed. Focused interaction/current-cartridge checks also cover
all six inventory predicates, retained native mailing, and refresh without
duplicating dialogue. The source/art preparation check covers all 52 complete
functions, the big-endian MIPS object, all texture pixels, all model triangles,
and retained translucent state. Wisp ownership remains open.

The focused quest-spawn check executes the actual state bridge and shared spawn
algorithms with sanitized native-service doubles: inactive/error/selection
states, all five acres, ordinary delegation, occupied acres/colonies, rank and
food filtering, creation failure, and countdown relocation. Current cartridge
checks retain every preceding physical resource, verify the one native dispatch
and unchanged relocation, all 22 startup CRCs, and UPS reconstruction. The current
seven-profile browser/offline comparison passes with empty selection still
V2-14. These checks do not establish ordinary event gameplay or hardware results.

`tests/test_v3_carried_quest.py` exercises the actual planner and directory/state
services with native allocation/clock doubles, covering date expiry, inclusive
windows, leap/year wrap, random bounds, complete common-record lifetime,
allocation failure, disabled selections, and atomic directory rejection. Its
current cartridge check covers the entire retained spawn prefix and save packet,
all 36 redirects, exact native caller changes, all retained physical resources,
the owned state/guard, 22 startup CRCs, and UPS reconstruction. The extended
storage test covers format-17 persistence, format-14/15/16 migration, old-reader
rejection, player deletion, all seven missing families, and unchanged output
on rejection. Seven current browser/offline profiles agree. Native gameplay
and ordinary save/reload are not inferred from these checks.

The current build uses saved format 17. Compatible older saves migrate forward;
V2 and format-16-or-earlier V3 cannot read new saves. Profiles missing required
carried families or diary styles remain incompatible. No ordinary save/reload, native
letter rendering, or carried-item gameplay is claimed. Ready/selected masks stay
zero until the missing consumers are connected. Both stable V2-14 deployments
and the main build lock remain unchanged. Native diary/creature fixture budgets
stay exhausted; this work does not restart them or clear their uncertainty.
