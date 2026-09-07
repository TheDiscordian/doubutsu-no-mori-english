# Native seasonal topics and connected replies

## Scope and presentation

`translations/n64-seasonal-topics.json` supplies 29 original English drafts:
26 missing conversations and three corrections to incompatible reference replies.
All native commands and arguments remain exact and ordered, including pages,
pauses, fields, expressions, other actor requests, choices, branches, and endings.
Original English lines fit within those native pages. No existing GameCube
candidate is reflowed, and no font, executable code, buffer, save format, actor
permission, or event schedule changes.

| IDs | Native meaning retained |
| --- | --- |
| `0B9C`, `11A2`, `1800`, `2833` | Sunday tournaments, June schedule, experience, and current progress |
| `0BC5` | Show the judge a fish; a fish bigger than any caught so far earns a prize |
| `11A4`, `281D` | Approaching morning aerobics, others' reactions, and rain cancellation |
| `11B1`, `2829` | Second Monday in October, both yearly sports fairs, ball tosses, and aerobics enthusiasm |
| `0BA7`, `11AE`, `11AF`, `180D`, `180E`, `270E`, `270F`, `2826`, `2827` | Distinct Fifteenth Night and Thirteenth Night, their lunar dates, nearly full moon, and invitations |
| `27D0`, `27EE`, `27EF`, `2824` | Harvest-moon date question and connected native moon-viewing replies |
| `27D3` | Dumplings beside the viewer and the joke about eating the moon by mistake |
| `27BC` | Spring blossoms, uncertainty between the 6th, 7th, and 5th, and visiting the shrine all three days |
| `27D6`, `27F2` | Matsutake enthusiasm, scarcity, and getting up early despite sleepiness |
| `27E2`, `27E3` | Waiting a whole year and counting down to the New Year's Eve countdown |
| `2834` | Christmas presents and the question about needing THAT |

The three corrected records are `0BC5`, `27EE`, and `27EF`. The native fishing
rule compares against fish caught so far; the reference's end-of-day prize claim
does not describe that rule. The two native replies describe moon viewing and
an autumn evening, not the reference meteor showers and summer. The second reply
retains lunar month eight, day 15, dumplings, and asking somebody else for the
converted date. Their original requests and fields remain unchanged.

## Date contract

Six drafts, `11AE/11AF/180E/270F/2826/2827`, declare
`runtime_requirements: [ordinary_dialogue_dates]`. Native `3E/3F` stay in order
with an English separating space. These are the actual converted date of lunar
month nine, day 13, not the current date or the first viewing's `3C/3D` pair.
The [ordinary-dialogue date patch](DIALOGUE_DATES.md) supplies the already-tested
English preparation; this batch does not change or extend the calendar code.
Basic generation withholds all six records and does not substitute the
incompatible same-ID GameCube dates. The full build verifies the installed patch.

`11AF` keeps the pond gathering from 6 p.m. `270F` explains the old lunar versus
modern calendar using the native samurai comparison. `2826` retains the entire
last-page joke that the speaker prefers the sun. `27EE` keeps current-month
command `1E`, served by the existing resident-module month formatter; this field
does not supply a converted event date.

## Questions and connected text

| Question | Choices in native order | Replies in native order |
| --- | --- | --- |
| `0B9C` | `002F/0069` | `0BC5/0BC6` |
| `11A2` | `002F/0069` | `11CA/11CB` |
| `11A4` | `0003/004E` | `11D4/11D5` |
| `11B1` | `002F/0069` | `11CC/11CD` |
| `1800` | `004C/0052` | `182B/182C` |
| `27D0` | `0069/0161` | `27EE/27EF` |
| `27D6` | `00EF/0162` | `27F0/27F1` |
| `2824` | `0069/017F` | `2841/2842` |
| `2833` | `0044/003B` | `2845/2846` |
| `2834` | `004C/0161` | `2847/2848` |

Seventeen existing connected candidates stay unchanged. They include the native
`11CD` Sports Day reply with its 9 a.m. shrine-plaza gathering, `2842` with the
first moon's converted date, and `2847` with the English small aside. The approved
`27F0` local mushroom-finder wordplay remains; the broader enthusiasm question
and scarce-mushroom response still connect without changing its approval.

Native `2833` choice `0044` means a positive response about progress. Its shared
English label, `Sure!`, and the second label, `It's OK, I guess.`, require
contextual wording review. This batch does not globally rewrite a reused label
or silently swap in the GameCube choice `018A`. Normal selection and the final
choice-label polish remain acceptance work.

`27E2/27E3/281D/2829` retain paired requests to native NPC0 rows two and eight,
including the distinct row-eight value `0002` in `27E3`. The countdown retains
all three numbers and their individual pauses. No standing-expression approval
is broadened to omit those requests. The replies' quest requests `0C/5/0001`,
`0C/5/0066`, and `0C/5/0002` remain exact.

## Verification boundary

Eight focused host tests check all complete hashes and native command sequences,
the unchanged 1,024-byte expansion limit, six date dependencies, ten question
routes, native choice identities, complete jokes, corrected meanings, and layout.
Generic free-field width warnings remain visible for the six dated records and
the current-month reply. A separate layout check substitutes all twelve English
months and all 31 ordinal days: all 372 combinations fit each of those seven
drafts with every other field still at its conservative width. This is a host
layout check, not a new native calendar conversion or rendering claim.

The fresh silent four-MiB cartridge-load batch checks all 29 drafts and the
seventeen unchanged replies, with complete headers/text, adjacent/module guards,
and restored checkpoint. It passes 46 native loader calls and 140 assertions
across 239 recorded steps, with blank FlashRAM and both save-write permissions
disabled. Only `8009E558` is called: no event, selection, prize award, actor
request dispatch, date insertion, saving, or original-hardware gameplay is
executed by this batch.

Complete wording, ordinary events and their connected choices, dynamic rendered
dates, and the human-playthrough review remain required. Artifact hashes and
test results belong in `docs/WORK_LOG.md`; generated evidence remains ignored
under `build/seasonal-topics-*` and `build/smoke-seasonal-topics-01/`.
