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

## Native acceptance in progress

`tools/mail_glyph_creator_scenario.py` composes the source-bound Mom, event,
score, and ordinary NPC batches with every original assertion and one shared
checkpoint. Catalogue-four cases exercise the formerly missing bodies as
successes; catalogue-two unavailable-body rejection remains. Other rejection,
save/global restoration, allocation accounting, and checkpoint checks remain.

`build/smoke-mail-glyph-creator-01` runs with a 1,200-second bound, four MiB,
disabled audio, no screenshots, and no permitted test FlashRAM/Pak writes. A
fresh boot-to-town supplies the new ROM's own generated population. No state
from a different ROM is loaded. The native result is pending; partial logs do
not prove acceptance. The previously recorded ordinary-NPC capture rejection
remains open until current execution resolves it.

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

Collect the native batch and inspect complete outcomes, blank saves, checkpoint
restoration, and rejection evidence. Continue remaining native letter/general
text consumers and review, actual save/travel compatibility, ordinary gameplay,
editorial/presentation polish, patch-only release preparation, title-first images,
and the GameCube-style keyboard. Hardware requires actual hardware evidence.
No full-project regression or complete-gameplay claim is made here.
