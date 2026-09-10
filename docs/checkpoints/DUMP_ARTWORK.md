# English dump sign checkpoint

Both seasonal signs use the exact supplied GameCube "Dump" artwork, with native
models, palettes, fences, item handling, and the Monday/Thursday collection
schedule unchanged. The current separate cartridge is
`build/dump-artwork-01/animal-forest-halfwidth.z64`, SHA-256
`5c5206c9a8ee548900ba264276f5052a4ed8b5a13803ffcf1a6b44c880f17226`;
its UPS SHA-256 is `08013de49c44790a2efbc751b4fd51ddad2428ca204c0b8ef937f7ccf88d8bc2`.

The retained title combination is
`build/title-dump-combined-01/animal-forest-title-preview.z64`, SHA-256
`9f734ba89b2456e5dce7b79c6cafe33b3017dd22e8d9cec02e5eb70c1533b560`;
its UPS SHA-256 is `c10c81ae66e3690f5cbfccd28a86bac6f10110b62306323f49dcea2e8cff14fe`.
It requires an Expansion Pak and retains all previous conversation, menu, text,
keyboard, title, and Nookington detail work. The existing private package remains
unchanged while the next artwork batch is assembled.

Four focused checks pass across the bounded batch. The first pass verifies full
source pixels/colours/readers and complete cartridge retention, but its accounting
check finds that bitmap kanji cannot be encoded by the native dialogue codec.
The ledger now accepts verified Unicode artwork transcriptions with source-image
hashes. The affected check passes in 0.465 seconds, the added kanji/negative test
in 0.121 seconds, and all sixteen existing counter regressions in 0.016 seconds.
No ROM change is required for that accounting correction. The title-combination
check passes in 8.105 seconds.

The checks bind actual GC texture fixups, all 88 native vertex uses, both retained
and active streamed copies, all 92 bounded building streams, every other resource,
the retained Nookington accounting profile, and UPS reconstruction. Upright native
and English projections are inspected, including both English seasons. Ordinary
scene/hardware acceptance is not claimed; no new native harness is needed for
the unchanged graphics commands.

The full counter verifies this cartridge and measures 752,002 replaced source
characters out of 752,024. Both original signs contribute four source characters
(`ゴミ 月木`), all replaced by the source-matching English design. The same
twenty-two structural-tail characters remain, and duplicate object copies add
no source weight. See the [specification](../../specs/DUMP_ARTWORK.md).

Continue seasonal fishing and festival props. The six inspected shrine atlases
contain no lettering requiring translation; preserve the native shrine. The
fortune booth and food stall differ substantially from their GC counterparts,
so their atlases are not safe whole-image swaps. The English GC fishing barrel
removes the Japanese owner name, but its T3 atlas retains `本部`; inspect the
actual model before assuming that lettering is a visible English-GC omission.
