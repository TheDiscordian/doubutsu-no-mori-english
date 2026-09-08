# Complete references with original native mood changes

## Purpose

Some native resident conversations set a persistent mood and its duration at
a page boundary. Their complete GameCube counterparts omit that pair. Dropping
the native pair would change gameplay state; treating it as an ordinary facial
expression is incorrect. Restore the original pair at the individually reviewed
corresponding English page without removing any reference words or delivery.

## Native behaviour

The pinned resident overlay uses `80976588..80976604` to read NPC0 row four,
slot two, then slot eight. A nonzero slot-two value calls `80978800` with the
actor, mood, and duration, then clears only the two consumed slots. Value five
is mapped to zero; this import path does not introduce that value. Consumer
SHA-256 is `7e62d55be66039121b422ad0e3ca9a18ab0c1d92f21f90bcd6e5f0d15d4a2c29`.

The native setter `80978800..80978874` reads the animal pointer at actor `174`,
writes the mood at animal `51E`, and uses actor `804` for the timer. A changed
nonzero mood starts `duration * 1800`; the same mood adds that amount, capped at
18000. A null animal does nothing. The supplied GameCube decompilation identifies
the corresponding `aNPC_check_feel_demoCode` and `aNPC_set_feel_info` behaviour.
Native machine code and structure offsets, not assumed cross-platform addresses,
are the authority. Production actor code and saved structures remain unchanged.

## Import contract

An individual `complete_reference.native_mood` rule binds the source byte offset,
decoded-reference character offset, and complete original ten-byte pair. Only
`09:02:0001` followed immediately by `09:08:0001` or `09:08:0002` is accepted.
The native source must contain exactly those two mood/timer commands, together
at a native page start. The English reference must contain no mood/timer command.
Its insertion point is the start of the reference or immediately after an exact
page-clear tag. English page numbers are not assumed to match native page numbers.

The complete native source, supplied reference, and final output stay hash-bound.
No wording/storage/other permission combines with this rule. The insertion
retains every English character, newline, page, pause, colour, and field. Complete
native actor command order and arguments must already agree after the insertion,
before the ordinary adapter runs. This prevents an incorrectly chosen page from
being hidden by that adapter's opcode-position argument restoration. Existing
field, flow, capacity, and formatting validation remains mandatory.

Generation and installation require the pinned unchanged resident overlay,
relocations, core order getter/setter, parser, and dispatch table through the
existing native-consumer guard. No animation-value, actor-field, random-branch,
or additional insertion permission is granted. Mid-page pairs and changed
topics remain outside this contract and require their own review.

## Acceptance

Nineteen complete references have individual approvals:

`1788 1F88 1FAD 1FB6 2067 207D 25E0 25EA 25F4 25F6 2621 2623 2628
2630 2634 263C 264F 2655 27B5`.

Their reviewed pages cover a prize handoff, sunny weather, the sun contest,
staying awake, completed trades, umbrella/weather acceptance, outdoor activity,
snow and gyroids, rain advice, thanks, and an igloo conversation. In `1FAD`,
the native effect follows the third page clear but belongs after the fourth
English page clear, at the final victory claim. Matching page counts would put
it too early. `263C` retains duration two; the other eighteen retain duration
one. Only `2067` removes two redundant article-suppression controls through the
existing adapter; no English text or delivery is removed.

Approval review must identify the corresponding semantic page and retain the
native mood effect at that point. Tests cover exact pairs and offsets, missing
or duplicated native commands, reference duplicates, page boundaries, actor
order, complete English retention, source/reference/final hashes, and independent
builder rejection. Native tests must verify complete cartridge text, both order
writes, cursor advancement, guards, and checkpoint restoration. These checks
do not establish normal mood animation, timer progression, save/reload, final
wording review, or original hardware. Exact batches/results belong in the work
log; unfinished review remains in the completion queue.
