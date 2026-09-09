# Complete fishing-record winner names

## Save-safe reader

The fishing-event actor at VROM `0094FF70`, RAM `80A8FCF0`, owns the score and
winner display. Its saved record has a four-byte score followed by a sixteen-byte
PersonalID: six name bytes, six town bytes, and two two-byte IDs. Saved fields,
score logic, random selection, and player-win copying remain unchanged.

NPC initialization at `80A90124` writes both numeric IDs as `FFFF`, copies six
native villager-name bytes, clears six town bytes to spaces through `80094EE0`,
then copies the five-byte marker at `80A90854`. The complete dummy town is
`98 A6 8F A1 20 20`. Both reserved IDs and all six dummy-town bytes must match
before a saved name can be interpreted as an NPC alias. A player with a matching
visible name but ordinary identity fields is not translated.

Only the name-field setter call at `80A9031C` changes. Its existing arguments
are the window, slot zero, PersonalID pointer, and length six. The new helper
performs an exact six-byte lookup in the [saved-name alias resource](NPC_MAIL_NAMES.md).
Known NPCs use the complete eight-byte English literal. Unknown keys, non-NPC
identities, and unexpected input lengths retain the original pointer and length.
There is no prefix matching, current-town lookup, save write, or session cache.
The score field at `80A90300`, original frame, and all writer instructions remain.

## Ownership and validation

The 3,296-byte native image and its original sixteen BSS bytes precede the
appended helper and immutable 6,368-byte alias resource. The original BSS offsets
remain fixed and are materialized as zeros. The alias resource is generated
locally from the hash-verified native ROM and complete English name resource;
extracted aliases remain ignored. Native relocation entries are retained, and
owned helper/table references receive explicit relocation entries. The main-code
actor metadata at `80102050` grows with the image; the profile pointer remains.
The new DMA pair uses `03B40000` and `03B50000` at the original pair's indices.
No resident allocation or save layout changes.

Installation requires the complete name resource and persistent dialogue fields.
Validation binds native actor/metadata, helper source and compiled image, aliases,
relocation, and ownership. Whole-game accounting verifies this reader without
adding another copy of the original villager-name records. Other unfinished
name consumers remain pending.

## Bounded checks

Check exact aliases and all identity-marker bytes, player-name collisions,
unknown keys, input immutability, output arguments, original writer/score code,
two relocation bases, independent compilation, and complete ROM/UPS retention.
Reuse the unchanged general-field setter's native evidence. Ordinary fishing
event interaction and save/restart belong to the combined v0 smoke; this reader
does not establish exhaustive old-save or original-hardware compatibility.
