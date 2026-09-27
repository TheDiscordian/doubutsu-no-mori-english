# V3 creature parents and room displays

## Connected category

`tools/v3_creature_items.py` connects the carried identity, official name,
price word, item category, room placement, complete room profile, and pickup
identity for all seventeen additive creature records. It consumes the existing
shared prepared graphics; it has no per-species model definitions or installers.
The ordinary `creature-profile-assets` import category schedules this dependency
after embedded motion and creature audio. Partial source requests still install
the shared category; they do not select additional imports.

Native fish `2300..231F` and insects `2D00..2D1F` remain untouched. New carried
IDs are `2320..2328` and `2D20..2D27`. The donor's brook trout `2301` maps to
`2328`; native herabuna remains `2301`, with its existing `1C2C` room display.
The append-only parent registry is independent of selection order. Display
destinations remain the existing `3C98..3CD8` reservations.

Names come directly from the complete donor `itemName_fish` and
`itemName_insect` resources, with their existing entries in the single
`translations/provenance.json` catalogue. Price words come from the complete
sentinel-bounded donor price tables. These are the engine's price words, not
a second hard-coded sale-price list. Source placement/pickup functions establish
each parent relationship. Whole native conversion functions and the original
32-entry item-category tables are checked before hooks change.

## Native readers and room profiles

Five outer entry hooks connect names, item categories, prices, placement, and
pickup. Existing surface, equipment, clothing, and native readers remain the
predecessors. Both carried and displayed forms use the parent's name and price.
Placement resolves the carried ID to its room form; pickup handles all four
rotations and restores the carried ID. Native herabuna never enters this path.
Unknown extended fish/insect IDs and unavailable imported displays return zero
without indexing the native 32-entry tables.

Sixteen complete embedded profiles reuse installed rig resources and callbacks.
The static ant installs all three converted native drawing layers. Source scalar
fields and interactions are preserved, including full-height tanks/cages and
the existing creature audio/motion integration. No simplified replacement model
or independent furniture option is created.

Each profile is installed inactive in its canonical sparse slot. Metadata keeps
the parent relationship. The reader additionally requires readiness and the
selected native profile. Readiness, profile activation, and selection remain off
until carried models/icons, catching/releasing, collection/profile persistence,
and spawn readers are complete. Prepared room support is not a playable species.

## Memory and startup

The immutable 3,840-byte module occupies `804FF100..804FFFFF`, after the console
session reservation ending at `804FF020`, and before model banks at `80500000`.
Existing recorded allocations are checked for overlap. Code has 2,048 bytes;
the 492-byte table starts at `804FF900`. Its header is `AFCI`, version one,
count seventeen, and stride 28. Each row is:

| Offset | Field |
| --- | --- |
| 0 | Carried item, u16 |
| 2 | Display item, u16 |
| 4 | Source price word, u16 |
| 6 | Native category, u8: fish 8, insect 18 |
| 7 | Source species index, u8 |
| 8 | Readiness, u32; zero while gameplay is incomplete |
| 12 | Complete space-padded ASCII name, 16 bytes |

The final sixteen packet bytes contain four `AF435249` guard words. Startup
loads and checks the full packet before the native initialization chain. All
eight shared packet loads use the same DMA/checksum/cache-flush function. A
failed DMA or checksum stops initialization before executing unchecked code.
The bootstrap stays inside its existing 688-byte reservation. No saved layout,
profile bits, or actor sizes change.

## Verification and remaining work

`tests/test_v3_creature_items.py` checks source identities, complete installed
profiles/resources, five hook targets, preservation of the native conversion
bodies, UPS reconstruction, retained saves, and optional all/empty composition.
Sanitized C checks exercise names, prices, categories, placement/pickup with
rotations, readiness/selection rejection, output bounds, native fallbacks, and
the eight-packet startup chain including DMA/checksum failures.

Native execution of this connected path and original hardware remain unverified.
The preceding scheduler test's unexplained debugger disconnect remains open;
host checks do not classify it. The active queue continues with carried models,
icons, catching/releasing, collection/profile persistence, and spawn readers as
one connected creature path, retaining the completed room and sound work.

