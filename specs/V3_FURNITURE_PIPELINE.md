# Automatic furniture import pipeline

## Workflow

New furniture uses `tools/v3_furniture_pipeline.py`, not a new Python item list,
family installer, catalogue switch, or dedicated native scenario. Extend shared
format/behaviour rules when the donor requires an unsupported feature. Item names
and themes do not determine which graphics converter runs.

The pipeline reads the checked GAFE01-r0 REL, symbol map, and identity worksheet.
`config/v3-import-build.json` pins the current complete development cartridge and
receipt. It is also the offline composer's source selection. Changing this file
does not change either web patcher. Build output includes a proposed next lock;
promote that lock after checking the batch. Never promote a partial/selected-only
cartridge as the full development base.
The output also retains `base-lock.json` and the conversion-directory reference,
so the next batch and its shared tests do not need another hard-coded predecessor.

```sh
python3 tools/v3_furniture_pipeline.py scan --output build/furniture-scan/inventory.json
python3 tools/v3_furniture_pipeline.py import --output build/furniture-import
```

`import` discovers, converts, and installs every supported, uninstalled item in
one invocation. `--select 3248 --select 334C` narrows the batch by canonical donor
ID. `convert` runs the same discovery/conversion without installation. The
standalone installer accepts an existing conversion through `--art`; it performs
the same source and base checks. Use fresh ignored output paths. No ROM, save,
source artwork, served website, or existing generated build is overwritten.

`--category` selects a discovered shared category without maintaining an item
list. `convert --assets-only` prepares complete artwork while retaining missing
metadata/gameplay/acquisition reasons. It produces a distinct **prepared-assets**
format that the installer rejects. This mode cannot be used with `import`.
The ordinary `convert` and `import` commands still require every eligibility
check. Inventory `asset_ready` describes conversion only; `status: supported`
also requires the supported metadata and acquisition route. Neither field is a
claim of completed playtesting.

```sh
python3 tools/v3_furniture_pipeline.py convert --assets-only \
  --category indexed-static-model-palette --output build/indexed-palette-assets
```

Each item has one generated descriptor containing profile/model dependencies,
textures, palettes, vertices, native display-list locations, official name,
price, footprint, acquisition list, catalogue position, scoring, source hashes,
and installed resource locations. The installer and tests consume those records.
They do not restate the items in another maintained Python list.

New official name entries are generated as `provenance.patch` if missing from
`translations/provenance.json`. Apply the generated patch through `apply_patch`
and build with the updated catalogue before promoting a build. Existing human
attribution is never overwritten; conflicting attribution stops the build for
review. The patch is a proposed edit to the single catalogue, not another text
source catalogue. The receipt states whether attribution is complete.

## Discovery and supported categories

Both actual donor `furniture_quality` tables must identify the same complete
profile. The REL relocation stream and symbol spans are indexed once and reused
across the scan. Dependencies come from actual profile/model pointers, including
interior vertex-array references. Missing, ambiguous, external, truncated, or
unaccounted dependencies are rejected.

The shared static-CI4 category supports:

- All four native opaque/translucent model slots, complete 16-colour palettes,
  one complete vertex array, and multiple textures/palettes.
- Complete TMEM-sized CI4 textures, untiled from GX blocks without resizing.
- Native vertex conversion preserving position, UVs, and colours, clearing only
  donor flag fields; complete triangle conversion and bounded vertex loads.
- Source primitive colours and the supported material/geometry commands.
  The unlit texture/primitive category preserves texture RGBA in cycle one,
  multiplies RGB by primitive colour in cycle two, and preserves texture alpha.
  Its symbolic native combiner compiles to the exact checked donor command;
  no theme/item switch or extra texture dependency is required.
  Clamp, wrap, and mirror combinations are decoded by their actual bit fields;
  repeated axes require power-of-two texture dimensions. Unknown state fails.
- Static profiles with supported shape, collision, lighting, and rotation
  fields. Footprint follows **shape**, as in donor `aMR_GetFurnitureUnit`, not
  collision: shape 4 is 1×1, shape 3 is 2×1, and shape 5 is 2×2.
