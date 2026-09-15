# V3: optional GameCube content imports

## Objective and boundary

Add villagers and items from the supplied **Animal Crossing (USA, Canada),
GAFE01 revision 0** disc to the translated N64 game. The browser patcher offers
individual selections, category selection, select all, and clear all. Imports
are off by default. Existing N64 villagers, items, locations, and the translation
remain available; importing means adding content, not silently replacing an
existing villager or painting a new name onto an unrelated item.

The stable baseline is V2-11, SHA-256
`8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507`.
The import-free path reproduces the pinned translation baseline exactly.
V3 development uses `v3/optional-imports`; the public V2 patcher, deployment
recipe, local V2 service, and published trailer remain unchanged.
V3 source and development work may be version-tracked on GitHub. Updating the
local or public web patcher to V3 requires the user's testing and subsequent
explicit approval. GitHub source publication does not authorise either update.
Provide private playtest builds first; completed implementation or developer
verification alone does not authorise the web-patcher switch.

Japanese GameCube editions, including e/e+, are follow-on donor adapters, not
assumed interchangeable inputs. Confirm exact editions, revisions, and source
resources before enabling their options. Do not download game images. The
currently supplied English disc is enough to begin the main implementation.
An e/e+ input requirement must not stop unrelated English-donor work.

## Verified starting facts

The pinned source references are N64 decompilation
`4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be` and GameCube decompilation
`09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c`. Local paths below identify those
checkouts, not new dependencies to download.

- N64 `upstream/af/include/m_npc.h` defines 216 villagers. Name-file padding is
  not extra characters. The GameCube donor has 236 name records and 238 entries
  in several runtime tables; entries 236 and 237 are test characters and are
  excluded. The actual disc confirms 20 additional named identities.
- GameCube `src/data/npc/grow_list.c` and the donor's `npc_grow_list` classify
  18 of those additions as islanders. Cheri and Punchy are ordinary starter
  villagers. Islander artwork does not supply ordinary town behaviour by itself.
- Default records contain clothing, a catchphrase string index, and an umbrella
  index. The native loader advances six bytes per record and transfers eight
  bytes, so an extended table needs safe final-read padding. The five-byte C
  comment is not the array stride. GC catchphrase indices are not N64 indices.
- N64 `src/code/m_npc.c` has a 27-byte selection bitset, a 216-entry shuffle
  array, loops and bounds using 216, and direct personality-table readers.
  Raising a single limit would be unsafe. The saved appearance-history field
  is already 32 bytes (`include/m_common_data.h`); do not enlarge it merely
  because the transient candidate bitset needs expansion.
- Villager personal identities include an eight-bit name ID, with `FF` used
  as a no-name sentinel. The first 20 additions fit the numerical range, but
  that alone proves neither complete reader support nor save compatibility.
  Larger e/e+ rosters need a separate capacity/identity decision.
- The donor furniture name tables contain 1,024 and 242 records. Its name reader
  handles furniture ID types `1xxx` and `3xxx` and four rotations per record.
  The native translated furniture-name resource has 947 rotation groups.
  These are storage counts, **not** a subtraction that establishes new items:
  placed-object aliases, shifted mappings, duplicates, and unused records need
  identity review. Ordinary item groups also require review, even when counts
  happen to match.
- Existing N64 runtime names and item readers are bounded for native IDs.
  Appending donor names is not sufficient to install an item. The relevant
  table and loader work is described in `ITEM_NAMES.md`, `NPC_NAMES.md`, and
  the later reader specifications linked from those documents.

## Import catalogue and persistent identities

`tools/v3_import_catalog.py` verifies the original N64 SHA-256, donor header,
both actual donor resource hashes, decoded REL hash, and pinned symbol/decoder
files. It emits an ignored local inventory, not a public patch or executable
import menu. The inventory preserves names, donor IDs, source hashes, villager
roles/default dependencies, and furniture rotations.

