# V1RC8 combined private package

## Deliverable

- ROM: `build/v1rc8/Animal Forest English V1RC8.z64`.
- ROM SHA-256: `2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4`.
- Patch archive: `build/v1rc8/V1RC8-patch.zip`.
- Archive SHA-256: `302b5c76ad5712d8de0f99f3d84ae877319557fb0283d3f1ee411c488b87cf51`.
- UPS SHA-256: `c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769`.
- Packaging revision: `25bfda63527e4a18b5f1d5081fcebab80fd35b06`.
- Packager SHA-256: `97f68f0b3916136e432b4bd333cbbf02730e6b5c059292e0ead2af4621581208`.
- Manifest SHA-256: `dcc80e29feb8290792b3a3f0306ccc25a939b3c306b8c49258c07943521cc3ca`.
- Verification SHA-256: `46076b8f7e26e2f6adc52020701aa98624cefc9ea38f7fa9f75b983a98cbd490`.
- README SHA-256: `8e787a7263a3340e1ec3e9c9d5a0eb7dc5ab14f0040a081674e6d3e461eac928`.

The cartridge is the completed [current V1 build](CURRENT_V1_REBUILD.md), with
all RC7 corrections and V1-28's 76 English scene/loading/settings strings.
Packaging changes no game content. The exact completed report, build revision,
and committed recipe hash bind this handoff; no old intermediate ROM is read.

## Completed package checks

Three focused checks in `test_package_v1_current.py` pass in 0.443 seconds:

- Exactly ten members, nine payload checksums, exact current ROM/patch/report
  identities, and included-document source hashes.
- Self-contained relative Markdown links, the offline compiler/source guide,
  absence of private machine paths, and rejection of missing local guide links.
- Rejection of unrecorded/incomplete reports, correct RC7 compatibility notes,
  and human acceptance separated from unexecuted RC8 gameplay.

The committed packager executes the ZIP's standalone patcher from an isolated
temporary folder. Against the original Japanese ROM, it reconstructs the exact
32-MiB current candidate with valid boot checksum. Only after success are the
named ROM, ZIP, manifest, verification, and README written to the fresh output
directory. No older package, candidate, save, or SD-card file changes.

No old-build tests, correction replays, full suite, emulator, or gameplay
scenario runs. The new package check and single standalone application are
the complete verification scope for this packaging change.

## Offline documentation

The archive includes README, SOURCES, TOOLCHAIN, and BUG_REPORT alongside the
UPS, manifest, tooling licence, patcher/helper, and checksums. It contains no
ROM, save, state, or loose game asset. Patch application needs Python 3 and the
original ROM, not a compiler, GameCube disc, network, or private source access.
The optional source-build instructions clearly distinguish source prerequisites
from patch application and retain the actual separate build evidence.

This closes the private-guide-link dependency for the distributable package.
It does not publish the repository, patch, or third-party inputs and does not
resolve redistribution permission. The package-specific README and compiler
guide use ZIP-relative links; the packager verifies the complete shipped set.

## Compatibility and acceptance

RC7-to-RC8 and RC8-to-RC7 save compatibility are expected, with no migration or
saved-format change. These particular directions are not independently tested.
Expansion Pak, 128-KiB FlashRAM, and RTC remain required. Save backups and all
older candidates stay intact; the known-broken RC3 is not a fallback.

All reported V1-01 through V1-23 corrections, earlier Nook-loop/Shrine findings,
and ordinary save/restart/reload retain the user's hardware acceptance. New
scene-menu wording is not relabelled as part of those sessions. Unreported
seasonal/travel/Pak cases and remaining artwork/text review retain their actual
limits; they do not require another test of unchanged accepted fixes.

## Remaining work

Address any new concrete bugs and genuinely unreviewed wording/artwork. Preserve
the completed scene-menu and neutral-image reviews. Public distribution requires
review and approval; the source remains private. V2 stays deferred. Do not
rebuild or re-test this package merely to refresh its evidence.
