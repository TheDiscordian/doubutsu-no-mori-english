# Native introductions and reunions

## Content and provenance

`translations/n64-reunion-greetings.json` contains 72 complete native-specific
drafts for `0013..005A`: 24 first introductions, 24 long-absence reunions, and
24 short-absence reunions. All supplied same-ID English GameCube slots contain
only termination. Native and legacy Japanese agree, and none of these records
has another identical visible native-text record after commands and whitespace
are removed. These checks establish no English donor or unused-code status.

Preserve the individual voices, morning/day/evening/late-night distinctions,
hesitation, interruptions, repeated catchphrases, and teasing or qualified
friendship invitations. Specific jokes include early-bird luck, fated meetings,
unwanted newspaper/religious solicitation, kidnapping suspicions, forgotten
friends, lookalikes, weight, and carnivores. The deep-blue joke in `0048` uses
navy blue to retain the escalating colour metaphor. It is an original English
localization, not extracted GameCube wording.

## Native control and presentation contract

Every command and argument remains exact, including every occurrence of player
and speaker names (`1A/1B`), catchphrases (`1C`), old town (`2A`), months (`2B`),
weeks (`2C`), and current town (`2F`). Field order and page assignment stay native.
All waits (`04`), clears (`02`), page counts, and continuing `01` endings remain.
Do not replace the native ending with the empty GameCube slot's `00`.

All per-page newline counts remain except `002C` page zero: its native five-line
page becomes four English lines by combining the interrupted greeting and
surprise. The player question, forgotten-speaker question, and speaker name
remain on that page. No page or pause is removed. No actual GameCube reference
is reflowed. Native-only English lines can move within their original page to
fit fields without shortening the message or dropping a clause.

Literal more-than-one-month wording in `002D/0030` is not a dynamic counter.
The actual month and week fields retain their different codes, units, and
qualifiers. `0037` repeats the player name three times; `0040` repeats the
speaker name twice; `0021` repeats the catchphrase four times. `0036/0042`
retain delayed recognition and their two separate player-name occurrences.

All drafts use ordinary exact-control validation and the unchanged 1,024-byte
expansion bound; all bounds fit at 148–620 bytes. Both basic and resident-runtime
candidate generation admit the complete batch. No new actor or field permissions,
runtime code, font metrics, save layouts, or reference approvals are introduced.

The generic current-town width estimate remains conservative. Nine records
(`0034/0045/0046/0049/004E/0050/0057/0059/005A`) retain explicit generic width
warnings. A separate host check uses six fullwidth cells only for current-town
`2F`, following the verified source and consumer in
[the field contract](REFERENCE_FIELDS.md). Every other field, including old-town
`2A` and both absence counters, retains the unchanged conservative estimate.
The global validator is not narrowed. Warnings remain visible for final review.

## Verification and remaining work

Focused tests check every source hash, exact command sequence, complete encoding,
continuing ending, expansion bound, page/field order, and the single line-count
exception. They also check runtime selection, native/legacy agreement, empty
same-ID English references, distinct fields/units, repetitions, and native topics.
The cartridge batch passes all 72 complete message loads, 218 assertions, and
369 recorded steps, checking headers and guards and restoring an isolated silent
checkpoint with blank FlashRAM/Pak files. All ten focused checks and 620
full-suite regression tests pass. These native calls execute only loader
`8009E558`, not the ordinary greeting actors. Exact results belong in
`docs/WORK_LOG.md`; current status belongs in `docs/PROGRESS.md`.

Host and loader tests do not establish actual greeting/reunion selection,
reachability, preparation of live old-town or absence fields, final wording and
rendered presentation, ordinary save compatibility, or original-hardware
acceptance. The distinct `0001..0012` development/control samples and all broader
missing text, runtime, review, gameplay, release, and stretch-goal work remain.