Donor identities use `GAFE01-r0/villager/00D8` or `GAFE01-r0/item/3000`.
These are source identities, not N64 destination IDs. The raw inventory leaves
destination IDs null; the separate [versioned villager registry](V3_NPC_DRAW.md)
reserves new actor IDs without declaring them playable. The
[furniture registry](V3_FURNITURE_RUNTIME.md) reserves the two reviewed static
pilot IDs independently of selection. Other item rows remain unreviewed until
native identity and behaviour are established; a name match alone cannot approve
them. The inventory deliberately does not call all 2,333 donor item-name records
new or importable. No inventory row is currently selectable.

The implementation catalogue must distinguish:

- Already present in N64, with a verified identity mapping.
- New donor content, awaiting conversion or missing a concrete dependency.
- Fully implemented and eligible for selection.
- Duplicated/aliased or unused/test content, with an explicit explanation.

Track model/texture, behaviour, English text, acquisition or move-in, persistence,
and verification independently. An inventory record or passing extraction test
is not a playable import. Do not introduce another general translation percentage
tool for this work.

Assign destination IDs in a versioned registry independent of selection order.
Never compact IDs when a checkbox is disabled: a saved object must not become
a different object under another profile. Cross-donor aliases must share a
reviewed identity instead of duplicating content under alternate spellings.
Keep source hashes and conversion revisions attached to each compiled import.

## Runtime work

### Villagers

The [cat/cub artwork converter](V3_VILLAGER_ART.md) produces Punchy/Cheri texture
objects with verified model/skeleton correspondence. The
[additive asset loader](V3_ASSET_LOADER.md) installs their texture banks and
preserves all original object banks. The [native draw routes](V3_NPC_DRAW.md)
install pilot draw rows in both NPC overlays and preserve full donor voice IDs.
The [melody adapter](V3_VILLAGER_AUDIO.md) installs their verified donor programs
and full-ID audio paths; focused native audio/draw checks pass. The
[text adapter](V3_VILLAGER_TEXT.md) connects shared names, full catchphrases,
native default reset, and four-byte borrowed/default references. Its focused
and native reader/insertion checks pass. The
[initial-default adapter](V3_VILLAGER_DEFAULTS.md) connects Cheri's verified
starting shirt/defaults and both pilots' personality lookup. The complete
variant connects Punchy's actual imported cherry shirt to his initializers and
the shared selection predicate. Native initialization, full name/catchphrase
insertion, clothing transfers, and dependency rejection pass. Ordinary gameplay/
save integration remains pending.
The [house adapter](V3_VILLAGER_HOUSES.md) installs Cheri's complete mapped
furniture/music layers and verified native surfaces, preserving original houses.
Focused native initialization and layer transfers pass; complete scene loading
and ordinary visits remain unverified. The complete variant installs Punchy's
house with the animated speed bag and actual cherry-shirt dependencies. The
complete native arithmetic block, house initialization, sparse pointers, and
all four imported foreground transfers have passing evidence; a separate
breakpoint-driven diagnostic remains recorded as failed. Do not infer working
house visits from these component checks.
The [secondary reader adapter](V3_VILLAGER_READERS.md) connects full names in
map, inventory, letters, recipient selection, conversation identity fields,
and generated-mail capture. Native names/aliases and saved field sizes remain.
The [selection adapter](V3_VILLAGER_SELECTION.md) expands unseen counts, history
reset, initial population, and normal move-in selection with independent
transient arrays. The [explicit town policy](V3_TOWN_RESIDENTS.md) connects all
twenty complete metadata/house/outfit records to selected town eligibility,
preserving donor roles and the six native personality schedules. The experimental
cartridge enables these identities for integration; native resident creation and
schedule checks are not complete ordinary gameplay or playable-browser support.
The [house-gift adapter](V3_VILLAGER_REWARDS.md) includes enabled imported
furniture in native room rewards while retaining exclusions, random selection,
full identities, and the existing stored reward field.

Start with one ordinary donor-only villager, then the second. Integrate model,
textures, expressions, the compatible species animation rig, English name and
catchphrase, personality, default clothes/umbrella, house data, move-in selection,
conversation, mail/recipient display, departure, and saved identity.

Audit every ID-indexed table and upper bound before allowing an extended ID to
reach ordinary gameplay. Allocate expanded transient tables in verified memory;
preserve DMA padding, owner lifetimes, relocation, and resident guards. Adapt
GameCube asset formats to the N64 renderer rather than copying executable or
graphics commands under an assumption of compatibility.

