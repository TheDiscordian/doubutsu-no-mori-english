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
web patcher to V3 requires the user's testing and subsequent explicit approval.
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
starting shirt/defaults and both pilots' personality lookup. Punchy's actual
cherry-shirt import, houses, selection, secondary ID-bounded readers, and
ordinary gameplay/save integration remain pending.

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
verification. Remaining external consumers and the ordinary item lifecycle are required;
these are not playable imports.
Punchy's speed bag needs its actual animation/interaction adapter.

Then batch imports by shared conversion and behaviour needs. Interactive
furniture, music, tools, living creatures, and other mechanics need their actual
behaviour, not a generic decorative placeholder labelled as complete. Missing
engine features stay explicit work rather than silently dropped scope.

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
storage is assumed free. The web patcher does not upload or edit saves.

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
Keep public deployment on stable V2 until a verified V3 handoff is ready.

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
