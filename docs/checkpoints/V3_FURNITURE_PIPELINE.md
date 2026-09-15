# Automatic furniture pipeline checkpoint

## Current material and catalogue-framing categories

The complete development cartridge is ABI 88:
`build/v3-furniture-material-preview-runtime-02/animal-forest-v3-asset-loader.z64`.
Shared discovery installs bug zapper `3234`, coffee machine `323C`, candy machine
`3254`, and steam roller `328C`, with 15,104 complete object bytes, 258 vertices,
and 153 triangles. The first two retain stock A, candy machine retains stock C,
and steam roller retains event acquisition and its two-cell footprint. All names
have official-source credits in the single provenance catalogue. Automatic
additions total twenty-three; the offline composer contains 85 installed
development options: 62 furniture, three shirts, and twenty villagers.

All four use the same unlit texture/primitive material command. Its two cycles
pass texture RGBA through, then multiply RGB by primitive colour while retaining
alpha. The symbolic native `gsDPSetCombineLERP` compiles to donor words
`FCFFFE60 FFFCF3F8`; complete compiled material/geometry checks pass. The coffee
machine's environment-lighting flag is also retained. There is no item-specific
graphics description or installer.

Catalogue framing is now source-indexed for all 62 installed furnishings. Byte
26 of the existing 32-byte item record stores the donor framing index plus one.
The complete 328-byte/41-entry table and its guards occupy
`80474A30..80474B9F`, with table data at `80474A40`. It fits after the placement
table and before accessory artwork, without increasing any permanent allocation.
The general native helper changes only model Y and scale after native
construction; clothing aliases keep their existing presentation. It replaces
the installed per-item Western, bike, and campfire overrides. The steam roller
and campfire both obtain the donor's mode 19 (`0.86`, `-3.0`) through records.
Disabled, absent, invalid-selector, and original-native cases retain their input.

The complete catalogue suffix is 3,408 bytes, and its 498 furniture rows retain
all 248 clothing rows. Conservative menu memory is 280,256 of 280,704 reserved
bytes. The import blob is 3,195,952 bytes, with 932,816 bytes before English
choices. Model-bank allocation and saved format 2 are unchanged. The required
saved profile is a superset of ABI 87. Saves using the four new items must not
be loaded in older builds or V2; ordinary cross-version reload is not newly
claimed. Both served patchers remain V2.

- ROM SHA-256: `5644a08760b63a396747adf2d5926340255667309152c7d9d0e4290263945319`.
- UPS SHA-256: `ed9c1c5b54e57d7414cc6b1f2b4dca39e9b5e284925222b999f54249e809c74e`.
- Build receipt SHA-256: `c8181c0ccb92625fb8d031317f8b83df5be29d9a09a5e5bddff64340105f5cfe`.
- Art receipt SHA-256: `e0e93177e8b011b6f73d571ce6e805317f4d13797adf03eefd2ee70ba4598a57`.
- Import blob SHA-256: `76032e58970f9e296b3d8054b09220662ef571a20339b345034ca9e8a172521a`.
- Preview table SHA-256: `fa6592f8af1ebb2ddb984e59b39649c36afeb85bdd4f9127dbcae26ba62a2a98`.
- Preview reservation SHA-256: `44d06f4df2fca8da04bb6c6a4ee48f131d9a2e1d22dce012027f077cb32b71bb`.

Thirty-four focused pipeline/composition checks pass against this candidate
before promoting its lock. They include the shared native combiner expression,
complete resource/geometry comparisons, all source-derived framing selectors,
guarded repeat-batch reuse, source credits, installed metadata, and selected/save
profile composition. The catalogue's host address/undefined-behaviour checks
cover the complete framing-table range and invalid boundaries. The fixture
preserves the distinct clothing-display stock route when enabling the full
catalogue wrapper. An initial build catches the old seating helper's reserved-
byte check; the corrected check recognises byte 26 as framing metadata while
retaining zero checks on bytes 27–31. That partial build has no promoted ROM.

The first silent native run passes 146 records with 124 assertions:
`build/v3-furniture-material-preview-native-01/results.json`, SHA-256
`3ae031b8643fbcd3a029b4387e2a7e5fde499f4b1157e4d687878e159a20b777`.
The shared representative selector covers all four new records because their
stock, footprint, preview, and lighting categories differ. Actual owner loads,
complete model DMA, source framing with every other preview field unchanged,
disabled/invalid/native framing fallbacks, names, prices, rotations, stock,
acquisition, ownership, restoration, and guards pass. The emulator exits cleanly;
no native retry is needed. This is not proof of full catalogue initialization,
GPU appearance, ordinary gameplay/save-restart, or original-hardware execution.

