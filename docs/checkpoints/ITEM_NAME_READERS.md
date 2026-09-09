# Complete inventoried item-name readers

## Applied state

The [reader boundary](../../specs/ITEM_NAME_READERS.md) accounts for all 35
recorded native item-name loader calls and the shared field consumers. Existing
inventory, catalogue, world-label, actor, choice, free-field, and letter-creator
integrations supply complete names. Remaining short calls are compatibility
preparations, fallback paths, or replaced routines, not untranslated final names.

`tools/item_name_readers.py` requires the complete family before allowing
resource-only item-name credit. The counter verifies each installed integration,
including additional explicit setter/wrapper/insertion, catalogue, song, and
world-font checks. The eight accented resource fields remain untranslated;
completing the reader family does not turn their Japanese bytes into English.
Catchphrase ambiguity and unrelated strings remain in their own pending state.

This closes the accounting/classification for implementations already present
in `build/letter-names-pilot`; no new ROM, resource, saved byte, or runtime code
changes in this batch. Its ROM SHA-256 remains
`785080e25caba10e4e0bc4557b84c6c08d23e47bbce0af70e097194db905c1de`.
No additional text is claimed merely for writing this classification.

## Bounded checks

All four focused checks pass in 92.246 seconds. They cover missing required
families, damaged fixed imports, altered catalogue/profile data, full current
cartridge measurement, no duplicate item/name credit, unchanged source
denominator, and retained missing-accent/catchphrase records. Older complete
reader builds legitimately receive the same item-family credit; their tests
retain their independent previous base weight and add only item-resource rows
without another credited source. Earlier partial builds remain pending.

The selected earlier choice-build accounting regression passes in 42.085 seconds;
all twelve counter unit checks pass. No build, emulator rerun, or new native harness is required for
this accounting-only change. Ordinary gameplay/save/restart remains in the
combined v0 safety pass, not inferred from the classification.

## Next implementation

Resolve ambiguous borrowed catchphrase display while retaining each original
villager's exact GC wording and four-byte saved data. Continue residual
text/letters and accents, then bounded combined v0 checks and playtest handoff.
