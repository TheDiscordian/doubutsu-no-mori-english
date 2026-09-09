# Reviewed item-name identities

## Purpose and source authority

Different legacy wording does not establish that a complete GameCube item name
is unavailable. `translations/item_reference_matches.json` records individually
reviewed native Japanese names and their supplied English counterparts. It does
not relax legacy matching for other items and does not approve a name simply
because two tables share a numeric index.

Each approval binds the native storage ID, exact ten-byte source hash, complete
native spelling, English reference ID, exact sixteen-byte reference hash, and
an explanation of the identity. Furniture approvals use the first of four
rotation slots. Every rotation must contain the identical complete native name.
Ordinary groups retain their actual legacy donor ID even when an explicit
approval names a different English reference index. References stay in the same
name family; placed-object aliases use their separate native conversion proof.

## Reviewed furniture groups

The registry contains 614 furniture identities, two ordinary clothing-name
approvals, seventy [flooring/wallpaper approvals](FLOOR_WALL_NAMES.md), and
209 [song, stationery, seed, ticket, and other ordinary names](ORDINARY_ITEM_NAMES.md).
The furniture total includes all 127 [gyroid identities](GYROID_ITEM_NAMES.md).
Of the furniture identities, 179 cover the first 300 groups.
It covers wardrobes/dressers/cabinets, furniture-series pieces, household and
school objects, instruments, recognisable plants/bonsai, and outdoor/construction
objects whose native names agree with the selected English identity. Exact
existing legacy/English matches are not reapproved or changed.

Retain the supplied game's series names: Halloween becomes spooky, Christmas
becomes Jingle, chic becomes classic, royal becomes regal, resort becomes cabana,
log becomes cabin, lovely remains lovely, country becomes ranch, monochrome
becomes modern, Asian becomes exotic, and colourful becomes kiddie. These
are reviewed series-name localisations, not automatic substring rules.
Complete reference spelling/case remains, including names such as dresser,
tansu, sewing box, fan, tea table, screen, hibachi, stove, computer, N logo,
vibraphone, biwa lute, caladium, lady palm, snake plant, weeping fig, and dharma.
The unused dresser/monkey references retain their native unused designation.

Ambiguous cases remain unapproved. These include the chest/vanity mismatch,
Japanese-to-English figurine names, opaque totem variants, flower species,
paintings, grape/grapefruit, differing bonsai species, viola/violin, and several
objects needing a visual/model identity check. Names that omit the native
unusable prefix do not receive approvals. No artwork identity, asset replacement,
or reachability is inferred from the name review.

The [mapped-name groups](MAPPED_ITEM_NAMES.md) supply 308 further identities,
including 170 explicit cross-index matches after inserted English entries.
Two direct ordinary approvals handle explicitly reviewed carried-name spelling
variants without relaxing exact-source alias matching.
The mapped groups retain native creatures, object types, fossil parts, and chess pieces,
not the unrelated names at equal table indices. Gyroids have individual bilingual
family/size approvals. Changed species and designs, numbered-shirt filler, and
native game slots still require review.

## Two unchanged capacities

All 614 complete furniture names fit the existing sixteen-byte resource: 2,456 rotation
slots. Only 165 fit the unchanged ten-byte native fields: 660 slots. The other
449 names remain complete in the separately installed resource and withheld
from ten-byte storage. No abbreviations, removed suffixes, punctuation changes,
or rotation-dependent names are introduced to fit a smaller destination.
The two ordinary clothing approvals also fit sixteen bytes; bear shirt fits
ten bytes, while winter sweater stays complete in the wider resource.

The shared `item_candidates` importer accepts an explicit match map. Its ordinary
legacy path remains unchanged for unapproved IDs. Native source spelling/hash,
English hash, plain supported Latin encoding, family, and capacity checks remain
mandatory. `reference_candidates.py` and `extended_items.py` load the same
versioned approvals, so short and wide resources cannot select different names.

`tools/item_matches.py` also checks approved names independently in the ROM
builder and wider-resource builder. It binds the actual target source, all four
native rotations, reference identity, and complete padded English hash. Removing
the metadata from a direct approved ID does not permit shortening the name.
Changing an output and its self-reported reference hash does not bypass the
repository approval. A propagated alias must retain its exact native donor,
conversion, source-name equality, and complete reference. Unknown/malformed
approvals and non-item metadata fail.

The [original N64 name registry](NATIVE_ITEM_NAMES.md) is a distinct source for
native objects with absent, garbled, or different donor names. It uses explicit
project-authored provenance and `native:` identities, not fabricated GameCube
references. It shares both capacity paths while retaining independent complete
wording/source/alias validation. Original and donor approvals cannot overlap.

## Runtime and review boundary

The resource stays at its existing VROM, size, entry count, sixteen-byte stride,
and header. Native item IDs, save structures, fixed ten-byte banks, code, font
metrics, and caller capacities stay unchanged. The existing approved main-item
fields use complete wide names; other direct item loaders, free fields,
handbills, inventory/catalogue displays, dynamic choices, and editor destinations
still require their own expansion/reader checks. Resource presence does not
establish complete integration at every destination.

Tests cover explicit cross-index identities, unchanged unapproved matching,
complete names at both capacities, every new source/reference/rotation hash,
malformed schemas, altered names/provenance, metadata removal, native alias
conversion, and independent ROM/resource rejection. Native tests check actual
cartridge-loaded ten- and sixteen-byte names, complete output, unaligned wide
destinations, guards, and restored state. Ordinary item display, final name
review, all wider destinations, saving, and original hardware remain separate
acceptance requirements. Exact runs and hashes belong in `docs/WORK_LOG.md`.
