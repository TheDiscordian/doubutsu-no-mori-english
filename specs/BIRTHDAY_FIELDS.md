# Complete ordinary-dialogue birthday fields

## Native evidence

The ordinary overlay's birthday preparer is `80921324..80921464`, reached by
demo-order type nine/value four through `80921464` and table `80921D78` entry
three. Its complete original body SHA-256 is
`770b3dbb0270671fe82acf1804887c667dd60e4c1ebd6f07c95b95be35a05440`.
The overlay/source bounds are shared with [ordinary dates](DIALOGUE_DATES.md).

The native function reads the current-player pointer at `80136FD8`, then birthday
month/day at player `A92/A93`. It consumes exactly two draws from `8002C9AC`,
multiplies each single-precision result by 12.0f, and truncates to a signed index.
The first index selects native string `0458..0463` (animal year) for item field
zero. The second selects `0494..049F` (Western sign) for item field one. There is
no GameCube repeat-avoidance state in the native helper. These deliberately
random values must not be replaced by the player's actual sign.

Item field two receives the actual Western sign, calculated with the complete
native twelve-pair table at `80921D58`:
`0113021203140413051406150716081609160A170B150C15`.
The calculation starts at index zero, selects the first month/day ceiling, and
rotates by minus three with wrap. The native invalid-date behaviour is preserved
separately from the English formatter's display fallback.

The native numerical item helper `8091D904` supplies month/day to item fields
three/four. English references expect a month name and ordinal day. The complete
Western name Sagittarius is eleven characters, so widening only the numeric
formatting calls cannot complete the birthday dialogue.

## Experimental implementation

`runtime/birthday.c` supplies a dedicated birthday preparer using the existing
sixteen-byte main-window item fields. The complete common English animal/sign
names are separate display strings. Shared native general strings and their
unexpanded callers are not changed or credited as translated by this work.
The English names match the supplied GameCube labels; they are not abbreviations
chosen to fit ten bytes. Month/day use the existing English formatters.

The guarded entry hook replaces only the first two original words
(`27BDFFC8/AFBF0034`) with a direct jump and delay-slot nop. Those entry words
have no native relocation. Remaining body and relocation entries stay present
and unchanged; original file, BSS, and save sizes do not grow. Installation must
bind the complete original body and reject external interior references before
enabling the hook. The complete cartridge reference audit finds exactly one
entry pointer, table offset `0045D4`, and no external interior targets. It scans
aligned literal pointers across all DMA files and native jumps/branches only in
pinned executable sections. The audit cache is keyed by the immutable verified
ROM, never by a changed output image.

All 33 original messages containing the exact `0C 09 0004` request require the
complete installed ordinary-date patch. The builder derives this dependency from
the verified cartridge independently of candidate metadata or identity approvals.
The generator withholds those references without the option and excludes them
from alias fallback. Enabled references carry the explicit requirement; original
draft selection receives the same source-derived requirement. Shared item commands
do not acquire global birthday meanings: a field before the birthday request, or
after another preparation request, retains its original purpose.

## Complete English conversations and answers

`088B` and `2586` retain their complete supplied English references. `088A/088C`
retain every supplied word, newline, page, pause, and action while replacing only
their context-dependent acknowledgement label. All three birthday-entry replies
display `0021/00C4`, You know it! / You're wrong!, retaining acknowledgement at
`0889` and correction at `088A`. Shared `0041` remains Nice to meet ya. in the
choice bank for its greeting contexts.

`2586` deliberately uses random Western sign field `32`, not actual sign `33`.
Its `0127/0162/00C4` answers retain confident reply `259D`, modest reply `259E`,
and incorrect-sign reply `259F`, including native friendship values `005/003/069`.
No action, reward, random selection, saved birthday, or global label changes.

The existing [contextual-label contract](CONTEXTUAL_CHOICES.md) explicitly binds
an unchanged complete reference when its donor already uses the native menu.
It does not invent a native-menu adaptation or permit changed reference text.
Two such approvals cover `088A/088C`; the other two retain the ordinary guarded
native-menu adaptation. The full source/output/label hashes remain mandatory.

## Compiled and host verification

The resident image contains 23,488 linked bytes, leaving 1,088 bytes below the
unchanged 24 KiB linked limit and separate 8 KiB test area. The cartridge heap
reservation remains 32 KiB. The preparer uses 64 stack bytes; its two helpers use
zero additional stack bytes. Independent pinned-Docker module builds agree at
SHA-256 `9f1f730f13d0a2a78bc2bbcfc570a5fa2249976cbe253edd6a22274eb95a6460`.
Imported NPC capture/creator and generation-probe code is rebuilt against the
new symbol addresses; stale module-bound imports remain rejected.

Host tests exercise the real wider item setter/reader, not a replacement mock
storage implementation. They cover all 144 random pool pairs, all 65,536 native
byte-valued date pairs, every retail month/day, invalid display fallbacks, missing
player handling, exact saved-date retention, first-row publication before the
second draw, full Sagittarius insertion, and unchanged neighbouring fields.
Complete reference/branch, source/table/entry mutation, dependency, and original
two-choice letter-question checks are separate tests. Full test results and
native execution evidence belong in the work log; normal gameplay and hardware
acceptance remain required.

## Required verification

The completed native birthday/date/contextual batch passes 913 calls and 1,588
memory assertions over 4,083 recorded steps, including all 24 birthday cases,
33 complete related messages, 190 birthday insertions, and 57 contextual/shape
answers. All 714 full-suite tests pass. Independent module/creator/ROM/UPS builds
match. The fresh train-to-town and NPC creator regression also passes. Exact
artifacts, hashes, and the independent audit are recorded in `docs/WORK_LOG.md`.
These checks satisfy the isolated implementation tests below, not normal
birthday-entry, gifting, rendering, saving, or hardware acceptance.

- Verify all native birthday instruction/table inputs, entry references, RNG
  scaling, field order, native boundary calculation, and unchanged saved date.
- Check all byte-valued month/day pairs, all twelve values in both random pools,
  full Sagittarius, date fallbacks, field lengths/padding, and no partial names.
- Compile with the pinned Docker toolchain, retain module/stack limits, and
  rebuild every imported overlay against the new resident symbol addresses.
- Load the actual patched ordinary overlay with the native cartridge loader.
  Execute the real request/dispatcher and check both random draws, the actual
  sign, all five full inserted fields, guards, source/save retention, and restore.
- The native fixture checks both sides of every sign boundary and all twelve
  values in both random pools. Independent calls to original `8002C9AC..8002CA00`
  verify seed `8003C590`, float scratch `800419F0`, and exactly two draws. The
  complete function hash is
  `54eaafabfeeb3e70158a80e2e61b775f4340c6620b3984238268d2765f34bb56`.
  A full-message batch inserts only fields prepared by the birthday request;
  it leaves the earlier food field in `0872` and later lucky colour in `29F9`
  untouched. It does not execute those unrelated preparation requests.
- Preserve complete `088B/2586` reference wording, lines, pauses, and native
  question/answer actions; audit the acknowledgement and wrong-sign replies.
- Batch broader runtime/date/mail regression after integration. Normal birthday
  entry, conversation selection, gifts, rendering, saving, and original hardware
  remain separate acceptance requirements.
