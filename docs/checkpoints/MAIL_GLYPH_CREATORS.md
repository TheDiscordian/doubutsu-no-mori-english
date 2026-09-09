# Catalogue-four creator integration

## Implemented

The optional `--mail-glyphs` creator routes new ordinary NPC replies, Mom,
departed-villager, villager-event, HRA welcome/advice, and HRA score letters
through immutable catalogue four. Source approvals cover the original callers
and complete donor parts, including Mom `0136`, birthday `00F6`, score `003D`,
and composite footer `psz:004D`. All 114 Mom, 55 villager-event, and 21 score
templates have complete resources. The eighteen departed and twenty advice
templates retain their wording. No GameCube-only selectors are introduced.

The default creator still selects catalogue two. The compiled read-only
`af_npc_mail_catalog_id` marker binds the manifest's strict optional boolean to
the selected variant; changing the manifest alone cannot enable glyphs. All six
paths use the same compile-time selection. Catalogues two and three, native RNG,
gifts, paper, dates, queues, selected fields, publication gates, and saved layouts
remain unchanged. Legacy binaries require rebuilding against current sources.

The loader installer requires exact catalogue-four/font candidates before
publishing hooks or configuration. The final builder checks the actual installed
font, as do system-route installation verifiers. Each source/installation report
names the catalogue and its complete IDs. The combined counter follows those
verified routes and recognizes only registered mail glyph pairs; unused resource
presence does not count as translation. The denominator is unchanged.

## Verified host and build evidence

- `build/mail-glyph-creator-final-tests.log`: 57 tests pass in 63.861 seconds,
  including both complete creator variants and six installation tests. Full
  text/metadata, both capitals, all selected templates, all inherited names/field
  cases, resource failures, input/overlap guards, private publication, catalogue
  confusion, exact font dependencies, and actual ROM installation are covered.
- `build/mail-glyph-creator-sanitizers.log`: all 26 glyph-creator tests pass in
  53.999 seconds under AddressSanitizer/UndefinedBehaviorSanitizer. Interpreter
  leak detection is disabled; invalid-access checks remain enabled.
- `build/mail-glyph-creator-reader-regressions.log`: all 75 reader, format,
  catalogue, font, loader, layout, and accounting tests pass in 10.751 seconds.
- Independent creator images, relocation resources, and manifests agree in
  `build/mail-glyph-creator` and `build/mail-glyph-creator-repro`.
- The legacy score creator, fortune payment-recovery actor, renewal actor, and
  sale/Redd actor are rebuilt against the current resident. The complete ROM
  retains all 13,383 ordinary translation edits.
- `build/mail-glyph-progress-scenario-tests.log`: five tests pass in 7.676
  seconds, checking the actual ROM's new letter credits, unchanged denominator,
  complete native case sets, shared checkpoint, screenshot-free boot generation,
  and original score selection boundaries. Log SHA-256:
  `0d07eea509b6ea1f9262badc6176348e2ed2c227d0465cdeaf21df7b3ae363eb`.
- The final approval batch, `build/mail-glyph-creator-final-approval-tests.log`,
  passes all twelve tests in 15.083 seconds. It adds atomic rejection of missing,
  corrupted, incorrectly configured, or incorrectly approved installed fonts,
  and repeats every catalogue/system installation and progress/scenario check.
  SHA-256: `16eb087f7b146d626f3b3aa6fc3bb0d957473e28d25b57f5a6ccbf0eaef9dfa0`.

The initial host batch finds two fixture expectations tied to the old unavailable
footer: a new test uses a relative offset where its mock requires an absolute ID,
and an inherited test expects `004D` to fail even in catalogue four. The initial
installer batch configures the catalogue before reader/items, contrary to their
required order. Corrected fixtures pass in the complete 57-test rerun; production
validation is not weakened.

Log SHA-256 values, in the order above:

