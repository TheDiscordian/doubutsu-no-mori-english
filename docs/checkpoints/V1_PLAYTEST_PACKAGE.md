# Combined private artwork playtest package

The local patch bundle is `build/releases/v1-artwork-playtest-02.zip`.
SHA-256: `d0763dcc0a963bcb29f2e06c41412760a5055740fdcea1ceeb7fa1c1c5fa1dd5`.
Its cartridge revision is `991a5d6ccd5144a73baf1faca5b39cebbf79eebe` and its
packaging revision is `fd08f1fbd751975533a5dbf98717c7845f8fc1a4`.

It reconstructs the complete combined cartridge at
`build/title-countdown-combined-01/animal-forest-title-preview.z64`, SHA-256
`6be7c2a514574a3c9f7eba0e00c45d84cb6f83866b39cd7d1de0b2db8c1f73b7`.
An Expansion Pak is required. The corrected four-MiB v0 package and all earlier
ROMs remain untouched. This is an experimental private handoff, not completed
v1 or a public release.

Both focused package tests pass in 3.749 seconds. Checks cover all nine allowed
members, member hashes, exact ROM/UPS/report identities, memory requirements,
rejection of unknown reports/revisions, absence of ROMs/saves/private absolute
paths, and actual standalone patcher execution in an isolated extraction folder.
The included patcher reconstructs the approved ROM, refuses a second write to
the same output, and leaves the original ROM unchanged.

The bundle includes Nookington's doorway/clearance details, both dump signs,
source-matching GC fishing and fortune props, and countdown minute/second labels,
along with all earlier title, keyboard, screen, text, and conversation work.

The manifest and standalone notes retain incomplete embedded-warning native
drawing, ordinary menu/transaction/save/restart/hardware acceptance, and remaining
festival-stall and lucky-bag artwork as explicit limitations. Successful birthday and
gyroid drawing checks do not claim ordinary navigation or save acceptance.
Continue remaining decorative artwork and respond to concrete playtest bugs;
do not repeat passing package, title, or conversation checks without a relevant
change.
