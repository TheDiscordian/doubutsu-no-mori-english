# V3: optional GameCube content imports

## Objective and boundary

Add villagers and items from the supplied **Animal Crossing (USA, Canada),
GAFE01 revision 0** disc to the translated N64 game. The browser patcher offers
individual selections, category selection, select all, and clear all. Imports
are off by default. Existing N64 villagers, items, locations, and the translation
remain available; importing means adding content, not silently replacing an
existing villager or painting a new name onto an unrelated item.

V3 is only the import pipeline: extraction/conversion, additive stable identities,
bulk asset/data installation, working item/villager runtime behaviour and
persistence, official English text, and deterministic independent browser/offline
selections. V3 is complete when the import pipeline works for items and villagers.
Regular items should be obtainable through the regular item pool.

Rewards that fit existing systems are in scope for V3. Assess acquisition by the
actual systems it requires, not by whether an item is special or awarded as a
reward. Mail, holiday, gift, and golden-tool rewards are not automatically V4.
Items requiring an entirely new acquisition feature or building should not be
importable through browser or offline selections until that feature exists in V4.
V3 may prepare their conversion/resources, but should not put them in substitute
regular stock. Prepared integration and selectable imports are separate states.

New buildings and entirely new features, including savings accounts, Able Sisters/
custom designs, the Museum building, and island facilities, belong to V4.
Preserve existing experiments and evaluate reward consumers individually; no V3
task requires completing a new V4 system or choosing its replacement route.
Design-dependent sign boards and saved-pattern representations remain deferred.
Ordinary fish, insects, fossils, and other items retain their actual item
behaviours within V3 without adding the Museum. This boundary governs subsystem
notes below and acquisition continuations in their linked checkpoints.

The deployed patcher and ordinary local preview serve stable V2-14, SHA-256
`0e81d5c62548c3a759cc89d63eba0975b1c336a3a941211a3000e317b9243bf2`.
The current experimental proposal pins this same V2-14 for empty selection.
The import-free path must reproduce
its build's pinned translation baseline exactly. V3 development uses
`v3/optional-imports`; it must not change the deployed patcher or local preview
to V3 or edit the published trailer. Stable V2 corrections update the public
patcher and local copy.
V3 source and development work may be version-tracked on GitHub. Updating the
deployed patcher or local preview to V3 requires the user's testing and subsequent
explicit approval. GitHub source publication does not authorise either update.
Provide private playtest builds first; completed implementation or developer
verification alone does not authorise the web-patcher switch.

Japanese GameCube editions, including e/e+, are follow-on donor adapters, not
assumed interchangeable inputs. Confirm exact editions, revisions, and source
resources before enabling their options. Do not download game images. The
currently supplied English disc is enough to begin the main implementation.
An e/e+ input requirement must not stop unrelated English-donor work.

## N64 and GameCube behaviour choices

For runtime behaviour within an imported item/villager, when a substantial
player-facing difference would otherwise require choosing
N64 behaviour over GameCube behaviour, expose an explicit **N64 / GameCube**
choice in the V3 WebUI. Describe the actual difference in outcomes, interactions,
or timing. Do not silently replace donor behaviour with native behaviour and
call the import faithful. Necessary platform-format conversions alone do not
need a toggle; crashes and broken behaviour are defects to fix, not alternatives.

Use shared mechanic/category settings where the same difference affects several
imports, rather than duplicating implementation for every item. Keep these
settings distinct from the per-villager/item inclusion checkboxes. Record source
evidence, affected content, available values, and the explicit default alongside
the existing import records; derive offline and browser choices from that same
data. Both labelled behaviours require real runtime support. If a behaviour is
unfinished, record the missing work instead of presenting a nonfunctional choice.

Resolve behaviour settings together with import dependencies, include the
resolved values in the deterministic build receipt, and explain any save impact
before patching. Do not assume switching behaviours is save-compatible. With no
imports or behaviour changes selected, retain the pinned translation-only output.
Verify the changed shared path in each supported mode with focused checks, reusing
unchanged evidence. These settings follow the existing V3 playtest and deployment
approval requirement; they do not authorise a live-patcher update.

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

The [QD services](V3_CONSOLE_DISK.md), complete BIOS/boot data, native CPU/PPU/audio
bindings, disk I/O/IRQ/motor timing, reset retention, final-save capture, and
common room bindings are installed. The console converter retains nineteen full
game images, twenty launch records, and sixty save operations. All twelve
supplied additional console furniture models have complete profiles; Excitebike
has a real lottery route, while eleven await their source reward systems.
The absent game-twenty payload is a donor limitation, not unfinished emulation.

