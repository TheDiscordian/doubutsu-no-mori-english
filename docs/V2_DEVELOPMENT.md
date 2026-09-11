# Animal Forest English — V2 Development

This private development patch includes the complete V1 Final translation and
the N64-inspired keyboard: light grey background, native N64 button graphics
with held feedback, and a left-side stick image. It retains the accepted key
positions, proportional editing, two keyboard pages, sounds, controls, and
saved capacities. The redundant label beside the stick is omitted; movement
instructions remain at the bottom.

This is not a public release or a V2 Final certification. The ZIP contains no
ROM, save, emulator checkpoint, or loose game artwork. Applying it to the
supported original ROM produces the current V2 development cartridge.

## Hardware and saves

- Expansion Pak: required, 8 MiB RAM.
- EverDrive save type: FLASHRAM, 128 KB / 1 Mbit.
- RTC: enabled.
- ROM: 32 MiB, big-endian `.z64`.

V1 Final → V2 and V2 → V1 Final save compatibility are expected without
migration. The saved formats and complete editing/input prefix are unchanged;
those particular loading directions have not been independently tested. The
prior ordinary save/restart/reload workflow has human hardware acceptance,
not a new claim of V2 save testing. Keep backups and associate a copy with the
matching EverDrive ROM filename. Do not use RC3 as a fallback because of its
known existing-town loading defect. The patcher never accesses game saves.

## Apply the patch offline

Extract the entire ZIP into one folder. Supply the extracted original Japanese
N64 ROM, not V1 or an earlier English build. Only Python 3 and its standard
library are required; no Docker, source checkout, GameCube disc, or network is
needed to apply this patch.

```sh
python3 apply_translation.py --rom "Doubutsu no Mori (Japan).z64" --output "Animal Forest English V2 Development.z64"
```

On Windows, `py -3` can replace `python3`. The patcher accepts supported `.z64`,
`.v64`, and `.n64` byte orders, not ZIP/7z archives. It verifies the original,
patch, complete output, and N64 boot checksum, and refuses an existing output
path. The original stays untouched.

- Original SHA-256 after byte-order normalisation:
  `d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908`.
- V2 ROM SHA-256:
  `085e3dfc10cc03e591ce4197d7f3841c45e3fba3b51344d1be58c87cda2fe9d9`.
- UPS SHA-256:
  `cbcee703fcf3f3957a112449a11e0718ac1a134fb440d2afddcfc6705228c888`.

`manifest.json` records source revisions, source hashes, compatibility, and
verification limits. `SHA256SUMS` covers every other archive member. Put the
locally reconstructed ROM on the cartridge; never redistribute that ROM.

## Verification and limits

The current build passes four focused checks of patch reconstruction,
unrelated-resource retention, editor relocation, artwork/font/key metrics,
and memory limits. Its suffix occupies 7,744 of the existing 8,192 reserved
bytes without a new allocation.

Controlled native drawing and ordinary name entry pass before the final
redundant-label removal: spaces, caret movement, deletion, Start confirmation,
and representative held-button appearance are checked. That removal has
focused artifact checks, not a new gameplay run. The manifest identifies the
tested predecessor instead of claiming exact-output hardware verification.

V1's reported fixes and repeated ordinary saving/restarting/reloading retain
their human acceptance. Other V2 keyboard callers, remaining pressed states,
cross-version loading, and original-hardware acceptance remain playtest limits.
Broader seasonal/event/travel/Pak combinations and individual dialogue layouts
are not exhaustively reviewed. Concrete findings use the [bug-report guide](BUG_REPORT.md);
an exhaustive test matrix or fresh town is not required for a report.

## Sources and distribution

[Sources and credits](SOURCES.md) and the [optional source-build guide](TOOLCHAIN.md)
are included for offline reading. `LICENSE-tooling.txt` covers original tools,
not Nintendo content or legacy work. The repository and package remain private.
Technical packaging does not grant redistribution rights; public publication
requires separate review and the user's approval.
