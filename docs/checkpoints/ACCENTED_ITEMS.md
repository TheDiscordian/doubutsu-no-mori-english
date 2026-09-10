# Accented item implementation

## Installed result

`build/accent-items-pilot/animal-forest-halfwidth.{z64,ups}` installs café shirt
and its four placed rotations, Pokémon Pikachu, Café K.K., and Señor K.K., with
complete display and generated-letter consumers. Rebuild with
`python3 tools/accent_items_install.py` after preparing its checked accent
artifacts and apology baseline. The cartridge is 33,554,432 bytes and uses the
existing four-MiB configuration; no Expansion Pak requirement is added.

- ROM SHA-256: `e09680bf156ae1b2662aca16878e056070f4acb07f26b5043a6789d9890ebb0e`.
- UPS SHA-256: `8e2dab236923fe38d49efe65451eacf7ecf08e29a3db8bbfce434acb17bfecf1`.
- Full-name SHA-256: `693ef2c0749822d07062114ffff0b35b4bb8a56d3b2617c932d9220dcc92165b`.
- Font-resource SHA-256: `24ae623d2917a2370ec70504daf372be327c830d24fb37bacc68ad84f0bbe90e`.
- Catalogue-five SHA-256: `26b2e95b10b8ae049853ecc6180e41c12b86efc677e39ee03f9742077e9005be`.
- Article-resource SHA-256: `b218119460fdbb472e641cbbc6d77ff809d489bda8b8622f0157562294d575ff`.

All 4,536 preceding English name fields, fourteen preceding separate glyph cells,
and original native atlas pixels remain unchanged. The two added ñ/Ñ cells use
actual donor codes `87/12`, both six pixels wide. Ordinary short-bank imports and
custom-input fields do not gain general permission for extended pairs.

## Complete consumers

The font/world/mail owner contains 11,344 image bytes and 672 relocation bytes,
requiring 12,031 allocated bytes within the existing loader limits. Four resident
mail entry guards precede startup installation; no fallible step follows old
font/world installation. Its image SHA-256 is
`f2bbd23684cb682ef38712e6d2dc5b5b971b5f8ec2c1e2feb756b09631078d98`;
relocation SHA-256 is
`6c9fda4a52beb4dfbe5aa57e1e39693f2ce2d67be8edcc26e24048216a11d657`.

The shared and sale-event capture/generation entries bridge through the actual
owned font pointer, preserving stack arguments. The shared creator and separate
board reader append the same checked treasure adapter. Shared creator image and
relocation sizes are 60,400 and 944 bytes; board sizes are 26,560 and 816 bytes.
The board fits its existing 27,264-byte seasonal reservation. The sale actor
keeps its 38,128-byte image size. The resident image, heap boundaries, shared
submenu pool, 122-byte mail envelope, and 96-byte treasure envelope stay intact.

Catalogue five changes only the two catalogue-four header words. Old catalogues
retain every payload and saved interpretation. Only used, exact accented item
fields upgrade newly generated catalogue-four letters. Catalogue-two upgrading
is limited to the sixteen sale templates whose complete parts match catalogue
five. Treasure packing leaves the caller's record unchanged, and both readers
retain native field masks, checksums, lengths, and town-heading correction.
The article resource changes five exact rows and the bound full-name hash only.

The installer reconstructs from the guarded original cartridge, retaining native
DMA indices and every unrelated resource. Exact approved updates include name
and article data, font/mail owner, three on-demand profiles, catalogue five, and
existing loader/owner metadata. Rebuilding from the original avoids appending
another payload after the already padded 32-MiB baseline. All existing letter,
shop, and notice resource-hash bindings identify the installed complete names.

## Verification

Seven host mail tests, two compiler/article tests, three accent-font tests,
three on-demand/installation tests, and thirteen counter regressions pass.
Independent font and all three on-demand builds agree. Checks cover exact
sources, old-profile retention, malformed pairs, atomic failure, capacities,
relocation at two bases, all unchanged cartridge payloads, and UPS reconstruction.
Combined accounting verifies every installed accent route and credits only the
eight exact fields. Its ledger is `build/accent-items-progress/entries.jsonl`.

The silent native run `build/accent-mail-native-02` passes 36 calls and 45 memory
assertions on the installed ROM. It verifies actual startup and all four hooks,
loads the shared creator, board reader, and sale actor from the cartridge through
native DMA/relocation/cache routines, and exercises all four exact item names.
Captured letters restore their complete English; invalid pairs fail; articles
match the donor; treasure packing and both decoding paths work; sale letters
upgrade correctly. No executable code is uploaded by the debugger.

The 81,920-byte isolated test allocation, stack, and module guards survive.
The complete saved payload remains unchanged, the test workspace is freed, and
the owned font pointer is retained. Checkpoint restoration completes, test scratch
returns to zero, and the emulator exits normally. The run uses blank isolated
saves, no flash-write opt-in, no audio, no screenshot, and four MiB.

The initial fixture passes startup checks but is rejected before its first DMA
call because the debugger requires exact verified bytes for kernel helpers below
its ordinary admission range. Adding those existing source-guarded helper ranges
is the single justified fixture retry; that corrected run passes completely.
This admission failure is not a game crash. Do not repeat the accent harness.

Ordinary gameplay and normal save/restart remain in the assembled v0 smoke;
checkpoint restoration does not substitute for persistent-save testing. Continue
the residual general/interface strings and letter variants. The separate apology
checkpoint retains its ordinary-submenu verification requirement.
