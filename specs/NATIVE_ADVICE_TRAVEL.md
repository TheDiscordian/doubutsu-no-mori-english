# N64-specific advice and Controller Pak text

## Source and scope

`translations/n64-advice-travel.json` contains seven original English drafts
translated from the verified N64 source. The GameCube same-ID records have
different advice, contexts, or travel/storage rules and are not imported.

| Native ID | Preserved meaning |
| --- | --- |
| `0945` | Travelling erases the existing named Controller Pak record; ask whether to continue |
| `11F1` | Keep notes about errands and cross off completed tasks |
| `147F` | Resume a lively conversation after a wait |
| `14CF` | Resume a relaxed conversation after a wait |
| `14FE` | Estimate the time from sunlight; the method does not work at night |
| `1BD3` | Pelly requires the visitor's original Controller Pak to handle letters |
| `1BD4` | Phyllis requests that same Pak, including her muted aside |

The drafts do not mention the GameCube tailor, add its sewing-equipment choices,
replace native chat with town-entry farewells, change the travel warning into a
missing-town-data error, or forbid all letter handling by travellers.

## Control and formatting contract

All native commands stay in the same order with the same arguments except seven
colour-span lengths in `0945`, `1BD3`, and `1BD4`. Each affected
`7F50198CDC09` becomes `7F50198CDC0E`, immediately followed by the complete
fourteen-character term `Controller Pak`. No colour, actor command, sound command,
pause, page transition, field, choice, branch, or terminator otherwise changes.

The three formatting-adjusted drafts use the existing `reference_layout`
validator with unchanged field/flow/capacity checks. Their focused test imposes
the stricter complete native-command comparison, allowing only those exact
span-length changes and checking the following full term. The remaining four
drafts use the exact native-command policy. Native lines are composed as English
within the original pages; no GameCube wording or timing is discarded because
those references do not describe the native content.

The data-loss warning retains choices `0029/0062` and branches `0946/0947`.
The current English labels are `Maybe not...` and `Taking a trip!`, matching the
native cancel/travel order. No test in this content batch executes an actual
passport overwrite or changes user saves. Ordinary travel, Pak identity/error
handling, and post-office interactions remain gameplay validation requirements.

## Verification

The host test checks every original source hash, complete command sequence,
colour span and term, warning choices/branches, explicit erasure wording, muted
aside, and expansion budget. The batched native loader scenario checks all seven
complete messages from the built cartridge, adjacent/module guards, and checkpoint
restoration. These are original drafts requiring final wording/layout review,
not completed hardware or ordinary-action acceptance.
