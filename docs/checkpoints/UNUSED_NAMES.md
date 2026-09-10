# Retained name-list translation

## Installed result

`build/unused-names-pilot/animal-forest-halfwidth.{z64,ups}` applies all 200
original English spellings in `string:009C..0163`. These retained records contain
824 Japanese source characters and have no selectors in the live animal-name,
special-character, or default-catchphrase tables. The supplied GameCube disc
retains the same Japanese bytes, so its Latin decoding is not an English source.
Original loanword spellings/romanizations preserve the retained name identities;
live localized villagers and their saved identities remain untouched.

- ROM SHA-256: `e02d3387c61913dad85aece9ff69f3d9de30a7951373755a89620f7849916ccf`.
- UPS SHA-256: `fdc805b9c3189c40ee6d8e2c1c4cf33b530a562d824ee633f77fe6d13601faef`.
- String-data SHA-256: `33d61d0c48315c9b386589b8183d5099c6cc26206ac0f4447ad57cea02adf0c6`.
- String-table SHA-256: `b84450e257a5afe966b3a7604b247496e602abd9982e2cfe2c31e5c98521c0ab`.

Rebuild with `python3 tools/unused_names.py` using its exact accent predecessor.
The 32-MiB cartridge retains the same four-MiB runtime configuration. Only string
data, cumulative offsets, and DMA metadata change. All code, accents, letter
catalogues, fonts, editors, and saved structures are unchanged. Complete names
fit thirteen bytes in the existing 64-byte generic loader contract; the longest
is `Chima Chogori`. This grants no wider saved-name or unrelated caller capacity.

## Verification

All four focused tests and thirteen counter regressions pass. The focused group
covers the exact native and donor source, all complete translations, rejection of
changed/partial/duplicate/overlong/command-bearing manifests, all 1,562 bank rows,
every unrelated resource and DMA index, full cartridge reconstruction, UPS
reconstruction, and combined accounting. Changed metadata and an altered item
resource are rejected. The counter retains all preceding credit and adds exactly
824 source characters once. No additional native harness is needed for this
data-only batch; unchanged loader and accent code retain their recorded evidence.

Continue residual general/interface strings and unselected letter variants.
Intentional empty English counters/letter components need explicit source-bound
accounting, not filler text. Zero-filled name/item tail storage remains structural
data and must not be overwritten to make a percentage move. Ordinary progression,
menus, apology entry, and normal save/restart remain in the assembled v0 smoke.
