# Current V1 patch package

Package the completed `build/v1-current-01/final` output as V1RC8, without
rebuilding or re-testing historical candidates. Bind the exact approved current
ROM, UPS, completed build report, and committed recipe identity. Read no RC ROM,
save, or intermediate stage artifact. Preserve all existing outputs.

`tools/package_v1_current.py` writes a named local ROM and patch-only archive to
a fresh `build/` directory. Require clean committed source, including documents,
and record the distinct build/packaging revisions. Only after the archived
standalone patcher reconstructs the full candidate from the original ROM may
the handoff directory be created. A failed patch application publishes nothing.

The ZIP contains exactly ten files: UPS, manifest, README, SOURCES, TOOLCHAIN,
BUG_REPORT, tooling licence, standalone patcher, binary helper, and SHA256SUMS.
Checksums cover the nine other members. All relative Markdown links resolve
within the package; applying the patch has no private documentation dependency.
The optional compiler/source workflow remains distinct from patch application
and explicitly requires source access and separately supplied inputs.

RC7-to-RC8 and RC8-to-RC7 save compatibility are expected, not independently
executed. No migration or saved-format change is introduced. Retain human
acceptance for all reported fixes and repeated ordinary save/restart/reload
without inventing fresh RC8 execution. Keep untested cases and redistribution
requirements explicit. Publishing a patch or changing repository visibility is
not part of packaging.

Verification is limited to the new package: exact payload and build identities,
offline-document links/checksums, compatibility/evidence scope, rejection of
unknown or incomplete build reports, and one archived-patcher execution. Do not
rerun correction tests, old packages, full builds, or gameplay for this change.
