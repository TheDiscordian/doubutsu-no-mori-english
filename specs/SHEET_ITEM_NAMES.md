# Source-bound first-generation item-name matches

## Identity and presentation

`translations/item_sheet_matches.json` adds 327 explicit identities to the
existing item registry. They cover 169 placed furniture/clothing/umbrella groups,
eleven carried umbrellas, 109 carried clothes, one shell, twenty floors, and
seventeen walls. All English fields come from the user-supplied GAFE01 disc,
including original spelling, case, and punctuation. No artwork is replaced.

The [first-generation comparison sheet](https://docs.google.com/spreadsheets/d/13sRAcj9YbP9_i-u0Kg6S7ycHbaOQx1jFG4lYLm2DJ4c/edit)
corroborates each exact native ID, Japanese name, and English localisation.
The ignored XLSX snapshot has SHA-256
`7fcfb2d7ac3c30c3c69650ed61ae253c9589be0fba4b3aff09a334770da32be0`.
Approvals retain both local game-source hashes, the worksheet row and stable row
identifier, and the snapshot hash. Matching N64/English artwork references are
supporting catalogue evidence, not a claim that the actual texture data has been
compared. Exact native bytes and exact supplied English fields remain the build
authority. The online sheet is not fetched during builds.

`tools/item_identity_sheet.py` reads stored worksheet values without executing
formulas or links. Its queue requires the pinned snapshot and expected columns,
then checks unique native IDs, exact Japanese spelling, complete reference names,
and version-specific image/texture references. Queue entries are never approvals.
`load_matches` merges the separately versioned, explicitly reviewed registry and
rejects duplicate roots or malformed identities. The original batch can still be
selected for its frozen tests with `include_sheet=False`; `include_resolved=False`
retains this sheet batch without the additional explicit resolutions.

The shifted later furniture references stay explicit. The final figurine and
four clocks do not inherit the donor's same-index custom umbrellas or NES titles.
Complete GameCube localisations such as classic vanity, the named figurines,
flower furniture, painting names, and plant/instrument names are retained rather
than literal legacy glosses. All original object identities and behaviour stay.

## Open names are not silently resolved

The four red/blue gym-clothing fields have conflicting carried/placed Japanese
labels and differently worded English fields and remain pending reconciliation.
The [resolved-name specification](RESOLVED_ITEM_NAMES.md) binds the cicada's placed
name to its existing supplied carried label through the actual native conversion.
The furniture `cafe shirt` field does not
authorise removing the accent from the carried `café shirt`.

Accented songs, Pokémon Pikachu, native-specific changed paintings and garments,
the pierced/glass-top table, bathhouse/worn-wood/worn-earth designs, original
vending machines/basins remain required work. The additional resolved-name batch
binds numbered placed shirts to their complete carried fields, reviews the four
totem middle dots individually, and selects seventeen stationery references by
exact native/English ID among repeated quantity groups.

## Complete resources and grammar

The batch adds 834 complete sixteen-byte fields: four rotations per placed group
plus carried/ordinary identities. All earlier 3,563 fields remain unchanged, for
4,397 translated fields. The remaining 147 name-resource fields are not treated
as translated. All 112 names/rotations that fit ten bytes also enter the native
bank, adding to the existing 13,598 ordinary edits. The new total is 13,710.

The name resource retains header, VROM, entry counts, width, and allocation size.
The [article profile](ITEM_ARTICLES.md) must be rebuilt and installed with these
names. Its 8,576 bytes bind each full name to the supplied article and CRC; the
immutable name/article hash pair prevents cross-installing old and new tables.
Only this read-only data changes inside the 58,144-byte complete creator. Code,
symbol offsets, 848-byte relocation table, workspace, and allocation stay exact.
The only resident-image change is the approved complete-creator CRC configuration.
The reader, other resources/actors, font, saved layout, and four-MiB bounds stay.

The original article profile remains verifiable with its exact original
generator hash. This exception is restricted to that immutable profile and that
one source-file identity; every compiled source and actual article bytes still
must match. It is not permission to waive changed runtime sources in old builds.

## Acceptance

Check every complete name, source/reference/rotation, original edit retention,
both capacities, and shortening/provenance rejection. Reconstruct articles from
the supplied REL, test all native IDs and damaged fields under sanitizers, and
reject mixed profiles. Independent creator builds must agree, with identical
code and relocations. The complete ROM changes only the native name bank, wider
name resource, creator data, and creator-CRC configuration; the UPS must recreate
that ROM from the original input.

The bounded native name batch covers the new identities and short fields with
shared loader boundaries, guards, and checkpoint restoration. Completed dialogue,
letter, and board batches are not replayed. Wide-name caller expansion, contextual
review, normal gameplay/save acceptance, and hardware remain separate required
work. Evidence and continuation are recorded in
[the checkpoint](../docs/checkpoints/SHEET_ITEM_NAMES.md).
