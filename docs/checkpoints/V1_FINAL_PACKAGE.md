# V1 Final handoff

## Artifacts

- Local ROM: `build/v1-final/Animal Forest English V1 Final.z64`.
- ROM SHA-256: `0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf`.
- Patch archive: `build/v1-final/V1-Final-patch.zip`.
- Archive SHA-256: `e00bee7961c09c154db91d6020128d6a4f71ff9739bd4abd114889f7bf4c8aa1`.
- UPS SHA-256: `acdfe82eae085337cc23d261154fbd06004f56d234b0a76587d2e6885047ae47`.
- Final-build revision: `5dcc07ed779f18ba1973e055e67c65b9855190d5`.
- Packaging revision: `1d1281805cfa53935e3a35357625e8eec2848c0e`.
- Packager SHA-256: `48faa525a93695f84230d26fbc2bb0350b1e18cf1a53df2ee732ed0e55fd72d4`.
- Manifest SHA-256: `c12af94a88255b5bcd63efe088bdd794496b7033cab214c1b409e68e69b4834b`.
- Verification SHA-256: `ef5f3f44a0240f93b4802f2e46e928cf5a3c94f024a835994c57c372fd5d7f22`.
- Packaged README SHA-256: `55a7ee5ab287fd983d53b552e45d73ddeb9df323ed121782730de33a42aaa613`.

The ROM is the completed diagnostic-stage output. It includes all tracked
V1-01 through V1-29 implementations, all RC8 content, the English title and
screen/building artwork, and the accepted GC-style keyboard. Packaging makes
no additional change to game content. This is the requested `V1 Final`, not
another RC. The package and repository remain private; no public upload occurs.

## Final-package verification

Three new focused package checks pass. The first invocation passes the two
rejection/document checks but fails archive preparation because the new
packager expects the generic UPS filename. The development builder actually
writes `animal-forest-diagnostic-text.ups`. After correcting that input name,
only the affected archive/compatibility test is rerun; it passes in 0.435 seconds.
No game defect or changed cartridge is involved in that correction.

The checks cover the exact final ROM and patch, bound completed receipts and
committed builder, all 29 finding IDs, the thirteen additional literals,
retained human-acceptance scope, compatibility warnings, ten ZIP members, nine
member checksums, bundled-source hashes, offline links, and the final source-
build output directory. Unknown/altered receipts and private machine paths are
rejected. The optional toolchain guide now describes the final diagnostic
suffix, its output, and the actual separate 109-stage evidence.

From clean committed packaging source, the archive's own standalone patcher
executes once in an isolated temporary folder. It recreates the exact complete
32-MiB final cartridge from the verified original and validates the N64 boot
checksum. The handoff directory is written only after this succeeds. No old
ROM is read, no historical build is replayed, no emulator runs, and no accepted
gameplay test is repeated. Only the recorded baseline receipt is consulted for
construction provenance.

## Compatibility and limits

Expansion Pak, 128-KiB FlashRAM, and RTC remain required. RC8-to-final and
final-to-RC8 saves are expected compatible without migration: only thirteen
in-place literals differ, with no instruction, pointer, allocation, or save-code
change. Those exact loading directions are not independently tested. Preserve
save backups and associate a copy with the new EverDrive ROM filename. RC3 is
not a safe fallback for the known existing-town loading defect.

Human acceptance of all reported fixes and repeated ordinary save/restart/reload
remains complete. It is not relabelled as a fresh final-ROM hardware session.
The [final guide](../V1_FINAL.md) retains untested broader gameplay, source-label
appearance, individual layouts, stall placements, and historical-suite limits.
No exhaustive whole-game, seasonal, or hardware certification is claimed.

Neutral tools, room surfaces, effects, and fish/insect artwork are excluded
from further speculative V1 review by the user's direction. A read-only decoder
job finishes before that direction is processed; its ignored previews under
`build/remaining-artwork-review-01/` are not visually reviewed, credited as
translated, or promoted into remaining work. The uncommitted sweep script is
removed. No source artwork or game resource is changed.

Public upload/source publication and the recorded redistribution decisions
remain separate from this completed local handoff. V2 remains deferred.
