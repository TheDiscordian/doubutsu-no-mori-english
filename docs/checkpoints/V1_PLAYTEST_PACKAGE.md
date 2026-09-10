# Combined private artwork playtest package

The local patch bundle is `build/releases/v1-artwork-playtest-01.zip`.
SHA-256: `e2d288f734571203702504f972115d8eb3734f0afd363186a3ce7bf1e3462f4a`.
Its cartridge revision is `a5e9eebbf3e36e736e6d806f5288623769b5b0bf` and its
packaging revision is `67a175391a88c9ff8263aba4cc6032fa2a63a4a5`.

It reconstructs the complete combined cartridge at
`build/title-gyroid-service-combined-01/animal-forest-title-preview.z64`, SHA-256
`da66a789341307c625da130ae11e20609b9a023fca82712f303fc59fe95deb94`.
An Expansion Pak is required. The corrected four-MiB v0 package and all earlier
ROMs remain untouched. This is an experimental private handoff, not completed
v1 or a public release.

Both focused package tests pass in 3.647 seconds. Checks cover all nine allowed
members, member hashes, exact ROM/UPS/report identities, memory requirements,
rejection of unknown reports/revisions, absence of ROMs/saves/private absolute
paths, and actual standalone patcher execution in an isolated extraction folder.
The included patcher reconstructs the approved ROM, refuses a second write to
the same output, and leaves the original ROM unchanged.

The manifest and standalone notes retain incomplete embedded-warning native
drawing, ordinary menu/transaction/save/restart/hardware acceptance, and remaining
decorative Japanese artwork as explicit limitations. Successful birthday and
gyroid drawing checks do not claim ordinary navigation or save acceptance.
Continue remaining decorative artwork and respond to concrete playtest bugs;
do not repeat passing package, title, or conversation checks without a relevant
change.