Format-five storage retains the full town and all four players' console records
inside the existing two banks, with capacity rejection before FlashRAM writes.
Native synchronous/asynchronous writing and fresh-process loading have recorded
evidence. A separate silent combined scenario at
`build/v3-console-combined-native-01/` verifies Clu Clu Land D and Wario's Woods
title execution/rendering, native Reset retention, and cleanup. Test-only menu/
return requests drive the real native callers; ordinary controller input, room
entry/world return, a new game-progress save cycle, audible quality, and hardware
are not established. Preserve this passing evidence for unchanged code/data.
See the [console checkpoint](../docs/checkpoints/V3_CONSOLE_ROOM.md).

Four additional paintings use full ordinary import integration. Shared built-in
profile staging installs complete resources even when acquisition is pending:
direct native models/contact, constant sequences, indexed flower palettes, and
the verified existing building-palette callback. Source identity, sounds/layers,
complete artwork, canonical records, callback dependencies, and inactive flags
are checked. No unfinished reward becomes substitute shop stock. The current
ABI-287 proposal has 167 selectable choices and 100 inactive furniture profiles;
the [bulk checkpoint](../docs/checkpoints/V3_BUILTIN_PROFILES.md) records its
identity and evidence. All official names use the single source catalogue.

The shared furniture converter prepares complete nested-model and dual-motion
resources for the aerobics radio and treasure chest. The ordinary importer
installs the chest's full scene/contact/motion/drawing lifecycle, both complete
multi-instrument trigger programmes, continuous sound, destruction, and native
saved-switch capture. Its actual island acquisition remains separate unfinished
work, so the profile remains unavailable for selection. The radio's
music-owner/emitter/drawing lifecycle is installed through the ordinary importer,
including original stereo interoperability and checked packet loading. Its source
indoor player-aerobics interaction is installed; its original reward route remains
acquisition work. All twelve complete player motions use the shared resource
loader, with enlarged animation banks and scene arena. The 18-gesture/chaining/
tempo core is registered with native controls, eligibility, camera, audio-clock
integration, and transient initialization. Source/host-adapter comparisons,
installed-resource checks, and private compositions do not claim native gameplay
or hardware testing.

