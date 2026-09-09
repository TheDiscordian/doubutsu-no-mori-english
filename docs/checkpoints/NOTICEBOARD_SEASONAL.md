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
original timestamp and advances the runtime posting cursor only after successful writing.
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
Calendar mocks are call-contract tests. The native results below add actual
calendar and controlled scheduler execution, but do not establish normal
gameplay, the enlarged submenu pool, save/reload, or hardware acceptance.

## Complete native batches

`build/smoke-notice-seasonal-owner-01` completes all 78 scheduled body/capital
cases, four direct unscheduled creations, and failures at each of five backlog
positions followed by complete retries. All 359 calls and 513 assertions pass.
The actual native calendar, shop getter, scheduler, writer, allocator, and
cartridge-loaded creator execute; no replacement creator code is uploaded.
Whole saved-payload checks permit only complete posts and the native checked time.
Every interrupted case keeps the complete prefix and retries only its suffix.
The two unscheduled IDs remain unscheduled, rather than acquiring invented events.

The year-2001 native lunar calls return `07D10A01` and `07D10A1D`; complete fields
retain `October 1st` and `October 29th`. The actual weekday call produces the
native sports date `October 8th`. Town and level-three shop fields stay complete.
The posting cursor at `80137918` is Common runtime state outside saved payload
`80126EA0..8013681F`. These results prove same-session interrupted-post retry,
not persistence of pending work through save/reload.

`build/smoke-notice-seasonal-reader-01` completes all 82 body/capital cases,
84 draws including two continuation pages, 11,930 glyphs, and 47,720 vertex
positions. All 183 calls and 466 assertions pass. The fixture places game/graphics
state at auxiliary offset `6000`, beyond the 24,304-byte reader, in a `F000`-byte
allocation. Actual loaders, constructor, destructor, callbacks, and glyph drawing
execute. This controlled owned submenu does not prove normal menu initialization
or allocation of the enlarged production pool.

Both batches retain heap/code/stack/global guards, restore the entire saved
payload and checkpoint, keep isolated FlashRAM/Pak files blank, and shut down
gracefully. No audio or screenshots are enabled. Completed initial and treasure
native batches are not replayed. Four owner and four reader frozen-evidence
checks pass; `native-evidence-tests.log` records the combined result. The earlier
four initial-reader evidence checks also pass without emulator replay.

| Evidence | SHA-256 |
| --- | --- |
| Owner results | `17941ccc6c0e645412958fdeeec97fe425c3562a06992d94fa4c75330052bc96` |
| Owner scenario | `170cf2d074294519048b732d1dda43c4debe7cda180b0286904ac3d2ecf773a4` |
| Owner checkpoint | `3f739ca7f557a3314c6c8a3ed07050a40baf4b4a42612a1de3f8ee7aadd6156a` |
| Reader results | `99ff132454c32a72b7c1f1a92d54fa731d689fc3712cf2d93e2391ba21d94687` |
| Reader scenario | `05f816f7aad1c4a4fa9fb079a8f944fb250d5ee80d180fee95a129e916d9bd4c` |
| Reader checkpoint | `07fdc7af40011006cfa1ebd3f1fb52dc1d4b5cbaf278542e0447d90f5816909c` |

Native fallback years, date boundaries, other shop tiers, new null-allocation
faults, normal menu entry, production pool allocation, and save/reload remain
acceptance work. Host tests cover fallback contracts and all shop tiers; those
are not substituted for native evidence.

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

1. Continue remaining general text/names and full-name callers. Do not replay
   the completed seasonal, initial, or treasure batches.
2. Batch outstanding native edges and normal menu/pool/save checks after bulk
   text installation, including interrupted-post persistence.
3. Complete gameplay/save
   compatibility, review, available validation, patch-only release, title art,
   and GameCube-style keyboard work. The overall goal remains active.
