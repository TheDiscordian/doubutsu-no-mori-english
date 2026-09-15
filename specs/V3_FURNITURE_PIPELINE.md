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
  Clamp, wrap, and mirror combinations are decoded by their actual bit fields;
  repeated axes require power-of-two texture dimensions. Unknown state fails.
- Static profiles with supported shape, collision, lighting, and rotation
  fields. Footprint follows **shape**, as in donor `aMR_GetFurnitureUnit`, not
  collision: shape 4 is 1×1, shape 3 is 2×1, and shape 5 is 2×2.
- Ordinary A/B/C, event, and lottery acquisition, existing scoring categories,
  and default catalogue framing. Names and prices come from actual donor tables.

Dynamic texture/palette pointers, animation rigs, custom callbacks, unsupported
contact/interaction flags, seating sounds, other acquisition routes, oversized
or different-format artwork, and special preview framing remain explicit review
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
items. The other seven reserved bytes remain zero. The builder populates masks
for **all** installed furniture, retaining existing non-orderable rewards and
the separate clothing-display route. Native gameplay IDs and saved formats do
not change. Profile selection still rejects absent dependencies.

## Verification policy

`tests/test_v3_furniture_pipeline.py` checks shared parser rules, source
relocations, independent complete texel/triangle comparisons, metadata/provenance,
current cartridge installation, retained data/code, and subset composition.
The catalogue mask reader has address/undefined-behaviour sanitizer checks.

`tools/v3_furniture_batch_smoke.py` and
`tests/scenarios/v3_furniture_batch.json` are reusable across future batches.
The manifest selects representatives by stock group, footprint, and model layers,
preferring larger assets. The check exercises actual native owner loading,
model DMA, item readers, placement, catalogue eligibility, acquisition, ownership,
state restoration, and guards. It does not create a new scenario per item.
GPU appearance, ordinary interactions, and save/restart require the gameplay pass;
memory-reader checks do not claim them. Retain passing unchanged evidence.

See [the implementation checkpoint](../docs/checkpoints/V3_FURNITURE_PIPELINE.md)
for actual outputs, counts, and verification results.
