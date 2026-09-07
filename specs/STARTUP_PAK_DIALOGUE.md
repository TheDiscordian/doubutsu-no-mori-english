# Native startup and Controller Pak dialogue

## Scope

`translations/n64-startup-pak.json` provides 35 original English drafts for the
six startup speakers. They describe native Pak capacity, write failure, duplicate
returning players, accepted transfers, cancelled returns, and Pak removal during
an operation. The GameCube's same-numbered rumble settings, Memory Card slots,
and different error meanings are not native equivalents.

These edits change text only. Startup logic, storage operations, save structures,
font assets/advances, and buffer limits remain unchanged. Every native command
and argument remains exact except these five explicitly tested colour lengths:

| Native command | English command | Complete highlighted term |
| --- | --- | --- |
| `50:198CDC:09` | `50:198CDC:0E` | Controller Pak |
| `50:198CDC:06` | `50:198CDC:0A` | controller |
| `50:BE2D2D:07` | `50:BE2D2D:0C` | START button |
| `50:324BE1:04` | `50:324BE1:08` | A Button |
| `50:198CDC:04` | `50:198CDC:09` | cartridge |

The N64 highlight remains `50:198CDC:03`. Tests compare the complete command
stream with only the five allowed changes and check each complete following
term. Native `05` warning formatting, expressions, pauses, pages, free fields,
catchphrases, actions, choices, branches, and terminators remain ordered. Original
English line divisions fit the existing native pages without reference reflow.

## Message families and routes

| Speaker base | Capacity | Write error | Duplicate return | Copy accepted | Copy declined | Pak removed |
| --- | --- | --- | --- | --- | --- | --- |
| `1400` | `140C` | `1413` | `1415` | `1416` | `1417` | `1418` |
| `1428` | `1434` | `143B` | `143D` | `143E` | `143F` | `1440` |
| `1450` | `145C` | `1463` | `1465` | `1466` | `1467` | `1468` |
| `1478` | `1484` | `148B` | `148D` | `148E` | `148F` | `1490` |
| `14A0` | `14AC` | `14B3` | `14B5` | `14B6` | `14B7` | `14B8` |
| `14C8` | `14D4` | `14DB` (existing) | `14DD` | `14DE` | `14DF` | `14E0` |

The six capacity messages explain deleting unneeded Pak data, holding START while
resetting the N64 to reach its deletion screen, removing the Pak if it will not
be used, and pressing A when ready. They return to `13F4/141C/1444/146C/1494/14BC`
respectively. The original capacity instructions are identical apart from these
targets; their English bodies remain identical too. No rumble-choice branch is
introduced. This is a translation of instructions, not an executed deletion.

The five write errors say writing failed, return to title, check the Pak
connection, and restart. They do not add a read failure or unavailable card-slot
field. The sixth existing English error `14DB` already describes this condition
and remains unchanged.

Duplicate-return warnings retain both native free-field `26` insertions. Starting
from the Pak record will erase the record from the player's earlier return.
That warning remains before `5E` and native choices `0066/003D`. Each question
keeps its immediate accepted/declined successors and `09/9/0001` request. No
default choice, confirmation action, or actual stored record changes.

Accepted transfers explicitly copy from Controller Pak to cartridge. All four
`05:C35F00` warning controls remain. Power-off and Pak-removal warnings precede
`59:04` and `09:9:0001`, then the original `0E` continuation selects
`1407/142F/1457/147F/14A7/14CF`. Those post-wait messages remain unchanged.
Declining instead asks for Pak removal and an A press, then returns to the
speaker's original start prompt. Declined text adds no transfer request.

The six mid-operation removal messages retain each speaker's explanation.
`1440` warns about losing a precious record, `1468` describes losing track of
progress, `1490` retains its additional catchphrase, and `14E0` has no invented
initial `03:08` pause. All return to title, ask for reinsertion into the
controller, and restart. They do not become GameCube missing-town-card errors.

## Verification and remaining work

Eight focused tests check all 35 complete source hashes, exact command/colour
changes, original draft layout, all six capacity/confirmation/transfer/cancel
routes, warning placement, native field counts, and distinct error meanings.
Every draft fits the unchanged 1,024-byte expansion limit without layout warnings.
All 519 regression tests pass, including the eight focused checks.
Both full and basic generation include all 35 and retain every earlier edit.

The cartridge-load scenario includes all 35 drafts and thirteen unchanged
messages: the six start prompts, six post-transfer continuations, and `14DB`.
It checks complete headers/text, adjacent/module guards, and checkpoint
restoration in a fresh silent four-MiB process with save writes disabled.
All 48 complete loads and 146 assertions pass across 249 recorded steps,
with blank FlashRAM and graceful shutdown.
This loader-only test does not execute warning formatting, ordinary startup,
choice selection, erasure, transfer, reinsertion, saving, or hardware gameplay.

Normal title/travel flows, dynamic fields and warning rendering, actual
confirmation/cancellation, safe storage recovery, and final wording remain
acceptance requirements. Recorded results and hashes belong in
`docs/WORK_LOG.md`; generated inputs and evidence remain ignored under
`build/startup-pak-*` and `build/smoke-startup-pak-01/`.