For islanders, implement explicit town-compatible schedules, dialogue, and houses
while retaining donor appearance, identity, and personality. Record each needed
adaptation. This is not an implicit commitment to port the GBA island subsystem;
if an import needs a materially different player-facing behaviour, identify the
choice before claiming faithful support.

The [islander accessory converter](V3_VILLAGER_ACCESSORIES.md) supplies all
sixteen separate donor accessories with actual consumer/joint bindings and
complete native graphics conversion. Retain these accessories when enabling
their eventual imports.
The [twenty-body bundle](../docs/checkpoints/V3_GORILLA_ART.md) includes
all sixteen required accessories and Yodel's separate full model. Complete expressions,
species layouts, and real shared face/matrix/material bindings are verified;
town/runtime integration is not implied by these converted components.
The [complete-asset loader](V3_COMPLETE_VILLAGER_ASSETS.md) installs all 38
objects in fixed banks 410–447, safely relocates growth permissions, and passes
native object-loading and population checks. The
[attachment runtime](V3_ACCESSORY_RUNTIME.md) installs all twenty draw records
and all sixteen accessories in both NPC owners. Full text,
defaults/houses, town behaviour, ordinary appearance, and persistence still
require integration; move-in flags remain off.
The [complete audio converter](V3_COMPLETE_VILLAGER_AUDIO.md) supplies all twenty
melodies and four missing instruments while retaining all original instruments.
The [complete audio runtime](V3_COMPLETE_AUDIO_RUNTIME.md) installs all sources
and expanded bank/wave resources, with native loading, font relocation, melody
copying, and allocation checks passing. Playback of the four new instruments
and the final post-audio guards remain unresolved; this remains a handoff issue.
The [complete text installation](V3_COMPLETE_VILLAGER_TEXT.md) supplies all
twenty names and full phrases, preserving personality and donor growth values.
Full-name aliases, actual dialogue insertions, borrowed phrases, and profile
handling have focused/native evidence. The [aloha outfit runtime](V3_ALOHA_OUTFITS.md)
installs both actual shirts and all eighteen islander defaults, with complete
native resource/name/price/default checks. The
[complete display/catalogue adapter](V3_ALOHA_DISPLAY.md) supplies all three fixed
mannequins, canonical readers, ownership, conversion, and complete native preview
loading without another allocation. Ordinary aloha acquisition and persistence
remain work before the imports are ready for a complete handoff.
The [islander arrival houses](V3_ISLANDER_HOUSES.md) install all eighteen authentic
initial rooms with reviewed existing furnishings and complete native wall/floor
matches. All twenty imported houses and forty fixed layers are present; actual
native initialization and layer loading pass. Ordinary house entry, scene
allocation, move-in progression, and persistence remain open. The explicit
town policy supplies checked selection and the existing personality schedules.
The [outdoor-house adapter](V3_HOUSE_EXTERIOR.md) connects the complete roster to
actual structure selection, door/NPC checks, and daily-growth protection, fixing
the invalid second-player construction. The [marker adapter](V3_HOUSE_MARKERS.md)
gives all twenty imported houses a separate temporary foreground range, retaining
original building IDs and the existing RAM allocations in a 64-MiB cartridge.
Complete house interactions and persistence still require gameplay evidence.

### Items

Establish canonical identity using native/donor item definitions, object/profile
tables, renderer assets, and current translated-name mappings. Review furniture
and ordinary groups, including clothing, stationery, walls/floors, tools, songs,
fish/insects, and miscellaneous items. Do not mistake stack states, rotations,
or alternate representations for independent imports.

Build a complete simple decorative-furniture import first. It must display the
right model and English name, use correct dimensions/collision/rotation and
price, appear through an ordinary acquisition route, place/pick up correctly,
and survive saving/loading. Extend catalogue flags, shops/rewards, inventory,
mail attachments, room scoring, and special readers where the item requires it.