- Ordinary A/B/C, event, and lottery acquisition, existing scoring categories,
  and source-indexed catalogue framing. Names and prices come from actual donor tables.
- Soft- and hard-chair action sounds, selected from the donor's actual category
  table. Matching complete sound programs, timing, instruments, and samples use
  the existing native audio; no replacement sample or new audio allocation is
  needed. The shared reader also covers previously installed furniture.
- Native `NO_COLLISION` interaction flag `0010`, preserved in the complete
  profile. The native registration/placement behaviour and shop exceptions
  remain; this is not a substitute for a diary's separate gameplay system.
- Source-derived placement layers: ordinary floor items, surfaces that hold
  other items, and objects that may be placed on those surfaces.
- Single-bed contact action `08`. Complete models and profile scalars feed the
  existing native bed positioning, contact, entry, and exit routines through
  the expanded profile table. No new bed callback, per-item behaviour switch,
  or animation replacement is needed. The build checks the current room engine
  and its four bed-profile bindings before accepting this category. Separate
  island/holiday acquisition requirements still prevent installation; bed
  support never substitutes ordinary shop stock for the actual donor route.
- Constant identity-indexed model/palette selection. A reviewed complete draw
  implementation selects two opaque models and one sixteen-colour palette from
  a complete relocated table. The converter derives the index base, row stride,
  model pointers, and palette from the donor, not per-item definitions. The
  selected palette replaces the fixed segment-eight reference in both models.
  All create/move/destroy callbacks must be complete no-ops, DMA must be absent,
  and every draw-code relocation must match the reviewed dependency pattern.
  Changed code, additional effects, incomplete tables, ambiguous bindings, and
  out-of-range indices fail. The descriptor retains function hashes, code/data
  relocations, the selector row, and palette binding. This removes only a
  constant draw selector, never animation or gameplay behaviour.

Dynamic texture/palette pointers, animation rigs, other custom callbacks, unsupported
contact/interaction flags, other action sounds or acquisition routes, oversized
or different-format artwork, and framing outside the checked source table remain explicit review
categories. Unsupported does not mean unused or unimportant. A successfully
converted object is not automatically evidence of complete gameplay.

## Shared installation

`tools/v3_furniture_install.py` binds the complete base ROM/report and source
data, regenerates the metadata/dependency description, and checks the converted
assets. It installs full profiles and item records, names/prices/footprints,
stock, catalogue entries, HRA/feng-shui rows, and selected-profile bits together.
Missing native scoring-series definitions require a category adapter. Existing
documented theme adapters retain their unavailable matching-surface policy.

Canonical furniture identity version 2 is independent of conversion order,
checkbox selection, and resource placement:

```text
saved item ID = canonical donor 3xxx ID
runtime index = 1024 + (saved item ID - 0x3000) / 4
```

Existing native items, old explicit reservations, and display aliases remain.
The checked build manifest records each new object's VROM; it is not a saved
identity. Object storage is appended at 16-byte alignment with complete physical
and virtual overlap checks, the 9,216-byte model-bank limit, ROM boundary checks,
CRC updates, and full patch reconstruction. No new DMA-directory entry is needed.

Stock and catalogue builders accept verified records without family switches.
Catalogue eligibility uses byte 24 of each existing 32-byte sparse item record:
`7` for ordinary A/B/C, `8` for event, `32` for lottery, and `0` for non-orderable
items. Byte 25 stores the donor action-sound category: `0` for none, `1` for
soft chairs, and `2` for hard chairs. Byte 26 holds the donor catalogue framing
index plus one; zero means no furniture-framing override. The other five
reserved bytes remain zero.
The builder populates masks for **all** installed furniture, retaining existing
non-orderable rewards and
the separate clothing-display route. Native gameplay IDs and saved formats do
not change. Profile selection still rejects absent dependencies.

