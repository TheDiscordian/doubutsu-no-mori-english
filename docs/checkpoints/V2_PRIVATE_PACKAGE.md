# Private V2 offline package work record

## Completed handoff

The V2 Development patch is packaged locally at
`build/v2-private-bundle/V2-Development-patch.zip`. The existing V2 ROM remains
`build/v2-keyboard-05/Animal Forest English V2 Development.z64`; it is not
rebuilt, renamed, or changed by packaging. V1 Final, previous builds, and the
user's saves remain intact. This is a private offline handoff, not another RC
or a public release.

- Archive SHA-256: `911e7ddc3d887edc3c40fa5b9eb84a7c6d85db9e15b5cf8b885bfc02aeb4e8a0`.
- ROM SHA-256: `085e3dfc10cc03e591ce4197d7f3841c45e3fba3b51344d1be58c87cda2fe9d9`.
- UPS SHA-256: `cbcee703fcf3f3957a112449a11e0718ac1a134fb440d2afddcfc6705228c888`.
- Packaging revision: `d0e784c946ff5cb0ffcfb3380be024fbffe234be`.
- Cartridge-source revision: `586d5abe50826358a39868e1d50dbe60f93bb145`.
- Build-receipt SHA-256: `0ed07e68b807f2e48efc66270ce4ea0c4c75723aed46dea0ee6156dd352ecdfd`.
- Verification receipt: `build/v2-private-bundle/verification.json`.

## Fresh evidence

`python3 -m unittest discover -s tests -p 'test_package_v2.py' -v` passes three
new package checks in 0.497 seconds. They bind the current ROM/patch, committed
builder sources and documents, archive allowlist, every member checksum, and
save/hardware/publication limits. Changed construction receipts and committed
source mismatches are rejected. Offline document links resolve inside the
archive, and the documentation contains no private machine paths.

`python3 tools/package_v2.py` then runs the archived standalone patcher from a
temporary extracted bundle, using the original Japanese ROM. The patcher
reconstructs the complete current V2 cartridge, checks its hash and N64 boot
checksum, and succeeds before the final ZIP is written. The patcher is the
existing standard-library implementation, not a new patch format or a private
checkout dependency. No emulator, old build, accepted save scenario, or
historical compilation chain is run.

The eleven-member ZIP contains eight guide/source/tooling files, one UPS,
one manifest, and a checksum list. It contains no ROM, save, emulator state,
or loose game asset. The patch applies to the supported original Japanese
ROM, not incrementally to V1. Original input and destination overwrite
protections are retained by the existing patcher.

## Preserved limits

Expansion Pak, 128-KiB FlashRAM, and RTC are required. V1 Final → V2 and
V2 → V1 Final save compatibility are expected without migration, not claimed
as independently executed. The manifest separately records the earlier normal
name-entry evidence and the final label-removal build's artifact checks.
Packaging success is not gameplay or original-hardware certification.

The offline guides describe source reproduction without claiming a new
end-to-end execution of the historical construction chain. Licensing and
publication decisions remain separate from successful technical packaging;
no public upload or repository visibility change is made.

The local V2 implementation and offline handoff are complete. Preserve the
artifacts and evidence. Further work needs a concrete correction or playtest
finding; do not generate more packages, replay tests, or broaden the artwork
scope simply because the full-project goal still awaits broader acceptance.
