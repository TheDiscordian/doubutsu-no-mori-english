# Complete seasonal English text, publication, and reading

## Completed source work

All 41 native seasonal/general board bodies `01A4..01CC` have complete reviewed
English definitions in `tools/notice_seasonal.py`: 21 unchanged supplied English
references, fifteen native-specific reference adaptations, and five original
translations. The [seasonal specification](../../specs/NOTICEBOARD_SEASONAL.md)
records calendar, venue, speaker, field, publication, and presentation constraints.
The source review retains both native moon-viewing dates, April 20th spring
sports, October fall sports, every-Saturday-in-August fireworks, White Day,
Doll Festival, Children's Day, and the shrine.

`python3 tools/notice_seasonal.py` generates the source-bound review and 82
complete body/capitalization record models at `build/noticeboard-seasonal/review.json`.
Its SHA-256 is
`be21b930f1a0e12ddf15e23b0d88c454673f05738280b544f7886759a9f4c4c4`.
Each entry records its source/reference/output identity and original posting
date. The longest expanded sample is 170 bytes. The five original bodies and
three complete rewrites retain six explicit lines each; span adaptations preserve
their matched reference's manual newline counts.

All six review/model tests pass. All seven C page-planner tests pass, including
the new 82-case comparison against independent expected rows. Logs are
`build/noticeboard-seasonal/review-tests.log` and `page-tests.log`.
One initial test incorrectly required every English notice to exceed 96 bytes;
the 96-byte sports timetable disproves that assumption. The corrected test checks
the exact complete body and capacity without imposing an unnecessary minimum.
No translation was shortened to satisfy a test.

## Installed cartridge and complete runtime

`build/notice-seasonal-pilot` installs all 41 complete bodies and every earlier
translation resource. Creation captures complete town/shop fields and native
lunar/sports dates in private storage. The native publication bridge keeps the
original timestamp and advances the saved cursor only after successful writing.
The complete reader retains initial/treasure/manual text, two caches, and all
full-body pages. The combined counter verifies installation before crediting
the 41 Japanese source IDs; sample names do not create extra name credit.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Complete ROM | 33,554,432 | `20fa1cbbccadb47e38c370cce4c314f5381b286141b4aed62b541618b496fa00` |
| UPS | 4,492,506 | `59db1da145db43a74e39d4265b08aa84545e362d999b2007efefa8a4d3c46e70` |
| Creator image | 58,144 | `2598d8ed5cc35e06a40e24aab1db93fbca2f8cdab00b752bd91ba7af5cd93637` |
| Creator relocations | 848 | `95f09d4b0c6ea100caa03cf798ee217836670c4e102ab5538dc2cb7be74b34a1` |
| Reader image | 24,304 | `4c90884012ca787e44b20e5052e984c2f1b39e1d9e184da3094d9af283a8f428` |
| Reader relocations | 720 | `d407cdd681b0ae42d48f4b0e29b072b0797519829ef7bc6309d28b8ecdc696ad` |
| Native bridge plus padding | 448 | `aed66e47ee62fa79e6d0cb0a0417a598fad8fc10f865d2d2398e3a426bc58b3a` |

Independent `creator/creator-repeat`, `reader/reader-repeat`, and
`owner/owner-repeat` builds agree on image, relocations where applicable, and
manifests. The 32,768-byte resident module remains
`493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6`;
the bootstrap remains
`9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f`.
The creator workspace remains 5,344 bytes, and its new complete loader request is
64,351 bytes including alignment. The creator's own compiled frame is 96 bytes.
The reader reserves 20 KiB of extra submenu space, 4 KiB more than the treasure
profile, for a 234,880-byte dominant pool total. Four-MiB bounds and saved layout
remain unchanged; actual new-pool allocation is not yet native-tested.

The generated readonly body data is 6,143 bytes, SHA-256
`003e03aed8eada220c3eaf333590454cd5021293effd12dfdddf80f3f577f398`;
the 492-byte entry table is
`4550159bc22df0f52dae5f295193865a40817fdcfef35111eeabf789a97472ae`;
the 64-byte full shop-name table is
`87224fa48dd9e49182a58c945fe4af2dac5293838f671ed7f7b1a8ecb63f831e`.
Generated reference content remains ignored, not committed.

## Passing checks and limits

All 54 creator, six decoder, and fourteen combined-reader host tests pass.
The same tests pass under address/undefined-behaviour sanitizers. The suite checks
all bodies/capitals, shop tiers, full lunar/sports date fields, fallback year
contracts, corrupted body data, overlap/atomic output, inherited letter/treasure
dispatch, full pages, mixed caches, and retry without changing saved text.
An initial mixed-cache assertion selected an older cache entry by pointer alone;
the corrected test matches the complete saved identity, as the real reader does.
The displayed production text required no change.

Six creator artifact checks and eleven owner/reader/installation/accounting
checks pass. These verify independent builds, readonly resources at three bases,
exact native reference/patch inventories, new pool arithmetic, rejected partial
installation, unchanged earlier resources, the UPS round trip, and exact combined
source-ID credit. Five old treasure creator, five owner, and five frozen native
evidence tests pass without replaying completed native batches.

Logs under `build/noticeboard-seasonal/` include `creator-tests.log`,
`decoder-tests.log`, `reader-tests.log`, their `*-sanitizer-tests.log` equivalents,
`creator-artifact-tests.log`, `install-tests.log`, `reader-build.log`,
`reader-repeat-build.log`, `owner-repeat-build.log`, `full-build.log`, and
the three `treasure-*-retention-tests.log` files. The complete native treasure
owner/reader evidence remains in the [treasure checkpoint](NOTICEBOARD_TREASURE.md).
Calendar mocks are call-contract tests, not actual calendar execution. No native
seasonal, normal scheduling, new pool, save/reload, or hardware proof is claimed.

## Reproduction

Use the current manifest `build/notice-seasonal-runtime/module.json`. Compile the
complete NPC creator with all preceding flags and `--notice-owner --notice-seasonal`.
Its approved article input remains `build/noticeboard-treasure/articles/articles.bin`.
Build publication with `python3 tools/notice_seasonal_owner.py`. Build the reader:

```sh
python3 tools/build_notice_overlay.py --treasure --seasonal \
  --module build/notice-seasonal-runtime/module.json \
  --output build/noticeboard-seasonal/reader
bash tools/build_seasonal_pilot.sh
```

The tracked full-ROM recipe contains every preceding option and explicit resource
path. Inputs and complete ROMs stay local; public release remains patch-only.

## Next work

1. Run a bounded seasonal native batch: actual lunar/weekday/shop calls, all
   complete bodies, both capitals, pending-prefix failure/retry, original
   scheduling/date behaviour, and full reader drawing. Preserve isolated saves,
   heap/global/code guards, and checkpoint restoration. Do not replay passed
   initial/treasure native cases.
2. Grow the native reader fixture's graphics offset beyond the 24,304-byte reader;
   the treasure fixture's `4000` offset is too early. Validate disjoint regions
   before execution. Host reader tests already cover all complete seasonal pages.
3. Continue remaining general text/names, full-name callers, gameplay/save
   compatibility, review, available validation, patch-only release, title art,
   and GameCube-style keyboard work. The overall goal remains active.
