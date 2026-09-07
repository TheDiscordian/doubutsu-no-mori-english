# Native resident topics and matched introductions

## Content

`translations/n64-resident-gaps.json` supplies eighteen native-specific drafts.
Four additional introductions use complete GameCube references with individually
bound source/reference/output hashes in `translations/reference_matches.json`.
No production runtime, font, save structure, or actor permission changes.

| Records | Native meaning retained |
| --- | --- |
| `02BB 03B9 10C8` | Failed errand; item taken by the named borrower; thanks for an item and surprise at being found |
| `084F 0850` | Complete letter/gift instructions; editable town melody at the post office; the separate board by the player's house and its friend-advertisement joke |
| `087B 1506` | Villagers move by accompanying player travel; the player's destination determines the move |
| `0AF8 0F8B` | Frustration, deep breathing, and an outfit gift; embarrassment at keeping an umbrella open after rain |
| `17C9 1C82` | Inventory-capacity refusal; appreciation for coming to town to send a letter |
| `1DCD 213B 2311` | New Year greeting; mood-dependent favourite-colour game; late visit after the resident's bedtime |
| `23E2 24D5 24D6 2A43` | Previous-town train delays; conversation and sweet-talk advice about an unnamed person; flowers wilting this season |
| `2BC3 2BC5 2BC7 2BC9` | First introductions with both names and the original friendly/teasing or startled-night context |

The four introduction sources exactly equal the complete native records at
`2DD1/2DD3/2DD5/2DD7`, respectively. Those English references express the native
meaning without the incompatible same-ID GameCube previous-town field `36`.
Use their complete wording, closing variants, manual lines/pages, punctuation,
and pauses unchanged. The source comparison includes all NPC0 row-two/row-eight
requests, expressions, names, catchphrases, and terminators. These approvals
do not extend standing-resident animation or field permissions.

## Control and presentation contract

The eighteen original drafts preserve every native command and argument except
seven explicit highlight-length corrections and one AM/PM insertion:

- `084F`: post office `4BA000:07 → 0B`, item screen `E11ED7:06 → 0B`, and
  A Button `324BE1:04 → 08`.
- `0850`: post office `4BA000:07 → 0B`, town melody `E11ED7:08 → 0B`, and
  both bulletin board spans `4BA000:05 → 0E`.
- `2311`: insert `76` immediately after the existing hour `21`, with a separating
  space. The English hour is twelve-hour time, so retaining AM/PM matters.

Those three drafts use `reference_layout`, with a stricter test checking the
entire native control sequence and exactly those differences. The other fifteen
use `exact`. Original English lines stay within the native pages; no GameCube
reference is reflowed, and no native page, pause, action, or terminator is removed.

The umbrella question keeps choices `00DC/00ED` and successors `29A8/29A9`.
The colour game keeps `0044/003D`, `213C/213D`, and `0C:5:0003`. The failed errand
keeps `09:5:006B`, not the GameCube quest-row request. The outfit gift stays before
`0C:3:0001`. The New Year message ends with `58:32`, with no invented year field.
Train delay uses native prepared field `32` after `0C:9:0002`, not the current
RTC minute `22`. The move warning retains final `00`, without GameCube help or
move-cancellation choices. No person field `39`, sender field `3B`, hobby field
`33`, or previous-town field `36` is invented.

Only the bedtime draft `2311` requires the resident module. Basic generation
withholds it and admits the other seventeen originals and four introductions.
The separate ordinary-dialogue lunar-date patch is not required by this batch.

## Verification boundary

Focused checks cover all eighteen native source hashes and command streams,
seven colour changes, hour-before-AM/PM, exact choices and special requests,
complete instructions and native topics, four complete cross-ID references,
and the unchanged 1,024-byte expansion limit. Generic field-width warnings remain
for `0850/1506/1C82/2311/23E2`. Host checks with the native six-fullwidth-cell
town limit, all twelve hours and both meridiems, and a ten-digit delay value fit
the original draft lines without reducing generic bounds. This checks width,
not actual actor preparation or normal rendered dialogue.

Batch cartridge loads check the complete installed messages and connected
choice replies, headers, adjacent/module guards, and restored isolated state.
All eight focused tests and 546 regression tests pass. The cartridge batch
passes 31 complete message loads and 95 assertions across 164 recorded steps,
including nine unchanged connected replies. Silent four-MiB configuration,
no seed saves, disabled save-write permissions, blank FlashRAM/Pak, checkpoint
restoration, and graceful shutdown pass. It calls only text loader `8009E558`.
These tests do not execute gifts, errands, moving, letter delivery, game choices,
sleeping residents, New Year events, or normal saving. Final wording/layout,
ordinary gameplay, save acceptance, and hardware testing remain required.
Generated evidence stays ignored under `build/resident-topics-*`; exact run
results and hashes belong in `docs/WORK_LOG.md`.
