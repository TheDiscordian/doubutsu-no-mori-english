# Flooring and wallpaper checkpoint

## Installed content

The complete ROM at `build/interior-items-pilot/animal-forest-halfwidth.z64`
installs seventy additional complete GameCube names: 37 floors and 33 walls.
All earlier 13,383 ordinary edits and 2,713 wider item candidates retain exact
content and provenance. Ten newly approved names also fit native ten-byte
fields, giving 13,393 ordinary edits and 2,783 wider item slots. The other sixty
names remain complete in the sixteen-byte resource; no truncated replacements
are supplied for smaller callers.

Only DMA files `010F4000` and `02A00000` differ from the preceding complete
glyph ROM. Every other extracted file, runtime instruction, letter catalogue,
font, and translation remains unchanged. The UPS reconstructs the complete
output from the verified original ROM. Generated game content remains ignored.

The [name specification](../../specs/FLOOR_WALL_NAMES.md) records semantic
approval and capacity boundaries. Bathhouse/western and old-wood/backyard design
changes remain withheld. This is a name import, not artwork replacement.

## Executed checks

- `build/interior-items-final-tests.log`: forty tests pass in 14.350 seconds.
  The batch covers native/reference identities, both capacities, every earlier
  candidate, exact installed names, every DMA file, resource reconstruction,
  complete patch application, loader bounds, and item-field consumers.
- `build/interior-items-final-scenario-tests.log`: eleven tests pass in 15.323
  seconds. The explicit reference-bank selection produces the same native
  scenario as the independent filtered input. All loader boundaries and
  rejection cases remain. This batch also tests the corrected twenty-first
  score case and split letter groups.
- `build/smoke-interior-items-01`: all 189 native calls and 181 memory assertions
  pass. The batch covers the complete 87 approved floor/wall reference names,
  including the seventy new names, ten new original-width loads, all item-group
  boundaries, unaligned destinations, invalid capacities/headers, disabled
  resources, and adjacent guards. The checkpoint reloads, its scratch assertion
  passes, the process survives, and shutdown is graceful. FlashRAM stays erased
  and the Pak retains its blank fixture. The emulator is silent and takes no
  screenshots; there is no ordinary gameplay or hardware claim.

The initial identity batch also passes all 28 tests in 2.491 seconds. There is
no full-project regression claim from these focused checks.

## Artifact hashes

| Artifact | SHA-256 |
| --- | --- |
| Complete ROM | `99d8599b02ef095143d73c7246fe1b9b76ee1c44109bd45b251a104f8fdf19bd` |
| UPS | `3700163b3dce10b4025e2baa880bb8eb708d7c73093100e22ed16b88d0d44310` |
| Wider item resource | `755dcbe9c03c3ac76a3d6142e03782037268b7fb3b79cea7a3b4d70d1dc17752` |
| Forty-test log | `f1d2ecaf55ad31e541accee9c1e083521fa44462db6fe0374fc5446d72d72b7a` |
| Eleven-test log | `75999452959967d016bfc3ec6fad7661ff403a8fa41a524fb77c03a26831d794` |
| Native scenario | `ce04e399c11d9e0244008bedbc0b2242a465dc7e33284cafab50a6bbaa7b85e0` |
| Native results | `d574de0284160e8127c125848f7c5d119b1b92b49f172b4725834062486331e1` |
| Erased FlashRAM | `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260` |
| Blank Pak | `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51` |

## Reproduction

Run `tools/extended_items.py` with the verified native `--rom`, outputting
`build/interior-items-resource`. Run `tools/reference_candidates.py` with the
same ROM, `--english-runtime`, `--runtime-module build/runtime-module`,
`--english-dialogue-dates`, `--english-fortunes`, `--english-resetti-replies`,
`--english-shop-units`, `--english-resident-words`, `--english-shared-npc-words`,
`--english-credits`, `--extended-font build/mail-font-cartridge`, and output
`build/interior-items-candidates`. Keep the default complete draft set.

The [complete glyph recipe](MAIL_GLYPH_CREATORS.md) retains all enabled runtime,
letter, and English flags. Change only these content/output options:

| Option | Value |
| --- | --- |
| `--translations` | `build/interior-items-candidates/translations.json` |
| `--extended-items` | `build/interior-items-resource` |
| `--output` | `build/interior-items-pilot` |

Generate the native scenario with `tools/extended_items_test_scenario.py`, using
the completed ROM, its `runtime-module.json`, the new resource's `names.json`,
and `--reference-bank item_26 --reference-bank item_27`. Add each original-width
case with `--native-item`: `0x260D/0x2613/0x262E/0x2631/0x270D/0x270E/0x2713/
0x2715/0x2716/0x2728`. Use a fresh isolated output directory, a 600-second bound,
and `--no-initial-screenshot` in the silent emulator runner.

## Required continuation

Continue remaining letter consumers, item identities, general strings, and the
five native diagnostic scripts. The complete glyph NPC creator passes in its
current matching-town batch; its actual receipt/pending-loop and ordinary mail
interactions remain. The current HRA scheduling assertion needs a bounded
diagnosis in the later combined bug pass; do not rerun completed template cases.
Expand remaining wider name destinations, preserve complete GameCube wording
and timing, finish save/travel/gameplay acceptance and review, prepare a patch-only
release, then complete title-first artwork and the GameCube-style keyboard.
Original hardware requires actual hardware evidence. The full goal stays active.
