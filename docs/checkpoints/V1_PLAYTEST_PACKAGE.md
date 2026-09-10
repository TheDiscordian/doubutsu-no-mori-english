# Combined private artwork playtest package

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