The post-scan in `build/v3-furniture-material-preview-post-scan-01/inventory.json`
has 49 supported entries, all installed, and 193 entries needing review. That
inventory includes aliases and unused records and is not a remaining-content
percentage. Continue shared behaviour/format/acquisition categories.

## Shared identity-indexed model and palette conversion

The converter handles the complete nine-entry flower selector through one
`indexed-static-model-palette` rule. No item list, separate graphics converter,
installer, runtime helper, or native test scenario is added. The source's fixed
actor identity selects two opaque models and a palette. Both models retain
their full material/geometry commands, and their segment-eight palette loads
become direct loads of the selected native palette.

The checked donor has `fNFL_dw` at `.text:2D0768`, 192 bytes, SHA-256
`612998bdab7cb941114e08d66db7100ded74894f8c1ccfdbdffe4bb9fbb44917`.
Its four code relocations bind the save/restore helpers and the complete
`fNFL_model_data` table at `.data:092BE0`, 108 bytes. The actual instructions
subtract runtime index 1246 and multiply by a twelve-byte row stride. All three
lifecycle callbacks are four-byte returns; the DMA slot is null. The verifier
checks those facts and dependencies, not merely function names. The donor room
renderer's `aMR_DrawRegistModel` uses the same current matrix and opaque0/opaque1
order; the special callback adds only the constant palette selection. Catalogue
rendering also retains that model order. Native execution of these new assets
is not yet claimed.

One command prepares all nine variants:

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette \
  --output build/v3-furniture-indexed-palette-art-01
