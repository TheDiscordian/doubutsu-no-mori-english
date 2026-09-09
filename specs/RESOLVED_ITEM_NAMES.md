# Resolved stationery, totem, and placed item names

`translations/item_resolved_matches.json` records thirty explicit identities:
seventeen stationery designs, four totems, seven placed numbered shirts, a placed
cicada, and its already translated carried identity. The batch adds 65 complete
fields without changing any previously installed English wording. The carried
cicada gains explicit identity evidence but no new translated-text credit.

## Source identity

The pinned first-generation XLSX snapshot and the supplied native/English game
fields remain the authorities described in [the sheet-name specification](SHEET_ITEM_NAMES.md).
No online lookup is performed by builds, and no artwork is replaced.

Stationery names repeat across four GameCube quantity groups. The exact catalogue
item ID selects the correct complete English field; repeated wording alone does
not select a donor. For these seventeen entries the specific paper-pattern
texture references agree. The differing generic stationery model reference is
recorded, not concealed as an actual model comparison. The native danger paper
has a different design and remains pending rather than inheriting orange paper.

The four totem identities differ only in the sheet's halfwidth middle dot versus
the native fullwidth middle dot. Each exception is individually reviewed and
source-bound. No general Japanese spelling normalization or automatic approval
is introduced.

The seven numbered shirts have filler in their supplied furniture-name fields.
Their native placed IDs convert to ordinary clothing IDs with identical Japanese
fields. `native_carried_id` binds each placed approval to the existing complete
carried-name approval. The original supplied reference remains an `item_24` field,
not an invented furniture reference. All four placed rotations receive that name.

The native placed cicada `1BBC` converts to carried insect `2D05`. Both native
fields say `ツクツクボウシ`; the supplied carried name is `walker cicada`. The
catalogue's different `priest cicada` furniture label is not adopted. The carried
name remains unchanged and receives an explicit approval so the placed identity
can bind to it. The creature and native conversion stay unchanged.

## Validation and integration

Approval loading checks the exact native conversion and requires the carried
approval's source name, source hash, reference identity, and reference hash to
agree. Independent resource/build validation also checks the actual carried
Japanese bytes and all four placed rotations. Removing edit metadata cannot
bypass the root approval. Wrong conversions, missing donors, changed references,
shortened English, and false cross-family references fail.

Candidate generation reads only the ordinary reference families required by
explicit placed approvals. Both ten-byte and sixteen-byte builders use this
same mapping. All prior English bytes are retained. The combined counter credits
only the 65 previously Japanese source fields, with an unchanged denominator.

The wider resource and matching treasure article profile must be installed
together. Their current hashes are approved only after complete source
reconstruction. Creator code, size, relocation data, memory bounds, saved layout,
font, reader, and other actors remain unchanged; only name/article data and the
whole-creator CRC configuration may change. Frozen earlier profiles retain only
their exact recorded generator hash, never arbitrary changed runtime sources.

Current evidence and remaining work belong in
[the checkpoint](../docs/checkpoints/RESOLVED_ITEM_NAMES.md). Contextual review,
remaining names and text, full-name callers, normal gameplay/save validation,
hardware acceptance, patch-only release, title artwork, and the GameCube-style
keyboard remain required project work.
