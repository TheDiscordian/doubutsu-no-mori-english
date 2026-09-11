# Animal Forest English V1RC6 — private playtest

V1RC6 retains every RC5 correction and adds two menu-text fixes:

- Town-tune confirmation reads `Are you sure?`, `Yes`, and `No`, using the
  complete English GameCube wording.
- The Controller Pak note manager says `Erase a Pak note`. This is an N64-only
  instruction; the GameCube game has no corresponding screen to copy.

The original menu controls, choice handlers, sounds, timing, melody, prices,
Pak operations, and saved formats are unchanged. The Pak heading remains centred.

## Save compatibility

RC5-to-RC6 and RC6-to-RC5 save compatibility are expected: formats, name encodings,
and save readers/writers are unchanged. No migration is required. Neither loading
direction nor an RC6 save/restart cycle is independently verified. Keep original
backups and use test copies. Do not use RC3 as a fallback because its known
town-loading memory failure remains in RC3 itself.

An Expansion Pak is required. EverDrive uses FLASHRAM (128 KB / 1 Mbit), with
RTC enabled. Earlier ROMs and saves remain preserved.

## Verification and limits

Eight focused checks pass for the two text corrections, covering complete
wording, actual pointer/count instructions, relocated addresses, layout bounds,
unchanged memory allocation and BSS, retention of all other resources, and full
UPS reconstruction. Both stages are constructed from committed sources.
Packaging verifies the committed receipts, exact cartridge/patch hashes, and
standalone application against the original Japanese ROM.

These checks are not ordinary menu or original-hardware acceptance. Earlier
native catalogue, font, and other checks retain their original tested builds;
they are not presented as fresh RC6 execution. Broad gameplay and hardware
playtesting, save/restart verification, and other V1 acceptance remain unfinished.
The historical full test suite is not claimed passed. V2 remains deferred.

## Local artifacts

ROM: `build/v1rc6/Animal Forest English V1RC6.z64`.
Patch-only archive: `build/v1rc6/V1RC6-patch.zip`.

The included standalone patcher accepts the verified original Japanese ROM,
not an earlier translation, and refuses to overwrite an existing output. It
never accesses saves or the Controller Pak. Do not erase Pak notes merely to
test the heading; its appearance can be checked without deleting anything.

Keep this candidate private. The archive contains a patch and original tooling,
not a ROM or loose game assets. Public-release approval and broader review remain
outstanding. Lucky-bag Japanese decoration remains intentionally retained.
