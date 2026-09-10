# English artwork and keyboard: private playtest

This experimental build combines the English translation, corrected Nook
first-job conversations, English title, GameCube-style keyboard, and translated
screen/building artwork. It also includes the birthday window, editor
confirmation, inventory/Pak warnings, and gyroid service responses.
The seasonal artwork includes Nookington's clearance/door details, both dump
signs, fishing props, the fortune table, and countdown minute/second labels.
The festival stall uses a compact GC-style shared mesh with a reflected second
placement, preserving native memory limits and item behaviour.
See `FEATURES.md` for the complete feature and verification notes. This is not a
completed v1, hardware certification, or public release.

## Apply the patch

Use your own extracted original Japanese retail ROM, not a previous translation
ROM. The included Python 3 patcher accepts standard N64 ROM byte orders and
checks the source, UPS, output, and N64 boot checksum. It does not overwrite an
existing output or change the source file.

```sh
python3 apply_translation.py --rom 'Doubutsu no Mori (Japan).z64' --output 'Animal Forest English Artwork Playtest.z64'
```

An ordinary UPS patcher also works with the verified big-endian `.z64` source.
Extract compressed ROM archives first. Exact source/output hashes and source
revisions are in `manifest.json`; `SHA256SUMS` checks the archive members.

## Hardware, saves, and controls

An **Expansion Pak is required**. A console without it displays an English
power-off/install instruction. The ROM is 32 MiB. The ordinary game heap remains
within four MiB; the title owns the extra memory. Use the flash cartridge's
usual Doubutsu no Mori save/RTC configuration. No cartridge-specific setting
or complete original-hardware compatibility is asserted by this package.

Back up existing saves and use a copy for playtesting. Native saved layouts and
input limits remain; complete English letter snapshots are not a supported
migration back to an unmodified Japanese ROM. The patcher itself never reads or
changes a save file.

On the keyboard, the stick/D-pad selects a key, A types, B deletes, and Start
finishes. L changes case, Z changes page, L+Z changes QWERTY/alphabetical order,
and R inserts a space. C-buttons move the text cursor; L+A applies the native
character alteration. Unsupported characters are disabled.

## Remaining playtest work

The full-conversation furniture-delivery loop and later letter-advice cleanup
have focused native fixes, but still need the ordinary hardware tutorial replay.
The GC-style stall needs ordinary appearance/lighting acceptance; lucky-bag
decorative writing remains Japanese as in GC. Line layout needs a human
polish pass preserving intentional GC line/page breaks and timing.

The embedded warning/confirmation native drawing probe is incomplete after a
test-script error; its cartridge, pointer, allocation, and host checks pass.
The birthday and gyroid-response native drawing checks pass, but do not replace
ordinary navigation. Complete menu/editor use, gyroid transactions, normal
save/restart, return-to-title/existing-save paths, travel, seasonal events, and
the full hardware playthrough remain unverified. Missing evidence is not claimed
as a pass, and no confirmed new game crash or save defect is waived by packaging.

For a bug, include the manifest revision, hardware/flash cartridge, activity,
displayed text, and reproduction steps. Retain a copy of the test save when
relevant. Do not attach full ROMs or disc images to public bug reports.

## Distribution

Keep this playtest bundle private. It contains a patch and original tooling,
not a full ROM. Public release requires the separate provenance/release review.
The tooling licence does not grant rights to Nintendo content or legacy work.
See `SOURCES.md` and `LICENSE-tooling.txt`.
