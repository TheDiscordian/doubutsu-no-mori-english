# English villager names

## Identity and native storage

The native game has 216 villager IDs. The name DMA file at VROM `00E04000`
contains an eight-byte header followed by six-byte, space-padded names. Its
additional complete alignment/reserve slots are not additional villagers.
Native `mNpc_LoadNpcNameString` at `800ACC38` computes `8 + 6 * name_id`, transfers
eight bytes into a local buffer, and copies six bytes to the caller. ID `FF`
does not load or write. Actor IDs, saved identity structures, and all destinations
retain their original sizes.

The first 216 names in the supplied English disc's name resource agree with the
same-index legacy English names. The first 216 native and GameCube personality
table entries also agree. Candidates require exact legacy-name confirmation,
the native slot hash, plain supported Latin text, and the GameCube reference's
complete eight-byte padded hash. Names are not inferred from similar spelling.

## Initial import

178 complete English names fit in six bytes. Import those with native space
padding, leaving the file header, every other name, and trailing reserved bytes
unchanged. The remaining 38 names need seven or eight bytes and remain withheld;
the generator must not truncate or abbreviate them. This is partial name coverage,
not a decision to ship Japanese names in the final translation.

The reference manifest distinguishes encoded text length from six-byte stored
length and records the source/reference hashes. Names remain candidates pending
gameplay review. Item names, special-character names from the general string
table, and user-entered player names are separate categories and are unaffected.

## Wider-name work

The full port must support the remaining reference names without corrupting
six-byte saved fields, personal identities, letters, labels, and temporary
buffers. Adding two bytes to the ROM stride alone is insufficient. That design
requires all loaders/readers and save compatibility to be audited before enabling
longer names. The initial import does not increase any buffer or change any ID.

## Validation

Static tests verify identity guards, padding, unsupported glyph rejection,
overlong-name withholding, unchanged reserve slots, and unchanged DMA file size.
Native tests load all 216 actual cartridge names into six-byte destinations with
guards on both sides, verify the resulting text, and test the no-write `FF` path.
World dialogue labels, quest names, mail, and save/reload remain gameplay tests.