```

The output contains 19,152 object bytes, 555 vertices, and 288 triangles across
all three pansies, three cosmos, and three tulips (`3378..3398`). Each object has
its actual official donor name/source index and its selected palette. The
complete prepared receipt SHA-256 is
`6e173ac1c9c1889389779d93b63fd7ac6589d5644bd6d0afa9387dfe72711e83`;
the inventory SHA-256 is
`20df1500755bc29f67ffcb923f84a34244430e79a758bc718eb6e89b4e61f522`.
Individual object/resource hashes are in that receipt.

All nine remain **prepared, not installed**. The donor's
`ftr_listEventPresentChumon` contains these nine flowers, two tree models, and
weed model. `mCL_furniture_init` and `mMpswd_check_present_user` treat this category as
orderable/password-eligible, but that does not establish a working native initial
acquisition route. The N64 has no matching stock-list slot. Do not put the objects
in ordinary shop stock or claim acquisition is complete. Shared acquisition and
catalogue handling must cover the twelve source records together.

The actual initial acquisition comes from `mSC_trophy_item`, not a random shop
list. Its 244-byte donor function at `.text:07C31C` has SHA-256
`48321dd6e22de9f11751b89f9557c5be837f142f70b36bbe5cbd8ff933ea8234`.
The 56-byte `soncho_item_table$582` at `.data:010714` has SHA-256
`2bf4a655de09672b8c202cad690e6595cae1859656b5f379e9b9347822ea2fd9`.

| Donor event | Source reward rule |
| --- | --- |
| Founder's Day, index 1 | Weed model `3080` |
| Cherry Blossom Festival, index 7 | Pink tree model `307C` |
| Nature Day, index 9 | Tree model `3078` |
| Groundhog Day, index 13 | Uniform random runtime index `1246 + RANDOM(9)` |

The gift list at `.data:698630` is 26 bytes including its terminator, SHA-256
`07391eb07d67a5f92dfcd3300ac0586bc3908bb470e8ff2257cd7e39e1a8040f`.
`aES2_talk_before_give` checks pocket space; `aES2_talk_give` performs the normal
handover, inserts the actual item, and records the event trophy. Their complete
function hashes are respectively
`a3129746c1e60b877ecd74ae82f6861db8ef00509f0f15bfebe097324683bacc`
and `adb99cc52df75acb980d5f865c3c20f9778e223011b86d6f0b00d59aeec0d699`.
This requires the donor Tortimer event actor, English conversations, calendar
integration, selected-reward eligibility, and reviewed per-player trophy/calendar
persistence; the N64 actor/profile inventory has no corresponding Tortimer
implementation. Donor private-data offsets are not native saved fields. Implement
the shared event route without turning these rewards into ordinary stock, and
continue unrelated conversion categories while that larger dependency is open.

Thirty-two focused pipeline/composition checks pass with
`V3_FURNITURE_PREPARED_ART=build/v3-furniture-indexed-palette-art-01`. The reused
asset checks compare complete texels, vertices, triangles, materials, and palette
load targets. New checks cover every actual selector row, independent relocation
resolution, unknown/changed callback rejection, extra DMA effects, bad indices,
ambiguous palette bindings, and refusal to install prepared-only output. No
native emulator run is repeated: ABI 87, the ROM, import lock, saves, and both
served V2 patchers are unchanged. The 81 installed options do not include these
nine prepared objects.

Callback inspection also identifies useful next shared categories: fifteen
station models with one animated clock/skeleton implementation; eight building
models using palette-fade callbacks; tool, fan, and pinwheel display selectors;
and move-only sound callbacks. These are category candidates, not approved static
substitutions. In particular, station clock hands and animated parts must remain.

## Collision and placement categories

The collision/placement cartridge is ABI 87:
`build/v3-furniture-placement-runtime-01/animal-forest-v3-asset-loader.z64`.
The same importer installs grass model `30E8`, dirt model `30F0`, and boxing
mat `3348`, retaining all 2,768 object bytes, 44 vertices, 24 triangles, textures,
and the donor's `0010` no-collision flag. Official name credits are in the single
provenance catalogue. Automatic additions total nineteen; the offline composer
contains 81 installed options: 58 furniture, three shirts, and twenty villagers.

Inspection identifies five native readers still indexing the original 947-entry
placement-layer table with imported indices. This can read unrelated data and
lose surface behaviour. The shared fix preserves the original prefix and adds
source-derived rows for every installed furnishing and all three clothing display
aliases. Four imported surfaces (teacher's desk, orange box, chess table, and
ringside table) and five surface-placeable objects (garden gnome, cow skull,
lantern, Luigi trophy, and Mario trophy) now have explicit correct categories.
Other imported furniture has category zero. No item-specific runtime branch is
added. The complete native collision-registration routine is unchanged except
for its corrected table address, preserving its ordinary-room/shop distinction.

The 2,051-entry table and guards occupy `804741F0..80474A1F` in the unused
registry-to-artwork gap. The five actual HI/LO pairs are at
`8093825C/80938268`, `80943878/8094387C`, `80943978/8094397C`,
`80943A34/80943A40`, and `809462C8/809462D4`. Ten obsolete relocations are
removed. All other native owner bytes and accessory records/artwork remain.
There is no added executable code, resident allocation, or saved-format growth.

- ROM SHA-256: `004a1173c51cdea009c3a5e291067469675d40809002bf8fd41d99f28f671c1d`.
- UPS SHA-256: `df73ad1e2f7c8f010bd6016356a2d03b333d4295de4bb8d04c44cc286906c999`.
- Receipt SHA-256: `64805f9215d264303347fc40842f5fa6b15d2c549453f3e6c5b7ac654b1e85ec`.
- Import-resource SHA-256: `c328b130c6bb338de7582f24ceb6f3b741769427477e5c237a7a9b5c53665a58`.
- Placement-table SHA-256: `9f6d51793f058d2b8ebe8952a4369fd4a7b5d48eb19c9998333b885aac89ef01`.
- Native owner SHA-256: `ca540a6f48fa15fb8bfad4d36abf77bb3d318799732d965f278063207f64b74a`.
- Relocation SHA-256: `c97bc9e48c97a6830145218f5fcdcaa664a7611167b2f013bc93d75f4e493bc5`.

The blob contains 3,116,400 bytes, with 1,012,368 bytes remaining before English
choices. The catalogue has 494 furniture rows and 248 clothing rows; conservative
menu memory remains 280,384 of 280,704 reserved bytes. All 28 focused pipeline/
composition tests pass. They include every converted texel/vertex/triangle,
unknown interaction/placement rejection, source-derived table entries, all five
retargeted references, complete relocation comparisons at two load addresses,
unrelated-owner retention, repeat-batch reuse, and save-profile composition.
The first silent native run passes 125 records and 107 assertions, including
the complete placement table/guards, native owner loading/relocation, actual
no-collision registration for all three new objects, complete model DMA,
one-/two-cell rotated footprints, names, prices, stock, catalogue eligibility,
acquisition, ownership, restored state, and guards. The existing four sound
routes also pass. The emulator exits cleanly; no native setup retry is needed.
Results are in `build/v3-furniture-placement-native-01/results.json`, SHA-256
`5757a4b7580348303195455ae9c1b5b17e425a3bafa18cfc19c549673a7e733a`.

Ordinary room appearance, table use, walking across the collision-less objects,
and save/restart remain unverified. Saved format 2 is unchanged and the profile
extends ABI 86; no ordinary cross-version reload is newly claimed. Saves using
the three new objects must not be loaded in older builds or V2. Neither served
patcher changes.

## Shared seating category

The seating-category cartridge is ABI 86:
`build/v3-furniture-seats-runtime-02/animal-forest-v3-asset-loader.z64`.
The automatic pipeline adds lawn chair `324C` and teacher's chair `3288`
without an item definition, dedicated installer, or separate native scenario.
Their 7,872 bytes retain all 163 vertices and 81 triangles. This brings the
automatic additions to sixteen and the offline composer to 78 installed options
(55 furniture, three shirts, and twenty villagers).

The category extension also supplies the donor's correct soft-chair sounds for
lawn chair and hard-chair sounds for teacher's chair, lefty desk, and righty desk.
Byte 25 of each existing item record stores its source-derived category. All
installed furniture is populated from the actual donor table, including entries
with no action sound. No per-item runtime branch or separate audio import is
needed. Full sound programs, timing, complete instruments, envelopes, samples,
loops, and predictors match native audio; matching sound numbers alone are not
the verification. Original native items retain their original reader body.

The helper is 208 bytes at `80483D00`, before the fire vtables at `80483FC0`.
The installer verifies the existing fire code and empty intervening bytes;
linker limits also prevent shared item/tent/fire/behaviour overlap. The helper
uses a bounded 32-byte stack frame and no new permanent RAM or audio resources.
The catalogue contains 491 furniture rows and 248 clothing rows. The resource is
3,049,104 bytes, with 1,079,664 bytes remaining before the English-choice region.

- ROM SHA-256: `e6f334027c352039fededafe8672d7ff480b5234bad914646b4beeffad00d1ab`.
- UPS SHA-256: `b20ac5cf1f0bc6452a3ec38b76d15ab76d5e215e9112fd81d0c912af42ce6d40`.
- Receipt SHA-256: `b3f9a540d3426a87dad66cc7eec0732fef38283b72de4fc312b87fd75eee4b54`.
- Import-resource SHA-256: `2963fa39c0886ac784b3b6ed842e8dc6a8c88cef65c7b4909868a7debbeefff5`.
- Native result: `build/v3-furniture-seats-native-01/results.json`, SHA-256
  `33895a6070a9e352a7fc663f22c4fc5b1e45d84eaed84919005199c897733f4c`.

All 26 focused pipeline/composition checks pass. The shared sound implementation
passes address/undefined-behaviour sanitizers for original delegation, complete
import index bounds, modes, categories, metadata identity, and disabled records.
The first silent native run passes 88 records and 73 assertions: complete helper
loading, original fallbacks, both modes for all four imported sound routes,
disabled-profile rejection, invalid indices/modes, complete chair model DMA,
names, prices, stock, catalogue eligibility, acquisition, ownership, restoration,
and guards. No audio is played through the user's speakers/headphones.

The initial installer attempt stops at a missing shared compiler-entry mapping;
the mapping is added and the completed build passes. There is no native setup
retry. Ordinary sitting, audible playback, GPU appearance, transactions, and
save/restart are not established by these component checks. Saved format 2 is
unchanged; the new profile is a superset of ABI 85, but ordinary cross-version
reload is not newly tested. Saves containing the new chairs must not be loaded
in an older cartridge or V2. Neither served patcher changes.

## Initial automatic batch

Source revision `7149f9c` discovers and installs fourteen new items in one
batch, without an item-specific converter definition, stock/catalogue switch,
installer, or test scenario. The complete command is:

```sh
python3 tools/v3_furniture_pipeline.py import \
  --base-lock tests/fixtures/v3-furniture-pipeline-base.json \
  --output build/furniture-reproduction
