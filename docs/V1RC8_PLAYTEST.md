# Animal Forest English V1RC8 — private playtest

This combined candidate contains the English translation, proportional Latin
font, English title and screen/building artwork, GameCube-style keyboard, and
all current V1 corrections. It is a private candidate, not a public release.

## Changes from V1RC7

All 76 Japanese scene-selector, loading, and settings strings in the native
development-menu resource are now English. Existing English strings, scene
destinations, menu access, game actions, saved data, and timing remain unchanged.
This does not enable a debug menu. Do not enable one or invoke save/deletion
operations merely to inspect labels.

All earlier fixes remain, including the Nook furniture-delivery conversation
loop, Shrine map name, title prompt, keyboard layout/sounds, font and transition
edges, clock, Bells displays, catalogue/payment text, letter/board editors,
recipient names, ordinary-space marker, and existing-town loading correction.

## Hardware and saves

- Expansion Pak: required (8 MiB RAM).
- EverDrive save type: FLASHRAM, 128 KB / 1 Mbit.
- RTC: enabled.
- ROM size: 32 MiB, big-endian `.z64` output.

V1RC7-to-V1RC8 and V1RC8-to-V1RC7 save compatibility are expected in both
directions. No migration is required: this change does not alter saved formats,
names, or save readers/writers. These particular loading directions have not
been independently tested. Keep backups of existing saves. RC3 retains its
known town-loading memory defect; do not use it as a fallback.

A differently named ROM may select a different EverDrive save file. Preserve
the original save and use a copy associated with the new ROM name when keeping
an existing town. The patcher never accesses cartridge saves or a Controller Pak.

## Apply the patch offline

Extract the entire ZIP into one folder. Supply an extracted original Japanese
N64 ROM, not a previously translated ROM. Python 3 and its standard library
are sufficient; Docker, the GameCube disc, repository access, and a network
connection are not needed to apply this package.

From the extracted package folder:

```sh
python3 apply_translation.py --rom "Doubutsu no Mori (Japan).z64" --output "Animal Forest English V1RC8.z64"
```

On Windows, `py -3` can replace `python3`. The patcher accepts `.z64`, `.v64`,
and `.n64` byte orders for the supported original ROM, but not archive files.
It verifies the original, patch, full output, and boot checksum, and refuses to
overwrite an existing destination. The original ROM remains untouched.

- Original ROM SHA-256 after byte-order normalisation:
  `d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
- V1RC8 ROM SHA-256:
  `2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`.
- UPS SHA-256:
  `c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769`.

`manifest.json` records source revisions, build identity, and compatibility;
`SHA256SUMS` covers every other file in the ZIP. Only the locally reconstructed
ROM goes onto the cartridge. Do not redistribute that ROM.

## Verification and limits

The user confirms all reported V1-01 through V1-23 defects are fixed, the
earlier Nook-loop/Shrine corrections are fixed, and ordinary saving, restarting,
and reloading works across many hardware playtests. That acceptance stays
closed. It is not a claim that the new RC8 menu text has had a hardware session.

The current nineteen-stage correction build passes and matches the separately
built scene-menu result. The package is checked using its own standalone
patcher against the original ROM before handoff. No old candidate is re-tested
and no unchanged gameplay check is repeated to produce this package.

Broader seasonal/event/travel/Pak cases and undiscovered text/layout issues
remain human-playtest work. Ordinary appearance of source-identified menu
additions and both adapted festival-stall placements is not fully verified.
Neither the complete game nor every image is certified exhaustively reviewed.
The lucky-bag Japanese decoration is intentionally retained to match English
GameCube artwork. The grey N64-inspired keyboard redesign belongs to V2.

Use the short [bug-report guide](BUG_REPORT.md) for new findings. Do not repeat
already accepted cases solely because this candidate has a new name.

## Included documentation and terms

[Sources and credits](SOURCES.md) and the [optional source-build guide](TOOLCHAIN.md)
are included in this ZIP and work without private-repository access. The source
repository itself remains private; the source-build commands require its checkout.
The patcher works independently of those commands.

`LICENSE-tooling.txt` covers original project tooling, not Nintendo content or
legacy work. This ZIP contains the UPS, documents, manifest, checksums, and two
Python files. It contains no ROM, save, emulator checkpoint, or loose game asset.
Public distribution and source-repository publication require separate review
and approval; generating this package does not publish either.
