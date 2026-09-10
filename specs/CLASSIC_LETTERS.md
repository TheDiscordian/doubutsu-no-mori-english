# Retained classic letter variants

## Scope

The remaining eighteen classic variants are `0000`, `0001`, `004D`, `0053..0056`,
`0058..005B`, `00BF`, `0182`, `0183`, and `0186..0189`. They retain diagnostic,
older shop/museum, and unselected Mom text. Complete English exists in immutable
catalogue four. Installing the catalogue alone does not complete their application.
The five reserve variants `00C0..00C4` use their separate native-bank translations.

The adapter leaves all existing live creators, calendar selection,
random choices, full-name capture, and saved formats unchanged. It does not make
the excluded Mom dates eligible or claim that a ten-byte native free-string row
can recover a longer English name. Live full-name consumers retain their complete
owner-specific routes.

## Installed boundaries

`overlays/classic_letters/creator.c` adds a checked `AFCL`/`F0` request to the
existing on-demand creator. All other requests delegate to its complete seasonal
entry. The existing 5,344-byte transient workspace, allocation/DMA/relocation
checks, busy state, and lifetime remain. Only required literal slots are captured;
their native ABI supplies ten bytes, including padding. Non-English values,
unsupported IDs, invalid descriptors, overlap, and snapshot overflow fail without
publishing or changing capitalization. No truncation or guessed alias is allowed.

`hook.c` targets the classic wrapper at `80093F04`. Its argument order is header,
split output, footer, body, and template ID. For the eighteen selected IDs, the
hook requires the native contiguous 10/96/16-byte text geometry and a separate,
aligned split output. It creates a snapshot in a private 164-byte stage and copies
only its 122 text bytes plus the explicit split marker to the caller. It never
infers ownership of the metadata preceding the header. Unknown IDs, legitimate
separate-buffer calls, or generation failure retain the native sized wrapper at
`80093F54`; a partial snapshot is never published. That fallback is not proof of
English application for an unreviewed separate-buffer caller.

The startup adapter checks the exact original wrapper entry before calling the
existing atomic font installer, then publishes and flushes its eight-byte jump.
The appended image retains all existing font glyphs, state offsets,
code, and relocations. No font or creator limit is relaxed merely to fit the
adapter. Source-bound build, installation, complete applicable caller review,
and focused native evidence are required before granting progress credit.

## Status

`build/classic-letters-pilot` installs the exact source-bound profiles. The font
image is 12,000 bytes with 704 relocation bytes; the creator image is 61,200 bytes
with 960 relocation bytes. Both fit the existing limits. Independent MIPS builds
match, five host tests pass, and three strict profile/retention tests pass.

The native check in `build/classic-letter-native-02` passes nine calls and thirty
memory assertions, including actual startup installation, on-demand allocation,
static and dynamic complete letters, full reader output, the translated native
reserve fallback, saved-payload retention, guards, release, and checkpoint
restoration. Normal progression and persistent save/restart remain combined v0
checks. The [checkpoint](../docs/checkpoints/CLASSIC_LETTERS.md) records the exact
build, integration evidence, and the corrected packaging failure.
