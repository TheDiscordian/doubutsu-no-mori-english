# Native startup greetings, preparation, and menus

## Scope

`translations/n64-startup-greetings.json` supplies fifty original English drafts.
They retain the complete native dialogue and action order instead of importing
GameCube-only card fields, rumble options, or shortened preparation sequences.
No runtime, font, saved layout, storage action, or speaker permission changes.

| Family | IDs |
| --- | --- |
| Recognised player | `1404 142C 1454 147C 14A4 14CC` |
| New face | `1405 142D 1455 147D 14A5 14CD` |
| Returning traveller | `1408 1430 1458 1480 14A8 14D0` |
| Visiting player | `140A 1432 145A 1482 14AA 14D2` |
| Continue from the record retained during travel | `1410 1438 1460 1488 14B0 14D8` |
| Sound/other/cancel menu | `13F5 141D 1445 146D 1495 14BD` |
| Other-settings menu | `1412 1462 148A 14B2 14DA` |
| Clock-setting acknowledgement | `13F7 141F 1447 146F 1497 14BF` |
| Away-player warning, town-reset cancellation, identity retry | `1437 14A2 14D9` |

All native commands and arguments are exact except twelve highlighted-name
lengths in the six returning-traveller messages: `50:198CDC:09` becomes
`50:198CDC:0E` for Controller Pak, and `50:198CDC:04` becomes `50:198CDC:09`
for cartridge. Those six drafts use `reference_layout`; the other 44 use `exact`.
Every page, pause, field, expression, action, choice, branch, and terminator
remains. `1480` retains its one-character coloured emphasis after the name,
using an English exclamation mark without changing the count.

## Preparation and storage boundaries

The eighteen recognised-player, new-face, and retained-record preparations keep
their two native `05:C35F00` formatting controls, power-off warning, `59:04`,
and `09:9:0001`. Their wait, completion page, personality-specific farewell,
and final `00` remain inside the same complete native record. They do not become
the GameCube's shorter `0E`-linked preparation messages. The lazy speaker's
muted grey admission in `1454`, both player-name insertions in `147C`, and the
snooty speaker's closing remarks remain.

The six returning-traveller messages retain player field `26`, copying from Pak
to cartridge, all four warning-format commands, and the power/removal warnings
before the request. Their continuations are `1407/142F/1457/147F/14A7/14CF`.
The six visitor arrivals instead prepare the game and continue to
`1409/1431/1459/1481/14A9/14D1`. Their original field order remains, including
town before player in `145A` and no added town field in `14AA/14D2`.

`1437` warns that the player is away: the retained record can be used, but items
and money went on the trip. Both player-name insertions remain, and the warning
precedes `0044/003D`, successors `1438/1439`, and request `09:9:0007`.
`14A2` explicitly cancels rebuilding the town, expresses relief at not vanishing,
and returns through `1494`. `14D9` retries the player's identity through native
`0D`, `19`, expression `FF`, and `09:9:0006`. No standing-resident expression
permission is applied to either title-menu speaker.

## Menus and clock acknowledgements

The six first menus retain choices `0070/01B3/0029`: Sound settings, Other
things, and the native cancellation choice. Each retains its sound menu, other
menu, and start-prompt branches. No GameCube rumble option or fourth branch is
added. Five other menus retain `0072/0073/0071/0029`: Demolish a house, Build a
new town, Set clock, and cancellation. The existing sixth menu `143A` remains
unchanged. Native `5E`, selection ordering, expression reset, and `09:9:0003`
remain. These text edits do not choose or execute an erasure action.

The six clock acknowledgements retain `04`, their native clock-setting successor,
`19`, and `01`, without the extra GameCube `5B` command. They are not the separate
opening greetings that display the current date and time.

## Verification and separate opening clocks

Eight focused tests and all 527 regression tests pass. They check all fifty
complete source hashes, exact commands and twelve colour corrections, complete
preparation/warning order, native choice identities and targets, individual
asides, and the unchanged expansion limit. Seventeen generic town-width warnings
remain visible. A separate host check substitutes six fullwidth Japanese cells,
the unchanged native town-name limit: all fifty drafts fit, with every other
field still at its conservative width. No font or generic bound is reduced.

The batch loads all fifty drafts and all 42 unchanged connected candidates.
Every one of their 53 unique outgoing targets has a candidate. The silent
four-MiB run passes 92 complete loader calls, 278 assertions, and 469 recorded
steps, including headers/text, adjacent/module guards, checkpoint restoration,
blank FlashRAM, and graceful shutdown. It calls only `8009E558`, with no save
write permission. It does not execute startup selection, erasure, preparation,
travel, date insertion, warning rendering, or original-hardware gameplay.

The separate [opening clock references](STARTUP_CLOCKS.md) cover
`13F2/141A/1442/146A/1492/14BA`, completing Japanese-static-text candidate coverage
in the inspected startup range `13F2..14E1`. They preserve GameCube calendar and
timing intent while omitting only the unavailable storage-location clause.
They require the resident AM/PM runtime and remain withheld from basic builds.
Original-draft selection also withholds module-command drafts when that runtime
is absent; the full builder independently verifies installed hooks and commands.

Normal gameplay, complete wording and layout review, actual warning/field
rendering, startup/storage acceptance, and hardware remain requirements.
Generated evidence stays ignored under `build/startup-greetings-*` and
`build/smoke-startup-greetings-01/`; hashes belong in `docs/WORK_LOG.md`.
