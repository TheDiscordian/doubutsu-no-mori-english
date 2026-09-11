# Animal Forest English V1RC5 — private playtest

V1RC5 addresses the catalogue and repayment labels reported on RC4:

- Catalogue prices show the English GC Bells image.
- Unorderable items show the complete `Not for Sale` wording.
- The repayment heading reads `Your Loan`, with `OK` on the confirmation button.
  Both shorter labels are centred in their original locations.

The catalogue's longer label bypasses the original small text buffer safely.
Prices, orderability, loan calculations, controls, existing English artwork,
and all RC4 corrections are retained.

## Save compatibility

RC4 saves are expected to work in RC5: saved formats, readers/writers, and name
encodings are unchanged, and no migration is required. Loading an existing world
and saving/restarting on RC5 are not independently verified. Keep backups and
use test copies. Compatibility is preferred, not mandatory; any required break
must be announced before testing. Do not use RC3 as the fallback because RC3
retains its known town-loading memory failure.

An Expansion Pak is required. EverDrive uses FLASHRAM (128 KB / 1 Mbit), with
RTC enabled. RC4 and previous saves remain preserved.

## Verification and limits

Five focused checks pass, covering complete source wording/pixels, unchanged
transaction code, buffer bounds, relocation, shared memory, resource retention,
and complete patch reconstruction. Both branches of the assembled catalogue
adapter also execute successfully in a silent emulator check with intact
buffers, guards, save data, and restored checkpoint. The font call is captured
in that check; it does not establish actual screen appearance or hardware acceptance.

Recheck catalogue prices, a non-sale item, and the repayment screen during
normal play. The broader human playthrough, save/restart validation, and other
outstanding V1 acceptance remain unfinished. The full historical test suite
is not claimed passed. V2 keyboard redesign remains deferred.

## Local artifacts

ROM: `build/v1rc5/Animal Forest English V1RC5.z64`.
Patch-only archive: `build/v1rc5/V1RC5-patch.zip`.

The standalone patcher accepts the verified original Japanese ROM, not a prior
translation, and refuses to overwrite an existing output. It never accesses
saves. Patch reconstruction is checked before handoff.

Keep this candidate private. The archive contains a patch and original tooling,
not a ROM or loose game assets. Public-release approval and broader acceptance
remain outstanding. Lucky-bag Japanese decoration remains intentionally retained.
