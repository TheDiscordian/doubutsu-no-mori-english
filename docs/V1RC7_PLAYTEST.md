# Animal Forest English V1RC7 — private playtest

V1RC7 retains all RC6 corrections and includes two further text batches:

- The title's missing-controller warning is English and retains the instruction
  to power off before connecting Controller 1. Its native erase-save menu label
  reads `Erase Save Data`.
- The separate native player-selection/save-menu gamestates have complete
  English headings, resident/status labels, and save-destination labels. Their
  access paths are unchanged; this does not enable an extra menu or replace the
  ordinary player option already corrected in earlier candidates.

The catalogue `Bells` / `Not for Sale`, repayment `Your Loan` / `OK`, tune
confirmation, Pak heading, and all earlier rendering/memory corrections remain.
Title artwork, keyboard, menu actions, save destinations, controller detection,
and saved names/formats are unchanged. No deletion or save operation is needed
to check a label; do not erase data merely to test its wording.

## Save compatibility

RC6-to-RC7 and RC7-to-RC6 save compatibility are expected: saved formats, names,
and save readers/writers are unchanged. No migration is required. Neither
loading direction nor an RC7 save/restart cycle is independently verified.
The user confirms repeated ordinary save/restart/reload cycles and all reported
fixes on their existing hardware playtests. That acceptance is retained; RC7's
new label changes are not part of those earlier sessions.
Keep original backups and use test copies. Do not use RC3 as a fallback because
its known town-loading memory failure remains in RC3 itself.

An Expansion Pak is required. EverDrive uses FLASHRAM (128 KB / 1 Mbit), with
RTC enabled. Earlier ROMs and saves remain preserved.

## Verification and limits

Ten focused construction checks pass across the two new batches. They cover
complete wording, actual pointer/count/copy instructions, relocated addresses,
display-buffer and stack bounds, unchanged memory requirements, retention of
all other cartridge resources, and complete original-ROM UPS reconstruction.
Both correction stages are constructed from committed sources.

The package checks bind both committed receipts, exact cartridge/patch hashes,
and standalone patch application against the original Japanese ROM. These
checks are not ordinary menu or original-hardware acceptance. Earlier native
tests remain evidence for their actual tested builds, not fresh RC7 execution.

All user-reported findings V1-01 through V1-23 are human-confirmed fixed, and
ordinary save/restart/reload is human-confirmed working. New source-identified
menu labels, broader untested gameplay, and remaining text/artwork review retain
their own verification limits. The historical full
test suite is not claimed passed. The unused/development scene-label lead has
not been translated by these two batches. V2 remains deferred.

## Local artifacts

ROM: `build/v1rc7/Animal Forest English V1RC7.z64`.
Patch-only archive: `build/v1rc7/V1RC7-patch.zip`.

The included standalone patcher accepts the verified original Japanese ROM,
not an earlier translation, and refuses to overwrite an existing output. It
never accesses saves or the Controller Pak.

Keep this candidate private. The archive contains a patch and original tooling,
not a ROM or loose game assets. Public-release approval and redistribution
review remain outstanding. Lucky-bag Japanese decoration remains intentionally
retained, matching the English GameCube artwork.