- `6128fced0a11ca8c8f08f1dad3eba8199c369e112851a3849c29575c92f6d15e`.
- `cd42eea9ca7ef43397759968c6c14d759c5fdd1c0362e3878902c3fd60edcd1a`.
- `1c277928ab6b24caae2dedbb129efcc747f21c307d6bedff96fa376fb7006371`.

## Artifacts

- ROM: `build/mail-glyph-letters-pilot/animal-forest-halfwidth.z64`, SHA-256
  `e176a72ef1fe3d180aeccc1d781a882672c77a34da56afc061946fe24b7ab736`.
- UPS: `build/mail-glyph-letters-pilot/animal-forest-halfwidth.ups`, SHA-256
  `df46c0e0c759ec0a56000f29b7c13b14f40a2bd054a43b414d3c256bac53f949`.
- Creator: 32,528 image bytes, SHA-256
  `f751d3d8584ca4cccbff4ea3365a77f691cb53c3fd9c7a7233b79fa3bad4d8f4`.
- Relocation: 560 bytes, SHA-256
  `bc304dc3f82d9b8fd133b3f113d374357f9b067ae578e5f654e54ba2830197e5`.
- Allocation: 38,447 bytes including unchanged 5,344-byte work and alignment;
  240 image bytes remain below the 32 KiB creator limit.
- Resident: 24,576 linked bytes in the unchanged 32,768-byte reservation, no
  linked headroom. This integration adds no resident instructions or saved bytes.
- Exact catalogue/font identities remain those in [MAIL_GLYPHS.md](MAIL_GLYPHS.md).

## Native acceptance

`tools/mail_glyph_creator_scenario.py` composes the source-bound Mom, event,
score, and ordinary NPC batches with every original assertion and one shared
checkpoint. Catalogue-four cases exercise the formerly missing bodies as
successes; catalogue-two unavailable-body rejection remains. Other rejection,
save/global restoration, allocation accounting, and checkpoint checks remain.

`build/smoke-mail-glyph-creator-01` runs with a 1,200-second bound, four MiB,
disabled audio, no screenshots, and no permitted test FlashRAM/Pak writes. A
fresh boot-to-town supplies the new ROM's own generated population. No state
from a different ROM is loaded. This run reaches message `07DD` and its matching
town checkpoint. All 114 Mom cases, seven rejections, one retry, and 735 helper
assertions pass. All 55 villager-event templates pass 110 original comparisons
and delivered readbacks, seventeen rejections, four retries, and 1,986 assertions.
Both completed helpers restore their own live save/globals and allocations.

Seventeen score templates `0034..0044`, including `003D`, pass both-capital
comparisons before the run reaches its process limit. The debugger connection
closes 1,209 seconds after the run manifest is created; the runner starts a
forced-kill timeout at `seconds+10`. No failing assertion is recorded, but the
score helper does not complete, NPC tests do not begin, and final checkpoint
restoration/graceful shutdown do not occur. This is not a passing overall batch.
FlashRAM remains erased and the Pak retains the blank fixture hash.

`build/smoke-mail-glyph-creator-02` continues only the unfinished score and NPC
groups, using the exact same ROM and the saved pre-test town checkpoint from
run 01. It has a 900-second bound and the same silence/no-write constraints.
It passes 41 complete score readbacks, then a Python `IndexError` stops the
twenty-first template's second capital state: the fixture's twenty-template
player mapping selects a nonexistent fifth player. `mailbox_position` cycles
the four actual players while preserving the original first twenty mappings.
The seven focused tests pass in 7.633 seconds and cover every player/mailbox.
This failure is in the test script, not evidence of a game crash.

`build/smoke-mail-glyph-creator-03` repeats only the unfinished groups with that
correction. All 21 templates pass 42 original comparisons, and 44 complete
readbacks include resource retry and original empty-room scoring. The batch
records 152 calls and 414 passing assertions, then one failed assertion at the
expected successful scheduler delivery. The entire save still matches the
pre-call fixture: neither mail nor the evaluation date is published. The
game-owned allocation probe returns zero; the successful case uses the original
NULL-game path. The cause remains unproven. This is not a passing scheduler
batch, and final checkpoint restoration/graceful shutdown do not occur.

