# Combined private artwork playtest package

## Current package 05

The local bundle is `build/releases/v1-artwork-playtest-05.zip`, SHA-256
`0d31a9e9f10e9c91106338ddcbc38f0bd16abb345ed8657b769af6c9b765d483`.
Cartridge source revision is `766a1d817814e55bc8e0f8232d2005ba9e15d486`;
packaging source revision is `067a71d3f23232891ea215d6c0f97f1de270aba9`.

It reconstructs `build/title-civic-interior-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256 is `a8072a76783317215ae85afbf31cca77422d5b783512194d8269004f31073780`;
UPS SHA-256 is `7398d8d3c3bd3b7e234057daabbf61684811e367be583ec4d82045dae2d624bd`.
Canonical bundled title-report approval is
`f851e26b4b448f030b0431e9245f6c6ba675a4cdca0d34368ad4f9ddbde57e19`.

All package-04 features remain, with the two English police-interior posters and
postal MAIL bag from [the civic-interior batch](CIVIC_INTERIOR_ARTWORK.md).
An Expansion Pak is required. Lucky-bag Japanese decoration remains intentional.

Both current packaging tests pass in 3.699 seconds. The final archive itself
also passes a separate nine-member/checksum inspection and standalone patcher
execution from isolated extraction. It reconstructs the approved 32-MiB ROM,
refuses a second write, and leaves the original ROM unchanged. No ROM, disc,
save, or private absolute path is bundled. Prior packages remain untouched.
The complete [28-stage public-image rebuild](V1_REBUILD.md) matches this ROM/UPS
and passes the same package approval with its actual compiler-report provenance.

This is a private candidate, not hardware certification or a public release.
Ordinary room appearance and the existing tutorial/menu/editor/transaction/
save/restart/travel/event/hardware acceptance remain playtest work. The incomplete
warning drawing probe remains explicitly unverified; no confirmed game defect
is waived by packaging.

## Retained package 04 record

The current local bundle is `build/releases/v1-artwork-playtest-04.zip`, SHA-256
`2fac4233c4ffa8c1a73a4f8f3c2936f0a1287d18ea9a8f757337fba1c23a801e`.
Its cartridge source revision is `76f49551ee106953ba1afb61566b599ccc5ad12c`;
packaging revision is `998d6738fee40ac3bbc6f04bf30b4411e8ffac85`.

It reconstructs `build/title-shop-interior-combined-01/animal-forest-title-preview.z64`.
ROM SHA-256 is `d7fbbffc85eb7c311f980c3945cf035de136b130d9fee6214ad096d60b8c8585`;
UPS SHA-256 is `4dca9b30625ea76350dcc3198835ad9d7b6d226cda77bc0828519fa630e5a31b`.
The canonical bundled title-report approval is
`79b6ee72a933a52a72b918f9c6099ece453b04babe0a2e6d7e9ba81d6017b029`.
An Expansion Pak is required. All package-03 features remain, with seven exact
English GC [shop-interior sign images](SHOP_INTERIOR_ARTWORK.md) added.
Lucky-bag Japanese decoration is intentionally retained, not a pending choice.

Both current package tests pass in 3.797 seconds. The final archive's own nine
members and hashes are separately checked, and its extracted standalone patcher
reconstructs the approved 32-MiB ROM. A second write is rejected; the source ROM
is unchanged. No ROM, disc image, save, or private absolute path is bundled.
The public-image 27-stage rebuild also passes the same packaging approval while
retaining its distinct actual compiler-report checksum, as recorded in the
[rebuild checkpoint](V1_REBUILD.md).

This remains a private playtest, not a completed public release or hardware
certification. Ordinary shop-room appearance joins the existing gameplay,
save/restart, menu, event, and original-hardware acceptance limits. No confirmed
game defect is waived. The old package and all user saves remain untouched.

## Retained package 03 record

The local patch bundle is `build/releases/v1-artwork-playtest-03.zip`.
SHA-256: `724ddcaec142a1dddf5708a240c3ecd04ba0a58a059121877c4b8ac71566bebe`.
Its cartridge revision is `8222cb3c23c79813b5f45923a03e2537e1b23c07` and its
packaging revision is `1865f2fc6145622f24cc3bb8594ccb3128069c21`.

It reconstructs the complete combined cartridge at
`build/title-stall-combined-01/animal-forest-title-preview.z64`, SHA-256
`128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19`.
An Expansion Pak is required. The corrected four-MiB v0 package and all earlier
ROMs remain untouched. This is an experimental private handoff, not completed
v1 or a public release.

Both focused package tests pass in 3.796 seconds. Checks cover all nine allowed
members, member hashes, exact ROM/UPS/report identities, memory requirements,
rejection of unknown reports/revisions, absence of ROMs/saves/private absolute
paths, and actual standalone patcher execution in an isolated extraction folder.
The included patcher also passes a separate check extracted from the final
archive: it reconstructs the approved ROM, refuses a second write to the same
output, and leaves the original ROM unchanged.

The bundle includes Nookington's doorway/clearance details, both dump signs,
source-matching GC fishing and fortune props, countdown minute/second labels,
and the compact GC-style shared festival stall,
along with all earlier title, keyboard, screen, text, and conversation work.

The manifest and standalone notes retain incomplete embedded-warning native
drawing, ordinary menu/transaction/save/restart/hardware acceptance, and remaining
festival-stall appearance and lucky-bag writing as explicit limitations. The
reflected stall placement is an adaptation, not the exact separate GC mesh.
Successful birthday and
gyroid drawing checks do not claim ordinary navigation or save acceptance.
Continue remaining decorative artwork and respond to concrete playtest bugs;
do not repeat passing package, title, or conversation checks without a relevant
change.