## Field and carried graphics

`v3_furniture_pipeline.py convert --representation creatures --assets-only`
prepares the complete seventeen-species field-frame category through the common
resource parser, material conversion, and one batch compiler invocation.
`tools/v3_creature_field.py` follows the donor's actual model-pointer arrays;
it does not define models by species name. All three fish consumers must agree
on their complete frames. Two-, four-, and six-entry insect frame arrays retain
their repeated poses and ordering. The result contains 59 frame references to
43 distinct models, 25,504 bytes, with no independent creature-display choices.

The common converter supports a different complete vertex array per model in
one object. Each model still requires exactly one bounded vertex array; arbitrary
cross-array loads remain unsupported. Textures and palettes shared by frames
are stored once. The insect colour expression preserves texture alpha multiplied
by environment alpha, primitive colour, and second-cycle shading. This keeps
the drawing caller's fading controls rather than making the insects opaque.

The prepared category retains both independently sourced fish animation selectors,
both complete frame sequences, height corrections, and insect behaviour indices.
Field and release selectors are not interchangeable: jellyfish and several sea
fish use different selectors. The largest converted fish is 2,192 bytes, within
the native 2,560-byte fish buffer; every added insect fits its 3,072-byte buffer.
These sizes describe complete converted objects, not estimates from donor size.
The prepared assets are not installed runtime readers or playable species.

### Native integration constraints

- Native fish actor indices `0..31` are ordinary fish, `32..34` are rubbish,
  and `35` selects the coastal salmon path. New carried IDs `2320..2328` must
  not become those existing actor indices. Preserve the original actor slots;
  map added fish to separate actor indices at capture and release boundaries.
  The prepared `native_index` field describes the carried-item index only.
- The field fish owner is VROM `922A10`, relocation `924590`, RAM `80A5AF70`;
  its start/end/model arrays are `80A5C568`, `80A5C5F8`, and `80A5C82C` (36
  entries), with animation selectors at `80A5C984` and height at `80A5CA14`.
  The fish graphics bank is VROM `1871000`, 61,344 bytes. The native loader
  skips each object's eight-byte header and subtracts its bank offset when
  publishing segment six. Converted lists need that same address convention.
- The release owner is VROM `93A920`, relocation `93BBC0`, RAM `80A7A680`;
  its start/end/model arrays are `80A7B444`, `80A7B4D4`, and `80A7B708`.
  The constructor at `80A7A934` directly subtracts `2300` from the carried ID;
  this boundary needs the explicit actor mapping. Its size table at `80A7B324`
  and animation table at `80A7B7C8` also need extended readers.
- The insect owner is VROM `8DEEC0`, relocation `8E0870`, RAM `80A10210`;
  start/end/model arrays are `80A116B8`, `80A11738`, and `80A119B8` (32 entries).
  Its graphics bank is VROM `113D000`, 39,248 bytes. Behaviour dispatch and the
  added insects' orientation rules are required alongside the graphics readers.
- The donor release-shadow code itself has only six correction entries despite
  adding XXL arapaima. The port must supply bounded XXL handling, not reproduce
  that out-of-bounds read. The separate native `Gyo_Kage` actor (`85`) also
  needs its size reader extended. Existing fish timing and golden-rod hooks
  must survive the category integration.
- The ABI-294 shared resource file ends at `27F0F80`, only 61,568 bytes below
  its `2800000` limit. Copying both complete native graphics banks and enlarged
  actor owners into that file does not fit. Reuse the existing checked external
  physical-resource allocator for a complete category resource layout; do not
  repeatedly grow the ordinary import file or overwrite its neighbouring data.

`tests/test_v3_creature_field.py` checks every source/frame binding, differing
field/release timing, missing/disagreeing-pointer rejection, complete converted
resources and command bounds, and reuse of all seventeen existing room objects.
No native carried/field execution or new cartridge installation is claimed.