The [combined rig importer](V3_FURNITURE_PIPELINE.md#reversible-material-and-particle-rigs)
installs complete reversible motion, delayed material selection, translucent
joint drawing, particle emission, and source audio through the shared category
pipeline. Crab stew retains all resources and its actual winter-camper route,
official text, scoring, and optional profile. Donor lifecycle comparisons,
sanitized host drawing, installed resources, and browser composition pass;
ordinary native play, saving with the item, and hardware remain unverified.

The [room-surface pipeline](V3_ROOM_SURFACES.md) prepares ten additive floors and
wallpapers while preserving all existing surfaces and special-room identifiers.
Complete resources, stable paired destinations, official names, source metadata,
and acquisition dependencies are retained. Shared resource, item, room-change,
and full home-byte readers are installed. Format-4 surface profile/ownership
validation is installed. Catalogue page lists/ownership dispatch and native full-ID
inventory exchange are connected. Full-index base weights retain native values
and add exact donor points; all five additive matching pairs and complete donor
theme/base-point categories are connected. Full-index player/NPC footstep and drag readers preserve original
mappings and bind complete donor programs/instruments with bounded audio storage.
HomePage password admission and the connected Harvest owner supply the four
remaining experimental selections. Each Harvest surface requires cutlery.
Ordinary acquisition and persistence remain required; experimental
selection does not establish playable-import acceptance.

The [shared password modules](V3_PASSWORDS.md) link the complete donor code
transform, eligibility rules, Nook results, and selected destination mapping for
277 implemented imports and 1,425 checked native correspondences. Bounded MIPS
code and sanitized donor comparisons are verified. The native engine passes 45
assertions across twelve cases for selected destinations, real DMA/CRC/cache,
RNG, preserved saved fields, guards, and cleanup. Four front counters have installed
input, official dialogue, and native animated handover bindings. Ordinary code
entry/delivery and persistence remain required before claiming usable password
rewards. Shared admission installs all sixteen password-only furniture records
and both HomePage surfaces without substituting shop stock. Five current
browser/offline profiles agree for 235 experimental choices. See
[the connected checkpoint](../docs/checkpoints/V3_NOOK_PASSWORDS.md) for the
incomplete enclosing scenario and retained setup allowance.

The [expanded import storage](V3_IMPORT_STORAGE.md) supports further batches
without adding to the full DMA directory. English choice data retains its
identity and contents at a new virtual address; the import resource gains a
larger checked reservation. Fixed canonical profile/item slots cover the existing
supported ID range without repeated metadata-table moves. This does not claim
that all slots contain converted items or completed gameplay.

The [camping batch](V3_CAMPING_ITEMS.md) installs seven complete static objects,
their English/item readers, catalogue framing and non-orderability, safe HRA
weight mapping, and selected dependencies without more resident memory.
Summer-camper acquisition remains an explicit engine dependency. The offline
composer supports these experimental choices without updating either patcher.

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
The [aloha scoring adapter](V3_ALOHA_SCORING.md) supplies both real clothing
records, with complete native grouping, point, and array-bound checks passing.
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

The [shared room-alias discovery](V3_FURNITURE_PIPELINE.md#room-display-aliases)
connects 48 donor display models to their actual parent items, including four
balloons in the older furniture range. The full donor inventory also identifies
seven worn-axe states as one parent identity. These are source-derived
relationships, not extra selectable furniture or completed native conversions.

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
pass. The [catalogue integration](V3_CATALOGUE_CAPACITY.md) supplies actual
753-slot pages, all 446 furniture rows, retained 248-row clothing, ordinary stock,
and complete scoring metadata. Native catalogue selection, scrolling, names,
model loading, B/C stock selection, and pocket ownership insertion pass.
The [offline composer](V3_OPTIONAL_COMPOSITION.md) connects all 39 installed
experimental options and their actual dependencies, including selected catalogue
packing/completion. Focused and native subset checks pass. Ordinary gameplay/
persistence and browser implementation remain required; neither patcher changes.

The [garden batch](V3_GARDEN_ITEMS.md) installs six complete decorative models,
shared readers, the 452-row furniture catalogue, scoring, saved dependencies,
and individual offline selections. The gnome uses the native lottery list and
can be reordered; the mailbox remains not for sale. Post-office reward delivery
and ordinary gameplay/persistence remain work.
The [reward-category adapter](V3_HRA_BIRTH.md) supplies expanded native counters
and donor reward weights, with focused and native verification. Backyard-series
installation is complete; post-office reward acquisition remains work.

The [Western batch](V3_WESTERN_ITEMS.md) installs seven more complete models,
English readers, true ordinary/event stock, catalogue/scoring, and optional
saved dependencies. The [dedicated bank owner](V3_FURNITURE_BANKS.md) provides
100 12,288-byte banks in reserved Expansion Pak memory without ordinary heap
growth. Separate catalogue model buffers have the same capacity. Native reader,
catalogue, event-selection, and scoring checks pass; bank construction and
first/last-bank DMA pass, while executed teardown remains unverified.
Both opaque saddle-fence parts and the well's double mirrors are
preserved. These are experimental imports, not certified complete gameplay.

The [full-sized Western batch](V3_WESTERN_LARGE_ITEMS.md) installs the remaining
three theme furnishings with true two-cell footprints, translucent water,
narrow texture rows, and explicit donor-to-native catalogue framing. A relocated
checked package adds 8 KiB while retaining save-code entry points and the existing
model/menu allocations. The offline composer contains 49 experimental options.
Ordinary gameplay, appearance, and persistence remain required validation.

### Limits and saves

The shared sustained-sound importer retains the donor's 96-entry level table
and the native expanded 128-entry dispatcher. Loop and trigger categories share
complete font/sample growth and resource placement. The extended wave archive
has virtual base `04000000` while actual audio continues using checked physical
ROM offsets; this does not increase cartridge capacity or the ordinary DMA
request limit. Installing a furniture sound does not establish its lifecycle,
acquisition, or playable eligibility.

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

The [optional composer](V3_OPTIONAL_COMPOSITION.md) resolves per-entry
selections for twenty installed villagers and 278 installed logical items,
including required outfits, house furnishings, and twenty-eight equipment parents.
Mannequin and equipment catalogue representations are dependencies, not separate
choices.
Six selectable surfaces have genuine A/C/event acquisition; two more use their
actual HomePage password path. The Harvest pair binds to the complete installed
Franklin owner and actual cutlery dependency. All ten have independent format-4
saved-profile bits. Floor/wall catalogue counts and selected-only stock follow
the same private selection records. Source reward surfaces remain non-orderable.
Ordinary acquisition and save/restart remain unverified.
Ten ordinary legacy furniture imports use explicit source-to-destination
registry records; their browser identities retain the GameCube IDs while native
records and saved bits use additive N64 destinations. The shared pipeline
validates that distinction for every source-table and selection consumer.
It updates actual native enable fields, resource CRCs, catalogue rows/counts, and
save profiles without new allocations. Empty selections reproduce the explicitly
pinned translation-only cartridge; all installed selections reproduce
the pinned complete integration cartridge. The private browser interface uses
generated records for the same choices, not a separate maintained item list.
These are experimental development profiles,
not complete donor coverage, playable-import certification, or served web options.
Fifty complete source holiday furniture gifts use independent choices and the
installed shared event providers without requiring diary imports. Source
selectors, guarded native handovers, inventory/collection, and saved trophy
records remain the initial acquisition path. Twelve source reorderable-list
members retain catalogue ordering after collection; no gift enters shop stock.
Ordinary conversation, acquisition/ordering, and physical save/restart remain
unverified. The source summer-exercise radio prize has ordinary admission with
its actual exercise-card dependency, retaining the complete installed controller,
room lifecycle, music, and indoor exercise. Card-only selection does not select
the radio. Initial acquisition remains the full source stamp/reward route,
without shop stock or catalogue ordering; ordinary gameplay/save verification
remains pending.
The shared draw-only scrolling category supplies backyard pool through its
verified donor event-item route, with complete layered graphics and the same
optional catalogue/save consumers. Well model remains inactive pending its
actual acquisition route; neither renderer preparation nor no-op callbacks
substitute ordinary shop stock for an unresolved source.
Shared positioned-loop/switch-fade callbacks connect Merlion and Manekin Pis
through the actual Gulliver route and fireplace through winter-camper trades.
All three retain donor non-orderability and full graphics/audio. Sprinkler uses
the shared native start-disabled placement rule with source C-stock acquisition
and catalogue reordering. These category implementations do not establish
ordinary gameplay or original-hardware acceptance.

### V4: preserved post-office account and source mail experiment

The new savings-account system is outside V3. Do not continue its account or
milestone controls to complete the import pipeline. Its dependent items should
remain unavailable until that acquisition exists. Mail and rewards fitting
existing systems are evaluated separately and are not automatically V4 work.
The following describes preserved experimental resources, not authorisation
to resume the savings-account feature.

The complete donor banking/Pelly frontend, source April talk controller, and
format-21 saved-town owner have a bounded combined native link. The separate
48-byte account record and enlarged save scratch retain checked reservations.
Actual linked menu/Pelly entries preserve original repayment and use the genuine
native wallet, pocket, text, and drawing APIs. The complete bank artwork uses
physical packet pointers without taking the native submenu's segment six.
Bank configuration has owned initialized storage, but no installed profile
control. ABI 387 installs this packet with banking disabled by default. Its
complete 245,824-byte shared startup transfer retains the existing 23-descriptor
loader, original reservation, guards, and every old physical copy. Repayment/Pelly
code and relocation pairs retain native directory order at explicit additive VROM
identities; both complete allocation readers and the retained menu chain grow
by their checked 64-byte allowances. The shared next-category reader retains them.

The April controller retains its eleven source NPC/message rows and all four
players' event-cache talk fields. Construction preflights native event allocation;
the bank borrows a distinct two-callback view of the complete source clip. Actual
April calendar/manager/actor consumers compile and have a complete native resource
plan for additive event 117/profile `F6`. Wisp 115 and Franklin 116 retain their
identities. Native cleanup includes 117, and all 75 existing manager rows and
relocations remain intact. Guarded lifecycle wrappers, saved-owner personal
deletion, and complete official postal dialogue are installed. Phyllis retains source
identity `D012`, independently of the postal draw-type field.

All 46 public saved-owner entries use the same linked format-21/account owner.
Fourteen official messages and four choices preserve all existing text and the
whole current Nook/Harvest/choice-reader receipts. Focused cartridge/resource
checks and five browser/offline profiles pass; native services remain doubled
in both-mode saved-owner checks. These results do not prove ordinary gameplay,
physical save/restart, or hardware behaviour.

Genuine successful-mail acknowledgement and scheduling, and independent mechanic/
reward controls remain unfinished. Assess their existing-system dependencies
separately from the new V4 savings-account feature. The source milestone does
not become lifetime earnings or random post-office stock. Format-21
saves migrate older supported records forward with empty accounts; format-20-or-
earlier readers cannot load format 21, even when banking is disabled. Preserve
separate builds/saves. See the [current source-mail checkpoint](../docs/checkpoints/V3_POST_OFFICE_REWARD_REVIEW.md).

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
Keep the deployed patcher and ordinary local preview on stable V2 until the user has tested V3 and
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
