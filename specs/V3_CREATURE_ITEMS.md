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