`tools/v3_furniture_behaviours.py` installs the shared sound reader at `80483D00`
within the existing package. Its reservation ends at `80483FC0`, before the fire
vtables. The original sound-reader entry at `800BED5C` delegates native indices
to its unchanged body; imported indices require complete, enabled item/profile
records and a supported mode/category. Invalid imported requests return no sound.
The build verifies complete source audio, current audio resources, original
function bytes, existing fire code, and unclaimed helper padding. Linker limits
separate the shared item, tent, fire, and behaviour code reservations.

`tools/v3_furniture_placement.py` provides a complete 2,051-entry placement-layer
table at `80474200`. Native entries 0–946 remain unchanged; imported furniture
uses its canonical donor entry, and clothing display aliases use their verified
mannequin source. Uninstalled slots are zero. The immutable table and its two
guards occupy `804741F0..80474A1F`, between the twenty accessory records ending
at `80474140` and artwork starting at `80475000`. Nothing is taken from a live
object or an unselected future item slot; no resident reservation grows.

All five native table references are redirected together. The builder resolves
the actual relocation pairs, rejects shared unrelated high halves, removes
exactly ten obsolete relocations, and leaves all other owner bytes intact.
The complete native collision-registration function is checked against the
original after accounting for its changed table address. Future batches update
the same table from their records, with the installed reservation and bindings
verified first. Neither the existing item records nor saved formats grow.

The shared preview builder in `tools/v3_catalogue.py` installs the complete
41-entry donor framing table at `80474A40`. Its table, padding, and two guards
occupy `80474A30..80474B9F`, after the placement table and before accessory artwork
at `80475000`. All installed furnishings use source-derived selectors; display
aliases retain their separate native presentation. New batches reuse the same
table and reject changed prior selectors or occupied reservations.

`af_v3_catalogue_frame` keeps ordinary native construction and changes only scale
and model Y for an enabled imported furniture record with a bounded selector.
It replaces the installed item-specific Western/camping/fire preview cases.
Native items, missing/disabled records, and invalid selectors are unchanged.
The native catalogue still uses mode zero during construction, then receives
the actual source floats; donor mode numbers are never mistaken for N64 indices.
No item-record, saved-format, or permanent allocation grows.

## Verification policy

`tests/test_v3_furniture_pipeline.py` checks shared parser rules, source
relocations, independent complete texel/triangle comparisons, metadata/provenance,
current cartridge installation, retained data/code, and subset composition.
The catalogue mask and seating-sound readers have address/undefined-behaviour
sanitizer checks.

`tools/v3_furniture_batch_smoke.py` and
`tests/scenarios/v3_furniture_batch.json` are reusable across future batches.
The manifest selects representatives by stock group, footprint, model layers,
action sound, placement/interaction flags, contact behaviour, preview mode, and lighting category,
preferring larger assets. The check exercises actual
native owner loading,
model DMA, item readers, placement, catalogue eligibility, acquisition, ownership,
state restoration, and guards. The sound check executes the actual native entry,
including original fallbacks, imported modes, disabled profiles, and invalid
indices. It checks returned sound IDs without playing audio through hardware.
Placement checks cover the complete resident table/guards, all five bindings
after relocation, and the actual native no-collision registration routine.
It does not create a new scenario per item.
Framing checks compare every preview field after the actual native helper runs,
including source floats, unchanged surrounding fields, disabled imports, invalid
selectors, native fallbacks, and the complete resident table/guards. Calling this
helper does not establish complete catalogue construction or GPU appearance.
The bed category exercises the actual native head-direction and both side-position
functions with a representative imported profile in all four rotations, checks
inactive-bed rejection, and preserves the complete temporary actor. This does
not establish an ordinary player climbing onto or leaving the bed.
GPU appearance, ordinary interactions, and save/restart require the gameplay pass;
memory-reader checks do not claim them. Retain passing unchanged evidence.

Set `V3_FURNITURE_PREPARED_ART` to a prepared-asset output directory to run the
same complete texture/vertex/triangle/material checks on that batch. The shared
test also checks source identities, retained pending reasons, and refusal by the
installer. No new test scenario is needed for another prepared category. A
converter-only change does not call for another native run of an unchanged ROM.

See [the implementation checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md)
for actual outputs, counts, and verification results.
