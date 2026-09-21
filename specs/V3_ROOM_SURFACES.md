# V3 additive floors and wallpapers

## Scope and current implementation

The general furniture pipeline's `surfaces` representation discovers complete
GameCube floor/wall banks, preserves existing N64 identities, converts missing
surfaces in a batch, and retains their names, prices, catalogue order, acquisition
lists, and floor-sound selectors. The shared runtime installer connects complete
artwork to player-room/shop double-buffer readers, single-buffer arranged rooms,
and catalogue previews. Shared full-name, price, and item-category readers use
the same ten identities. Shared room reservation/application and full saved-byte
reading are installed. The format-4 save category supplies optional-profile
validation and independent ownership. Native inventory actions preserve full
surface IDs; catalogue page lists and bit dispatch use the new ownership category.
Base surface scoring, all five additive matching themes, and full-index footstep/drag audio
are installed. Shared A/C/event stock supports six additions with selected-only
membership and selection. The private composer exposes those six surfaces as
individual or all-selected options, with real catalogue counts and independent
saved profiles. HomePage/Harvest acquisition remains required; complete shared
theme and furniture birth-point categories are installed. The four associated records stay disabled; installed
artwork alone does not make them selectable. Ordinary gameplay and persistence
are not established by category installation.

Use the current explicit experimental lock; keep the main lock and both stable
website deployments unchanged:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --representation surfaces \
  --base-lock build/v3-start-disabled-imports-01/cartridge/build-lock.json \
  --output build/v3-room-surfaces-prepared-02