```

The recorded run used the same pinned input through the current-build lock
before that lock was promoted. The final output is
`build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64`, ABI 85.
The one-command output in `build/v3-auto-furniture-02/cartridge/` has the same
complete ROM and patch hashes. The final rebuild adds reusable predecessor/art
locations to the receipt; it does not change any cartridge bytes or require
another native run. The folder name identifies this implementation batch,
not a finished V3 release.

- ROM SHA-256: `571e849108cf36983c7129a38d08bfc3b47dd71db5c4347cfe16b7425b1ed35c`.
- UPS SHA-256: `d9283d2908b779694ee584889d5f1559523159bbc3f8ae4512d368bf11d664f5`.
- Final build receipt SHA-256: `9f1df24e3e98f4972afc7c38720f91947afe6417082a79d13bdeee3959b80166`.
- Appended import resource: 2,976,720 bytes, ending at VROM `024D6BD0`,
  leaving 1,152,048 bytes before the reserved English-choice resource.
- Models: 50,064 bytes, 1,038 vertices, and 570 triangles, with complete textures
  and palettes. No donor artwork is truncated or replaced with a placeholder.
- Catalogue: 489 furniture rows and 248 clothing rows. The compiled suffix is
  3,424 bytes; conservative menu memory is 280,384 of 280,704 reserved bytes.
- No additional permanent RAM, model-bank allocation, or saved-format growth.

Imported records: track model `30EC`, train car model `30F4`, orange box `30F8`,
merge sign `31EC`, radiator `3248`, chess table `3250`, cement mixer `325C`,
jackhammer `3260`, potbelly stove `326C`, flip-top desk `3278`, Luigi trophy
`32C8`, Mario trophy `32CC`, boxing barricade `3338`, and ringside table `334C`.
Names have generated official-source entries in `translations/provenance.json`.

The offline composer resolves 76 installed development options. The concrete
subset `build/v3-optional-auto-furniture-01/` selects radiator, Mario trophy,
and ringside table without other new furniture, ROM SHA-256
`a973cee3a9e2f24adca32dd95e766c6a94e5d965da52805a8562aff558ab6453`.
Empty selection reproduces V2; all selection reproduces the complete cartridge.
Neither served patcher changes, and this is not a public-release handoff.

### Initial batch verification

Seven shared format/donor tests, five current-cartridge tests, and twelve
composition tests pass: **24 focused tests**. Checks cover every new texel,
vertex, and triangle, actual source relocations, retained material commands,
complete installed assets/profiles, official names, stock membership, scoring,
catalogue order, ROM checksums, full/empty/subset selection, and saved-profile
requirements. The shared catalogue reader passes address/undefined-behaviour
sanitizers across its bounded index/list/category/rotation cases.

The initial native attempt stops before emulation because `Xvfb` is not on PATH.
The one corrected retry explicitly uses the existing executable:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-auto-furniture-final-01/animal-forest-v3-asset-loader.z64 \
  --output build/furniture-native-reproduction \
  --scenario tests/scenarios/v3_furniture_batch.json \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --seconds 180 --expansion-pak --no-initial-screenshot
```

