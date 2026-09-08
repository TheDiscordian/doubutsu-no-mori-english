# Native resident return greetings

## Content and provenance

`translations/n64-return-greetings.json` supplies 35 original translations for
`00B0..00D2`. The native and legacy entries retain the same Japanese prose;
every supplied same-ID GameCube slot contains only termination. A comparison
of visible native prose, ignoring commands and whitespace, finds no identical
second native record for any of these entries. No complete cross-ID English
donor is established, so these remain native-specific translation drafts.

The range includes friendly, energetic, sleepy, gruff, and teasing greetings,
month/week absences, health worries, furniture/decorating reminders, hot-spring
travel wishes, and late-night jokes. Preserve the debt-collector joke, the
spears-from-the-sky exaggeration, and the different teasing/reassuring responses.
Do not replace these complete conversations with generic return greetings or
classify them as unused simply because earlier records contain development text.
Reachability and actual callers remain unestablished.

## Control and presentation contract

Every source hash and every original command/argument remains exact. In
particular, month field `2B` and week field `2C` are not interchangeable; player
name `1A` and every catchphrase `1C` stay in their original command order and
on their original page. All records retain continuing terminator `01`, not
the empty GameCube slot's `00`. No actor request, action, new runtime command,
field permission, save change, or font edit is introduced.

Original English lines occupy the native four-line pages. The total newline
count and each page's line count remain the same as the native source. Each
native wait `04` and clear `02` stays in place. There is no GameCube reference
layout to reflow in these empty donor slots. Numeric fields use their full
existing conservative expansion bounds; layout does not depend on assuming
that an absent player can only have a one-digit absence count. All original
drafts remain available in basic and resident-runtime generation.

## Verification boundary

`tests/test_native_return_greetings.py` checks every original source hash,
complete native control sequence, page/line structure, terminating mode,
field multiplicity and page assignment, candidate encoding, expansion bounds,
layout, explicit native topics, and the lack of same-ID English donors.
All seven focused tests and 602 full-suite regression tests pass. The native
batch loads every complete new message from the actual built ROM: 35 calls,
107 assertions, and 184 recorded steps pass with complete headers, adjacent/
module guards, restored checkpoint, and blank isolated FlashRAM/Pak files.
No new runtime or field-consumer behaviour is needed by this batch.

The loader test is not normal resident greeting selection, actual month/week
preparation, live catchphrase/name rendering, final wording review, ordinary
saving, or hardware validation. Those checks remain in the combined gameplay
and human-playthrough pass. Generated evidence stays local under
`build/return-greetings-*`; exact results and hashes belong in `docs/WORK_LOG.md`.
