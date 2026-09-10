# English translation: private v0 playtest candidate

This candidate contains the base English translation, proportional Latin text,
complete English names and letters, and the English-first native keyboard.
The title artwork and GameCube-style keyboard are follow-up features.
It is a private test build, not a hardware-certified or public release.

## Apply the patch

Use your own extracted Japanese retail ROM, not an earlier translation ROM.
The included Python 3 patcher accepts the standard N64 ROM byte orders and
checks the source, patch, resulting ROM, and N64 boot checksums. It never
overwrites an existing output or changes the source file.

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English.z64'
```

An ordinary UPS patcher also works with the verified big-endian `.z64` source.
The source and resulting SHA-256 values are in `manifest.json`; `SHA256SUMS`
checks the package files. Extract `.7z` archives before applying the patch.

## Compatibility and testing

The ROM is 32 MiB. Native execution and fresh-game entry/arrival checks run in
4 MiB; an Expansion Pak is permitted but is not a verified requirement of this
candidate. The first original-hardware playtest reaches the furniture-delivery
job but encounters the critical conversation loop listed below; this is not
complete hardware acceptance. Use the flash cartridge's
normal Doubutsu no Mori save/RTC configuration; no cartridge-specific settings
are asserted by this package.

Use a separate test save and back up existing saves before playing. Do not
overwrite a valued Japanese or earlier translation town. Complete English
generated letters use translated snapshot records; returning a translated save
to an unmodified Japanese ROM is not a supported migration.

Focused cartridge, relocation, buffer, letter creation/readback, and native
memory checks pass. Fresh-game English name/town entry, long choices, and train
arrival pass in the combined candidate. Native FlashRAM letter tests exercise
isolated writes and fresh-process reads in earlier matching subsystem builds;
that evidence is not a normal in-game save/restart or hardware test.

The combined regression run is still under review. Ordinary game-menu saving
and post-load gameplay, later tutorial progression, the complete apology-editor
guard check, and broad menu/mail/board interaction are not yet established by
the combined candidate. These missing checks are not reported as passes.

## Known limitations and bug reports

- **Critical:** Nook's furniture delivery to Buzz loops the whole conversation,
  including the furniture reward, instead of finishing. The handed-off candidate
  retains this defect; a separately verified correction is required.
- The map incorrectly calls the native shrine "Wishing Well". The label must be
  "Shrine", preserving the N64 location rather than its GameCube replacement.
- Japanese text remains visible on signs, bags, buildings, and screens including
  the map, inventory, and time settings. Classify text versus image assets before
  replacement; use matching supplied GameCube art where appropriate.
- English title artwork and a GameCube-style grid keyboard are not included.
- Native input/storage limits remain for custom player names and catchphrases.
- Line layout needs a human polish pass. Preserve deliberate GameCube line/page
  breaks and timing when reporting awkward spacing.
- Seasonal events, travel, every dialogue branch, and a full hardware playthrough
  remain human acceptance work.
- Three zero-filled storage slots remain untouched; they are not displayed
  Japanese phrases. The text inventory is not a proof that every image or
  undiscovered embedded string has been localized.

For a bug, record the manifest revision, emulator or cartridge/hardware, current
game activity, displayed text, and steps to reproduce. Retain a copy of the test
save if the issue involves saving or letters. A screenshot helps for text/layout
issues. Do not distribute ROMs or disc images in bug reports.

## Distribution

This archive contains a patch and original tooling, not a full ROM. Keep it
private during the playtest. Public distribution needs the project's outstanding
provenance and release review. The tooling licence does not grant rights to
Nintendo assets, extracted English text, or legacy translation work. See
`SOURCES.md` and `LICENSE-tooling.txt`.