`build/smoke-mail-glyph-creator-04` selects only NPCs from the same original
matching-town checkpoint. All 48 original comparisons, eight successive complete
creations, and eight rejections pass, including controlled allocation failure.
All 245 calls and 539 memory assertions pass. Complete English reconstruction,
metadata, RNG, native temporary fields, source saves, heap accounting, and
guards are retained. Live globals restore, the fixture allocation is released,
the checkpoint loads, the process survives, and shutdown is graceful. The old
ordinary-NPC rejection does not recur in this current build/fixture; that does
not establish the cause of the earlier rejection. No creator bytes are uploaded
by the debugger. Actual receipt/pending-loop and normal interaction remain.

FlashRAM and Pak hashes remain the blank fixtures in all three continuations.
The scenario generator's
`--groups` option retains every selected group's assertions and shared checkpoint;
completed Mom/event groups are not repeated.

Partial native evidence SHA-256:

- Run 01 results: `2027b920e2957aa42af3976b378112d1bd744cbaa9fd674b5e9ca92888f52469`.
- Run 02 results: `e5e161f32230f31ba3856384f9e491f83dd2253a1892f5bc0b01ec24621ebf26`.
- Run 03 results: `9d22b467af40b616bea2779102c28cb86983259e3399485a0ec1f088bd99a3f2`.
- Run 04 results: `7488660fa86b7884934d013abf1027a640b41f09bb6c2c3ca284bcc391d349ca`.
- Seven-test fixture log: `41507ef3ebca2211a32d5e46733e55906ef24ad2d3df4035558117d8a6e2544d`.
- Full post-scenario: `c4f970627339e9612f4b98a2e17b53ddf98a0c0e4c836a2949976f0726b3a0a7`.
- Boot scenario: `e9d9b23136eac346eb5ef3de87f560d321fa0ad9d843da467acbb9ce7b8cca73`.
- Erased FlashRAM: `b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260`.
- Blank Pak fixture: `ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51`.

## Reproduction

Use the [glyph framework recipe](MAIL_GLYPHS.md) for the current resident,
catalogue bundle, and font. Build the creator with all existing system flags
plus `--mail-glyphs`, output `build/mail-glyph-creator`. Rebuild fortune recovery,
renewal, and event actors against `build/runtime-module/module.json`.

Use the [complete score ROM recipe](ACADEMY_SCORE_LETTERS.md), retaining every
other flag and all translation inputs, with these substitutions:

| Option | Value |
| --- | --- |
| `--mail-catalog` | `build/mail-glyph-resources` |
| `--npc-mail-generation` | `build/mail-glyph-creator` |
| `--extended-font` | `build/mail-font-cartridge` |
| `--output` | `build/mail-glyph-letters-pilot` |

Generate `scenario.json` and screenshot-free `boot-scenario.json` with
`tools/mail_glyph_creator_scenario.py --output <scenario> --boot-output <boot>`.
Run the boot scenario and creator post-scenario in one silent isolated emulator,
or use a matching-ROM town checkpoint. Always select a fresh output directory.
Generated game content, ROMs, patches, and logs remain ignored.

## Required continuation

Diagnose the actual HRA scheduler's missing delivery in a bounded later bug
batch, without repeating complete template comparisons. Continue actual NPC
receipt/pending-loop and remaining native letter/general
text consumers and review, actual save/travel compatibility, ordinary gameplay,
editorial/presentation polish, patch-only release preparation, title-first images,
and the GameCube-style keyboard. Hardware requires actual hardware evidence.
No full-project regression or complete-gameplay claim is made here.
The [flooring/wallpaper build](FLOOR_WALL_NAMES.md) retains every glyph/runtime/
letter file and supplies the next complete ROM with seventy additional names.
