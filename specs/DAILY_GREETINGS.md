# Native move, daily, and month-return greetings

## Content and provenance

`translations/n64-daily-greetings.json` supplies 85 complete original drafts
for `005B..00AF`. Every source remains Japanese in the legacy distribution,
and every supplied same-ID GameCube slot contains only termination. These are
native-specific translations, not same-ID English matches or permissions to
reuse an unrelated reference. A record's early bank position does not establish
that it is unused.

The batch contains 24 recent-move conversations (`005B..0072`), 24 daily
greetings (`0073..008A`), 24 repeat greetings (`008B..00A2`), and thirteen
month-return conversations (`00A3..00AF`). Preserve the separate old/current
town destinations, incomplete unpacking, visits from old friends, secret-move
and starting-over jokes, daytime/evening distinctions, sleepiness, snack and
furniture remarks, gruff reprimands, and qualified or teasing responses.
The native drinking remark in `0083` and three-kilogram remark in `00A4`
remain in their actual context; neither is replaced with unrelated dialogue.

## Control and presentation contract

All native commands and arguments remain exact. This includes player and
speaker names (`1A/1B`), catchphrases (`1C`), the supplied old-town field (`2A`),
month counts (`2B`), current-town insertion (`2F`), waits (`04`), clears (`02`),
and continuing ending `01`. Every field occurrence remains on its native page
in the native order. The GameCube empty-slot `00` must not replace `01`.

English wording occupies the original pages, retaining every page's newline
count, including the shorter repeat greetings. Original English lines may
place a full field on its own line, but no native page or text is removed to
meet a capacity limit. No actual GameCube reference is reflowed, no new actor
or field permission is added, and no runtime, font, input, or save change is
needed. All drafts remain available in both basic and resident-runtime generation.

The ordinary 1,024-byte expansion checks retain their conservative field
allowances. Six drafts (`0062/0065/0067/006D/0070/0071`) have generic current-town
width warnings because that generic estimate exceeds the actual six-byte name.
The native current-town consumer and source are verified in
[the field contract](REFERENCE_FIELDS.md); `m_land.h` defines `LAND_NAME_SIZE`
as six. A separate host layout check substitutes six fullwidth cells only for
`2F`, leaving every other field at its full conservative bound. All 85 draft
layouts fit that check. Generic warnings remain visible; this does not narrow
the global validator or assume a bound for the separate old-town field.

## Verification boundary

Focused tests bind all original source hashes, exact command sequences,
field/page assignments, line counts, continuing endings, complete encoding,
expansion limits, runtime selection, empty English donor slots, source/legacy
agreement, and specific native topics. The cartridge batch loads every complete
new message and checks headers, neighbouring/module guards, and checkpoint
restoration with silent isolated state.
All 85 complete cartridge loads pass with 257 assertions over 434 recorded
steps, restored checkpoint, and blank FlashRAM/Pak files. The native test calls
only loader `8009E558`; it does not run greeting selection or field preparation.
All 610 full-suite regression tests pass, including eight daily-greeting tests.

These checks do not establish the early records' actual callers, normal move
or greeting selection, live old-town/month preparation, rendered names and
catchphrases, final wording/presentation review, ordinary saving, or hardware
compatibility. The wider introduction/reunion block `0013..005A` has a separate
[complete draft contract](REUNION_GREETINGS.md). The distinct development/control
samples `0001..0012` and other missing text remain work.
Generated evidence stays ignored under `build/daily-greetings-*`; current
results belong in `docs/PROGRESS.md`, and exact runs/hashes in `docs/WORK_LOG.md`.
