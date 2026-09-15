# Automatic furniture pipeline checkpoint

## Current shared seating category

The current complete cartridge is ABI 86:
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
40 under its present complete category rules, all installed. The post-install
scan identifies no remaining supported,
uninstalled entries. This is **not** a whole-project completeness percentage.
The other 202 entries include already-installed special adapters and explicit
identity/unused cases as well as genuinely missing imports.

Continue through shared feature categories, not individual item queues:

1. Shared contact flags and callback families: 20 entries have the same `0010`
   interaction flag; 106 have custom callback tables. Inspect actual behaviour
   and dependencies before enabling a family; never discard callbacks to make
   an item fit the static category.
2. Acquisition categories, special preview framing, and graphics variants:
   extend reusable adapters for the inventory's explicit reasons. Some items
   need combined features; clearing one reason need not make the item complete.

No more bespoke furniture installers or item-by-item metadata definitions are
the default development path. The legacy scripts remain as reproducibility
records; new supported items flow through the shared pipeline.