The [static furniture converter](V3_FURNITURE_ART.md) produces complete native
haz-mat barrel and oil drum assets for Cheri's house, with verified donor profile
bindings and seven passing focused tests. The
[native furniture loader](V3_FURNITURE_RUNTIME.md) installs stable item identities,
resident profiles, expanded readers, and native model-bank selection/cleanup.
Five focused checks and the bounded native check pass. The
[shared item readers](V3_FURNITURE_ITEMS.md) add full names, category, donor price
values, and placement footprints, with four focused checks and native verification.
The [room adapter](V3_FURNITURE_ROOM.md) connects 21 range checks, two index
conversions, and four field-type scans, with focused and native register/delay
verification. The [shared field adapter](V3_FURNITURE_FIELDS.md) connects both
complete native room-grid builders and donor-backed shop eligibility, with
focused/native checks. The [menu adapter](V3_FURNITURE_MENU.md) connects action
menus, hand destinations, and room-placement dispatch, with focused/native checks.
The [inventory icon adapter](V3_FURNITURE_ICON.md) connects the separate leaf reader,
with focused checks and actual native selection/drawing-command verification.
The [ground adapter](V3_FURNITURE_GROUND.md) connects drop flags and ground-descriptor
selection, with focused/native checks. The [pocket adapter](V3_FURNITURE_POCKETS.md)
connects both shared furniture count/index queries, with focused/native checks.
The [collection adapter](V3_COLLECTION.md) connects native acquisition/collection
and live-player clearing to saved imported ownership. The
[catalogue adapter](V3_CATALOGUE.md) connects collected rows, full names,
selection, model previews, prices, and completion. Four focused tests and a
70-step native check pass. The [shop adapter](V3_SHOPS.md) connects actual native
goods lists and category queries, with four focused tests and partial native
stock/acquisition evidence. The [shop interaction adapter](V3_SHOP_INTERACTIONS.md)
connects twenty decisions across all five shopkeepers, with focused tests and
native interaction-window/ticket checks. Both complete imported-order letters,
readback, and pending clearing pass. The [shop-floor adapter](V3_SHOP_FLOOR.md)
connects reserve points, floor selection, and sold-removal classification, with
focused tests and native selection/branch checks. Ordinary acquisition/payment,
model removal, and the full item lifecycle are required; these are not
playable imports. The [HRA adapter](V3_HRA.md) connects native evaluation,
actual donor metadata, theme groups, and missing-item recommendations, with
focused checks and native execution. The [feng shui adapter](V3_FENG_SHUI.md)
connects actual donor colours to native item/room evaluation and retains N64
point weights, with focused checks and native execution.
Punchy's speed bag has its actual animation/interaction adapter and connected
stock, catalogue, scoring, and save profile. Ordinary gameplay/persistence and
final appearance verification remain open.

Then batch imports by shared conversion and behaviour needs. Interactive
furniture, music, tools, living creatures, and other mechanics need their actual
behaviour, not a generic decorative placeholder labelled as complete. Missing
engine features stay explicit work rather than silently dropped scope.

The [construction batch](V3_CONSTRUCTION_ITEMS.md) adds complete conversion for
seven opaque-only furnishings, retaining all models, textures, material states,
names/prices, stock groups, and scoring properties. Combined table generation
retains current imports and native data. The
[construction runtime](V3_CONSTRUCTION_RUNTIME.md) installs all seven complete
objects, fixed profiles, shared item readers, and saved-profile dependencies
without another RAM allocation. Native readers and paired model-bank loading
pass. Catalogue capacity, ordinary stock/scoring installation, optional
composition, and gameplay/persistence remain required for complete imports.

### Limits and saves

Target an Expansion Pak-equipped N64 with 128-KiB FlashRAM and RTC, retaining
the existing hardware requirements. Measure actual loaded memory, display-list
capacity, asset lifetime, and cartridge-size limits. The builder currently caps
ROMs at 64 MiB; 32 MiB of output padding is not proof that any content fits RAM.
Keep fail-closed build guards for source identity, bounds, relocation, and CRC.

V3-with-imports save compatibility is **not established**. Preserve all existing
saves and builds. Use copied or disposable saves for tests. Record an explicit
matrix for V2 → V3, V3 → V2, unchanged profiles, adding imports, and removing
imports. Do not claim backward compatibility merely because field widths remain
the same. A save referencing disabled IDs needs safe handling, a migration, or
an explicit incompatibility warning; it must not silently load an unrelated ID.