```

`scan --representation surfaces` records the complete inventory. Preparation
accepts individual canonical donor IDs with repeated `--select`, a `floor` or
`wall` category, or all missing surfaces by default. `--reuse-assets` verifies
and copies complete prepared objects. These are developer preparation options;
no experimental choices are added to the served browser patcher.

## Source banks and identities

### Selected-only stock

The shared stock installer copies each complete original 192-byte floor/wall
goods resource, appends expanded A/C/event lists, and updates only the affected
segment-six pointers. Each complete replacement occupies 272 bytes. Native
descriptors retain the table offset and use size-derived temporary allocations;
the original DMA resources stay intact. The complete donor acquisition lists
bind each added identity to its real category. HomePage and Harvest additions
are not substituted into ordinary/event stock.

The helper at `804BFE00` wraps the complete native list getter and existing shop
category chain. Only short, terminated floor/wall lists are compacted, before
native membership or random selection reads them. Original items stay; additive
items require enabled metadata. No RNG, rarity, season, or other item-category
behaviour is replaced. The code and bridge occupy 480 bytes of reserved packet
memory. There is no new permanent allocation; each temporary list grows 80 bytes.
Private selection still controls whether any imported metadata is enabled.

Both donor banks contain 67 player surfaces followed by four shop surfaces.
The original N64 banks contain 64 player surfaces and four shop surfaces. Floors
contain one 32-byte palette and four 64×64 CI4 tiles, totalling `2020` bytes.
Wallpapers contain the same palette and two tiles, totalling `1020` bytes.
Conversion changes RGB5A3 palettes to native RGBA5551 and untangles each complete
8×8-block texture independently. Unsupported partial alpha rejects.

Full decoded-pixel matching identifies 124 existing player surfaces and ten
additions, with no ambiguous matches. Eight donor shop surfaces map from indices
67–70 to native 64–67; shop textures are not selectable imports. The pinned item
worksheet independently identifies all ten additions as lacking an N64 item.
Equal numerical indices alone never establish identity.

The four edition replacements remain distinct content. N64 bath tile floor,
old plank floor, bathhouse wall, and worn earth wall remain available. Donor
western desert, backyard lawn, western vista, and backyard fence are additions,
not replacements or renamed original items.

## Stable reservations

`tools/v3_registry.py` owns append-only surface reservations independently of
selection order. Native floor-sound identifiers extend through 72 even though
the player/shop texture bank ends at 67. New reservations begin at 73, preserving
the post office, police station, travelling merchant, broker, and igloo sound
identities. Paired wallpaper/floor additions use the same index so the existing
room-series scoring representation can identify a matching pair.

| Donor pair | Contents | New index | Native item pair |
| --- | --- | ---: | --- |
| `2612` / `2712` | western desert / western vista | 73 | `2649` / `2749` |
| `261A` / `271A` | backyard lawn / backyard fence | 74 | `264A` / `274A` |
| `2640` / `2740` | block flooring / mushroom mural | 75 | `264B` / `274B` |
| `2641` / `2741` | boxing ring mat / ringside seating | 76 | `264C` / `274C` |
| `2642` / `2742` | harvest rug / harvest wall | 77 | `264D` / `274D` |

Reservations do not imply complete item integration. Each native home record has
independent full-byte floor/wall fields at offsets `14`/`15`; neither field packs
unrelated flags. Native initialization and application preserve all eight bits.
The original floor getter alone masks player/NPC floor identity to six bits;
the selected-surface wrapper preserves additive IDs and retains original masking
for other values. Preserve the complete native home payload and establish
complete item/profile integration before enabling a surface. The
[format-4 extension](V3_SURFACE_SAVE.md) has an explicit compatibility warning;
V2 and older format-1/2/3 V3 builds cannot read its saves.

## Complete metadata and preparation

The source REL supplies all 16-byte English names, 67-entry catalogue orders,
terminated price tables, and the complete 23-entry acquisition pointer tables.
Every non-null list is resolved through its actual relocation. All lists must
terminate, contain valid unique IDs, and cover each player surface exactly once.
Prices retain their complete source words; catalogue eligibility is not guessed
from the price or acquisition label. Acquisition routes remain genuine donor
routes, including A/C stock, event stock, HomePage/Mario delivery, and Harvest.
Missing routes cannot be replaced with arbitrary shop stock.

The single `translations/provenance.json` catalogue credits the prepared names
to the official GameCube localisation, with source symbol, index, and exact
name-record hash. Existing human edits are checked and preserved. Artwork and
generated metadata stay in ignored `build/` directories.

The complete donor 95-entry and native 73-entry floor-sound selector tables are
source-hash checked and retained. This establishes numbering and dependencies,
not complete sound equivalence: the runtime installer checks corresponding
complete programs, instruments, samples, and walking/running variants. The existing
campsite floor getter deliberately uses native sound slot 68; preserve its
wrapper when extending ordinary room-floor identity.

Prepared caches verify source banks, registry, metadata, paths, and complete
converted objects. Partial, changed, ambiguous, or unknown resources reject.
Ten objects total 61,760 bytes; conversion requires no compiler container or
cartridge write.

## Shared room/shop texture runtime

`tools/v3_furniture_install.py --refresh-runtime --room-surfaces-art <prepared>`
installs the complete prepared category using the explicit predecessor lock.
Five floor records and five wallpaper records are appended contiguously in
stable destination order. Original texture banks are neither moved nor copied.
Additional cartridge artwork is 61,760 bytes; RAM and saved state do not grow.

`overlays/v3/room_surfaces.c` supplies both native owners. The player-room actor
at VROM `00846860`, linked `80951A70`, calls floor/wall readers at `80951BC4`
and `80951CDC`. The shop actor at `0084F180`, linked `8095A3B0`, calls the same
implementation at `8095A514` and `8095A62C`. Each complete native function has
280 bytes. Both compiled pairs contain identical 520-byte instructions/padding,
with 40-byte stack frames, no local data, and only a fixed engine-DMA call.

All original indices 0–67 retain their original complete palette/texture reads.
New indices 73–77 resolve into the separate appended banks. Missing indices,
invalid buffer selectors, null actors, and null individual buffers issue no
out-of-range transfer. The argument registers are explicitly narrowed as the
retail functions do. Buffer selector 2 refreshes both buffers; 0/1 changes only
that buffer. Floor/wall pointers remain at actor offsets `180`/`188`, with two
pointers each. Texture sizes remain `2020`/`1020`.

Installation checks complete native function hashes, incoming control flow,
compiled entry positions, and complete relocation tables. Each owner removes
eight obsolete debug-string relocations within the rewritten functions. The
remaining owner bytes, relocation entries, and all caller targets are retained.
The common owner-tail allocator stores full uncompressed owners without changing
their logical DMA identities or overwriting earlier ROMs.

Focused checks cover the actual shared C under memory-safety sanitizers, complete
installed objects, owner/relocation mutations, and unchanged selection/saves.
The native representative probe copies the installed pair into an isolated
20-KiB arena and uses real DMA for original/imported floor and wall resources.
Room/shop instruction identity avoids repeating an identical execution. This
does not establish ordinary room entry, GPU drawing, item use, or persistence.

## Shared catalogue and arranged-room consumers

The same refresh command extends an already installed surface category without
appending or recompiling its artwork. `surface_single.c` occupies the complete
arranged-room wall/floor functions at `80950EC8`/`80950F1C` in owner `00845C40`,
linked at `80950E50`. The pair uses 164 bytes and no stack/local data. Original
indices 0–67 and additive 73–77 have bounded complete transfers; invalid indices
and null destinations do not transfer. The constructor's checked 72-byte bounds
window accepts original player indices 0–63 and additive 73–77, retains fallback
63 otherwise, and preserves all remaining constructor code and actor sizes.

`surface_preview.c` replaces the two complete catalogue setup functions at
`808A6854`/`808A694C` in owner `03970000`, linked at `808A6100`. The pair uses
480 bytes and 40/32-byte stack frames. It preserves the native preview's half
scale, -90 Y position, wall/floor draw types 2/3, timer, profile/offset fields,
16-bit item interpretation, and actual A/B/C-stock price eligibility. Complete
palettes/textures come from the existing or separate added bank. Missing indices
and null texture buffers cannot cause out-of-range DMA. This is texture setup,
not new item orderability or complete catalogue ownership integration.

Each owner retains its complete original function checks and control-flow
guards. Four obsolete debug relocations are removed per owner; all other
relocations remain. `v3_garden_runtime.install_catalogue` reapplies the checked
installed preview code to fresh catalogue builds, checks the complete original
preview functions, and records updated owner/relocation hashes. Ordinary bulk
imports must not silently discard surface readers.

Focused tests cover the actual C under address/undefined-behaviour sanitizers,
all preview fields, price-query ordering, full owner/relocation reconstruction,
constructor mutation rejection, future catalogue retention, and unchanged
save/profile composition. A bounded native probe uses complete installed reader
copies, real DMA and native stock/pricing, and the actual constructor bounds
block in an isolated 16-KiB arena. It does not run the entire arranged-room
constructor, ordinary room entry, GPU draw, item use, or save/restart.

## Runtime integration queue

1. Apply genuine acquisition categories and complete Harvest/Mario furniture
   themes. Floor sounds, base surface scoring, and the existing Western,
   Backyard, and Boxing matching pairs are installed from the shared registry.
2. Connect private individual/all composition to enabled metadata, independent
   required-profile bits, and counted catalogue lists. Preserve the original 64
   rows; compact selected imports in source order without changing their IDs.
3. Bind the prepared contact/floor lifecycle to installed surfaces. The mower
   also requires the donor room owner's movement sound dispatch in
   `aMR_SetMoveSE`; that owner handles both lawn mower and stone coin sounds.
   Colour callbacks alone do not complete the parent behaviour.
4. Verify changed acquisition/selection paths and an ordinary menu/save cycle
   before a private playtest handoff. Retain passing unchanged reader,
   catalogue, inventory-body, application, and save-component evidence.

Do not replay unchanged rendering or earlier cartridge tests for preparation.
Native execution, in-game appearance, ordinary transactions, save/restart, and
hardware acceptance remain separate from source and converted-resource checks.

## Shared item names, prices, categories, and startup

`tools/v3_surface_items.py` consumes the complete installed surface records. It
retains each full sixteen-byte official name and complete unsigned price word
under its stable destination. Both native category tables independently contain
64 entries of category 12; their complete contents and pointer bounds are checked.
Missing indices 64–72 and 78–255 in either surface group cannot fall through to
the native unchecked category-table access. Original 0–63 indices retain the
prior native/imported item dispatch chains. Name arguments retain their full
width; type/price arguments narrow to sixteen bits like their native entries.

The 16-KiB permanent packet at `804BC000..804BFFFF` follows the existing scrolling
packet and ends below the model pool at `80500000`. Its 912-byte reader/action code has
24-byte stack frames. The `AFSI` metadata header at `804BC800` carries version 1,
count 10, and stride 24. Each row stores item/price halfwords, one enable word,
and sixteen name bytes. Only enable word 1 is accepted; all proposal records
contain zero. The complete packet ends with four `AF5351DE` guard words.
The format-4 category extends code and saved state within owned memory;
there is no new heap, actor, or scene allocation.

A 128-byte bootstrap occupies `804A8D40..804A8DBF`, in the checked unused gap
after parent metadata and before the retained equipment guard at `804A8FF0`.
It performs real DMA, checks the entire new packet's CRC, flushes caches, and
then calls the original furniture-table initialiser at `8046A000`. A compile-time
startup target selects this chain; the complete startup remains 960/992 bytes.
DMA/checksum failure does not mark startup installed or run the remaining init.
The equipment packet's full hash and startup CRC are updated; its size is unchanged.

The public name/type/price entries at `801969C8`, `800A5630`, and `800C0194`
call the new wrappers. Non-extended items delegate to the exact previous entries
`80467300`, `804AA000`, and `80467574`. Existing display aliases, clothing,
equipment categories, and full furniture readers are not replaced. Future
category updates must preserve these outer hooks and the startup chain.

Actual C and bootstrap failure cases pass memory-safety sanitizer checks. The
bounded native probe verifies the complete packet loaded by ordinary startup,
actual public entries, all ten names/prices under temporary fixture enable flags,
disabled and invalid IDs, original-floor name/category, complete restored packet,
guards, and unchanged saved extension. It restores an emulator checkpoint; it
does not establish room application, acquisition, ordinary save/restart, or
hardware operation. Optional profile/save validation uses the same enabled
metadata in the format-4 category; acquisition, remaining themes, and private
selection must finish before any surface is offered for selection.

## Room reservation, application, and complete home identities

`tools/v3_surface_application.py` extends the installed category through the same
refresh command. Its complete item/action code occupies 912 bytes before metadata
at `804BC800`, without changing artwork, scene allocation, or native saved fields.
The separate [save category](V3_SURFACE_SAVE.md) uses later packet storage and
extends the saved selection/ownership format, not native room-ID storage.

Both native reservation entries, `8095267C`/`809526D4`, delegate to a shared
helper. Arguments narrow to sixteen bits. Null clips/owners, busy queues, wrong
item groups, missing identities, and disabled imports return zero without
changing the actor or exchanging an item. Original application indices 0–67
remain accepted; additive 73–77 require their exact enabled metadata record.

Two checked 32-byte windows in native wall/floor commit functions
`80952444`/`8095253C` call the same predicate. The remaining complete functions
retain menu-close deferral, pending-flag clearing, room eligibility, buffer flip,
actual texture DMA, saved-byte writes, sound calls, and native notification.
Complete function hashes, incoming branches, and relocation intersections are
checked. All existing relocations and owner sizes remain unchanged.

The full floor wrapper at `800BEEC4` reads original home bytes for scenes 20–22
and the actual NPC floor query for scene 6. Selected additive IDs remain intact;
other values retain the native low-six-bit fallback. Invalid player-home indices
reject without an out-of-bounds read. Other scenes delegate to the complete
existing campsite/native wrapper, retaining special-room sound identities.

Homes begin at payload offset `3588`, stride `B48`, with four records. The
native default initializer stores complete bytes, and the room initializer at
`80951F14` reads complete bytes into actor halfwords `174`/`176`. The complete
current save runtime and its installed hooks are checked; native payload-copy
lengths remain `F980`. No extra room-ID storage is needed. Surface selection and
catalogue ownership use the explicit format-4 category; complete room bytes
alone do not supply profile guards.

Actual C sanitizer fixtures cover the shared reserve/predicate/getter, original
scene routing, all four homes, and a host-side full-payload save/read/commit. The
bounded native fixture executes a complete relocated installed room owner with
a private actor. Real reserve/commit paths, menu deferral, complete DMA, saved
home-byte writes, and the untouched native initializer reload pass. It restores
all saved/transient fixture data and the emulator checkpoint. Live-player
notification, ordinary inventory exchange, real FlashRAM restart, GPU appearance,
and hardware operation are not established by this fixture.

## Full-index floor sound dispatch

`tools/v3_surface_audio.py` handles the complete five-floor category together.
It binds the verified donor selector table and full SFX sequence to actual
native programs, complete instruments, envelopes, predictors, loops, samples,
and shared priorities. Corresponding numerical IDs alone do not establish
equivalence. Native walking variants have stride nine; donor variants have
stride ten. All eight variants for each distinct selector are checked.

Native grass programs remain complete but unreferenced in the sequence.
Reserved group-three slots 9, 18, 27, 36, 45, 54, 63, and 72 bind those exact
programs for the additive lawn. None overlaps any variant reachable from the
73 original floor selectors. Existing live program pointers and complete
program data stay intact. The raw lawn drag sound differs from the original
sound with the same number. It uses a new group-zero slot 80 and a complete
source program, reusing the exact existing instrument. All 80 original movement
slots remain in the extended 81-entry table, with no priority changes.

Independent 256-entry halfword tables at `804BFA00` (walk selectors) and
`804BFC00` (full raw movement sounds) fit the existing surface packet. All 73
original selectors and special rooms remain unchanged. Added indices use their
checked donor bindings; other byte indices fall back to the original wood
selector instead of reading outside a table. The actual native player, NPC,
and drag functions at `800F9064`, `800F9170`, and `800FA520` receive only checked
pointer-load changes. Their scene conditions, angle/distance/volume/reverb,
walking/running selection, and complete common dispatcher remain native.

The complete sequence grows by 176 bytes without new instruments or waveforms.
Shared audio resource installation retains existing batches and headers and
grows only fixed/permanent audio capacity by 1 KiB. Session pools stay unchanged;
conservative spare capacity is 896 bytes. This is measured heap growth, not an
assumption that an Expansion Pak automatically changes native allocations.

Host checks cover source/program equivalence, original mappings, complete
resource retention, bounded patches, CRCs, selections, and UPS reconstruction.
The bounded native fixture verifies actual loaded data, heap pools, complete
player/NPC/drag callers, selected priorities, saved state, and guards. Original
SFX channels self-modify twelve explicit index/group operands via C7 stores;
the fixture checks those stores and live operand bounds instead of comparing
live dispatch state to zero-filled ROM operands. No synthesis, listening,
ordinary room interaction, or original-hardware verification is implied.

The room owner's `aMR_SetMoveSE` equivalent, which chooses mower/stone-coin
movement effects, remains part of contact/floor lifecycle integration. Completing
the public floor-sound readers does not implement that separate caller.

## Full-index HRA scoring

`tools/v3_surface_scoring.py` supplies independent 256-entry halfword point
tables at `804BF600` (floors) and `804BF800` (walls), inside the existing packet.
Original indices 0–63 use the complete checked native birth/weight tables,
including the native lottery value. Added indices 73–77 use donor base values
412, 51, 1000, 412, and 1177 respectively. Gaps are zero. Donor acquisition
categories need not index the smaller native furniture counters.

The complete native base evaluator at `809274F8` is checked before changing
its 88-byte surface accumulation window at `80927794`. Each full index is
bounded before a direct halfword load. Existing furniture points, the caller's
points, stack, and epilogue remain intact. Six old pointer relocations are
removed without increasing owner or relocation storage. The actual home reader
already passes full bytes; no additional home-format change is needed.

Source-bound Western, Backyard, and Boxing series adapters map donor pair
indices 18, 26, and 65 to stable native indices 73, 74, and 76. The complete donor
theme extension also maps Harvest 66 to 77 and Mario 64 to 75, retaining their
distinct base-series/theme rules. Native partial and complete scoring uses these
pairs. Complete furniture birth-point categories use the shared 27-counter
evaluator. Actual delivery remains required; installing these definitions does
not enable an unfinished import. The ordinary furniture
installer accepts checked mapped indices as well as explicitly missing pairs,
so future bulk imports retain this shared mapping.

Focused verification covers complete resource/relocation reconstruction,
unchanged original values and resources, exact no-import/all-import composition,
and UPS reconstruction. A bounded native fixture runs the complete evaluator
and existing theme routines in a small isolated arena, preserving furniture
accumulation and checking matching bonuses, invalid indices, saved-state
restoration, and guards. It does not test ordinary score letters or hardware.

## Catalogue category lists and inventory exchange

`tools/v3_surface_menu.py` installs one 144-byte, leaf catalogue helper at
`804BF000` within the existing 16-KiB surface packet. It extends the actual
ownership-bit query for the active player's wall/floor pointers (`B68`/`B70`).
Original indices 0–63 delegate to the actual native function, including debug
behaviour. Added indices query the stable full-item ownership entry at
`80469AD4`; invalid surface indices cannot enter the native eight-byte arrays.
Other catalogue categories retain the existing native/furniture dispatch.

The catalogue's checked 84-byte ownership wrapper receives a sixteen-byte entry
bridge. The bridge passes the real relocated native function to the resident
helper. Two new HI16/LO16 relocations replace the two old surface-table pointer
relocations; image and relocation lengths are unchanged. Both existing caller
sites retain their targets. Original native executable code and all other menu
resources remain intact. The installer checks the complete predecessor wrapper,
both original lists/descriptors, occupied memory, and all changed relocations.

Floor and wallpaper list reservations at `804BF400`/`804BF490` each hold 69
halfwords: original 0–63 followed by the five stable imports in source order.
Descriptors at catalogue addresses `808AF7B4`/`808AF7AC` point to these resident
lists and count only available rows. With imports disabled, both counts remain
64, preserving category completion. Private composition must compact only
selected imports into each tail and set count `64 + selected`; reserved entries
alone are not available imports. Native category construction retains full IDs,
page capacities, source names, navigation, and completion logic.

The shared catalogue builder reapplies these descriptors and the checked entry
bridge after a fresh build, alongside the retained preview readers. No new
submenu pool, actor, texture, saved-state, or artwork allocation is needed.
The complete packet and existing equipment bootstrap retain DMA/CRC checks.

The native wallpaper and floor inventory actions at `808726B0`/`80872748` each
contain 152 bytes. They read a complete pocket halfword, invoke room clip offset
4/8, and store the complete returned item halfword. They do not mask indices to
six bits. The installed surface reservations therefore receive full IDs without
another inventory patch. Focused native execution copies each complete action
and substitutes only its UI index/close calls. The actual pocket exchange and
installed room reservation run, but ordinary UI navigation is not established.

The native catalogue fixture uses the complete real overlay loader and
initializer. It verifies disabled/uncollected states, all ten collected
identities, full names, original rows, complete/partial indicators, selected
list counts, and guards. It restores private state and the emulator checkpoint;
it performs no explicit FlashRAM write, GPU comparison, or hardware test.