`build/v3-auto-furniture-native-02/results.json` passes **148 records and 133
assertions**, SHA-256
`d97bcd43bf3a6665c0e63f1d87a3e9cb99b7500d5c394acb6887e40f286e44f7`.
The manifest chooses train car model, Luigi trophy, Mario trophy, flip-top desk,
jackhammer, and ringside table to cover A/B/C, event, lottery, one-/two-cell,
and model-layer categories. Actual owner loading/relocation, names, prices,
rotated footprints, complete upper-memory model DMA and untouched tails, bank
assignment, stock membership, catalogue eligibility/rejection, acquisition,
saved ownership, restored state, and guards pass. The emulator exits cleanly.
No existing save is used and no test FlashRAM write is requested.

Ordinary room appearance, GPU rendering of these new models, transactions,
interactions, and save/restart remain unverified. The preceding full profile is
a subset of this profile; the codec accepts equal/superset requirements, but
ordinary cross-version reload is not newly tested. Do not load saves using the
new items in an older build or V2.

## Category queue

The donor worksheet contains 242 canonical 3xxx entries. This converter supports
43 under its present complete category rules, all installed. The post-install
scan identifies no remaining supported,
uninstalled entries. This is **not** a whole-project completeness percentage.
The other 199 entries include already-installed special adapters and explicit
identity/unused cases as well as genuinely missing imports.

Continue through shared feature categories, not individual item queues:

1. Shared callback families: 102 uninstalled entries stop on custom callback
   tables. Classify the actual callback/dependency patterns and implement shared
   behaviour adapters; never discard callbacks to fit the static category.
2. The supported `0010` flag exposes further dependencies: sixteen diary display
   models need diary identity/gameplay/acquisition; weed model needs the shared
   `ftr_listEventPresentChumon` reward route. Neither is a completed static import.
3. Acquisition categories, special preview framing, and graphics variants:
   extend reusable adapters for the inventory's explicit reasons. Some items
   need combined features; clearing one reason need not make the item complete.

No more bespoke furniture installers or item-by-item metadata definitions are
the default development path. The legacy scripts remain as reproducibility
records; new supported items flow through the shared pipeline.