Export a deterministic profile alongside each ROM: base build/hash, registry and
converter versions, selected identities, dependencies, and output hash. Design
any runtime save/profile guard only after the save layout audit; no reserved
storage is assumed free. The [save/profile codec](V3_SAVE_PROFILE.md) defines
the reviewed two-bank extension and records the native read/write integration
constraints. The [FlashRAM runtime](V3_FLASH_RUNTIME.md) connects actual save/load
hooks and the incompatibility warning, with isolated fresh-process persistence
and cold-boot rejection checks. Ordinary gameplay/catalogue and Controller Pak
integration remain required. The web patcher does not upload or edit saves.

The [local optional composer](V3_OPTIONAL_COMPOSITION.md) resolves per-entry
selections for the twenty installed villagers and six installed logical items,
including required outfits, house furnishings, and mannequin representations.
It updates actual native enable fields and save profiles without new code or
allocations. Empty selections reproduce V2-11; all installed selections reproduce
the pinned complete integration cartridge. These are experimental local profiles,
not complete donor coverage, playable-import certification, or served web options.

## Browser implementation

Keep all ROM/disc reading and conversion inside the browser worker. The existing
disc slicing, CISO support, hashing, cancellation, and static hosting are reusable.
The fixed-output V2 recipe is not sufficient for arbitrary combinations: add a
validated composition format with pinned base, conversions, explicit writes,
dependency ordering, collision checks, and deterministic final CRC/hash reporting.
Do not prebuild every possible checkbox combination.

The interface provides searchable villager/item lists, individual checkboxes,
category select/clear controls, and select all/clear all. Show existing or
unsupported content accurately with the reason it cannot be selected. Select all
means all implemented additions for the verified supplied donors; it must not
claim to include unfinished candidates. Required playable-content dependencies
are disclosed, not silently enabled as unrelated additions.

Changing a selection or input invalidates old results. Cancellation releases the
worker and download URLs. Equivalent selection sets produce the same profile
and cartridge regardless of click order. The source files remain untouched.
Keep both served patchers on stable V2 until the user has tested V3 and
explicitly approved the switch. A verified playtest handoff alone is not approval.

## Delivery order and acceptance

1. Verified donor inventory and durable scope/identity/save design.
2. One complete ordinary villager and one simple furniture item as local pilots.
3. ID/runtime expansion and profile-aware composition, with import-free retention.
4. Batch remaining English-donor conversions and behaviours; adapt islanders.
5. Per-entry web selections, dependencies, select all, profile downloads, and
   actual browser reconstruction of the changed cartridge.
6. Bounded combined tests and a V3 build for original-hardware playtesting.
7. Separate e/e+ donor adapters after exact sources and additional requirements
   are established. Preserve the English-donor milestone independently.

Tests concentrate on the changed loader/renderer/ID/persistence paths and a
representative combined profile, including select all. Reuse accepted V2
evidence for unchanged content. Known crashes, save damage, and memory corruption
block a playable handoff; exhaustive seasonal or every-subset testing does not.
Do not mark the goal complete while requested imports are merely inventoried,
renamed, disabled without resolution, or awaiting required runtime implementation.

## References

- [Pinned GameCube definitions](https://github.com/ACreTeam/ac-decomp/blob/09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c/include/m_name_table.h).
- [Pinned GameCube growth permissions](https://github.com/ACreTeam/ac-decomp/blob/09ca8e8b5b24e6ab44047ee980cf0088ad7ecb4c/src/data/npc/grow_list.c).
- [Pinned N64 villager implementation](https://github.com/zeldaret/af/blob/4ddba04604ee7b4c4cfc0b64f8ee4d094bb385be/src/code/m_npc.c).
- [Source and e+ reference assessment](../docs/SOURCES.md). The existing
  [e+ translation checkout](https://github.com/ColinGamez/animal-crossing-ePlus-translation)
  is not a verified content-conversion source; its completeness claims do not
  establish an import format or trustworthy translations.
