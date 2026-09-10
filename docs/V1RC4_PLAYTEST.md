# Animal Forest English V1RC4 — private playtest

V1RC4 fixes the RC3 town-loading memory crash and removes the stray `SP` blocks
drawn to the right when
entering spaces in a name. Ordinary spaces display blank, matching the English
GameCube name window. The shared fix also applies to town names, catchphrases,
apology input, and song requests. The keyboard's Space label remains visible.
Name contents, input limits, and proportional caret movement are unchanged.

The complete bordered font moves into its own Expansion Pak reservation,
separate from title artwork and the original game heaps. Font pixels, edge
correction, speech spacing, and transition improvements remain intact.

## Save compatibility

**The supplied RC2 save loads in RC4, and the player responds to movement.**
The same save reproduces RC3's out-of-memory fault. This correction changes no
saved formats, readers/writers, name encodings, or migration requirements.
Loading an RC3-created save in RC4, loading an RC4-written save in older RCs,
and a manual save/quit/restart cycle are not yet verified. Backward compatibility
is preferred, not mandatory, and necessary incompatibilities receive advance
warning. RC3 retains its known older-save loading crash; do not use RC3 as the
fallback test. Preserve original saves and test with separate copies.

Do not move English letter snapshots back to the unmodified Japanese game.
Future RC handoffs explicitly warn about any older-version incompatibility and
state any required migration before use.

An **Expansion Pak is required**. EverDrive uses **FLASHRAM (128 KB / 1 Mbit)**
with **RTC enabled**. RC3 and existing saves remain preserved.

## Checks and limits

Four focused tests verify the actual marker-branch instructions, spaces at the
beginning/middle/end of names, repeated spaces, relocation, complete retention
of all other ROM resources, and patch reconstruction. The corrected branch
skips only the old marker drawing; the original text/caret calls remain.
These are instruction/resource checks, not a fresh emulator or hardware draw.

Four additional focused tests cover the new font loader's bounds, CRC and
failure paths, absent-memory behaviour, re-entry, unchanged resources, and
full patch reconstruction. Host loader checks use address/undefined-behaviour
sanitisers. Native loading and controller movement preserve the complete loaded
font and font/title/module guards, with no faulted game thread. The loaded town
has 25,216 free bytes; RC3 has only 304 bytes when its 528-byte request fails.
Actual four-MiB emulation also confirms a clean unsupported-machine stop.

The font-edge and building-transition implementations retain their existing
controlled native evidence on the builds identified in the RC3 records. Their
unchanged drawing resources are checked in this cartridge, but the font's
allocation address changes. Earlier controlled drawing executions are not
relabelled as fresh RC4 tests. Normal save/restart, original-hardware
appearance, and the broad human playthrough remain acceptance work. The
historical full regression is not claimed passed.

Recheck spaces in a name and continue ordinary playtesting. Report issues using
the V1RC4 label. The N64-inspired keyboard remains V2 work, after V1 completion.
Lucky-bag Japanese decoration remains intentionally retained.

## Patch and local ROM

The local ROM is `build/v1rc4/Animal Forest English V1RC4.z64`.
The private patch-only archive is `build/v1rc4/V1RC4-patch.zip`.
The archived standalone patcher accepts the verified original Japanese ROM,
not an earlier translation, and refuses to overwrite an existing output.
Its execution is checked before handoff. The patcher never accesses saves.

Keep this playtest private. The archive contains a patch and original tooling,
not a ROM or loose game assets. Provenance review and public-release approval
remain outstanding; this candidate does not certify completion of V1.
