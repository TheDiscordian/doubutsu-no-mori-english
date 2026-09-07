# Parcels, town advice, and native event corrections

## Complete English references

Forty-nine complete GameCube references have individual native-context reviews
under the [resident animation contract](RESIDENT_ANIMATIONS.md). Each approval
binds the original N64 message, complete supplied English reference, and final
encoded output. Only reviewed NPC0 slot-zero expressions may differ. Other actor
requests, fields, gameplay decisions, and buffer limits remain guarded.

| Context | Native records |
| --- | --- |
| Parcels, moved-away owners, cancelled searches, refusal, and disappointment | `019C 0209 0212 0240 0246 0260 02C2` |
| Full pockets before item/reward handoff | `033A 034B 0373 0441` |
| Four-player sharing, fruit, Nook's shop, selling, letters, moving, and boards | `0847 084B 084E 0857 0859 085B 085D 0864 0869 086B 086D 086F 0876 0877` |
| Retained/shared letters, courier teasing, repeated visits, and refusal | `090C 0911 0A69 0AC4` |
| Morning exercises, New Year's Eve, Redd's value warning, and snowman care | `0B9D 0BB8 0D67 0E8F` |
| Deferred rewards when pockets are full | `0EA9 0EAA 0EAC 0EAD 0EB0 102B 102C 102E 102F 1032` |
| Quoted phrase, gardening, town improvement, and successful rewards | `0EE7 0FC4 0FC5 0FFB 1013 1042` |

All English wording, manual lines, pages, emphasis, and pauses remain intact.
Only `0212`, `0240`, and `0246` remove the existing redundant pre-field
`CUTARTICLE` command. The full reference hash is checked before adaptation;
native field insertion does not supply that article. Other records keep the
complete encoded reference without adaptation.

The moved-away owner remains the intended recipient, not the player. Search
cancellations still require returning the borrowed item. Full pockets still
defer the reward; English localisation softens some native hurry/forgetfulness
remarks without granting an item or changing the capacity gate. The advice
retains four players in total, native A-button actions, the post-office town-tune
board, and the separate event board near the player houses. Special actors such
as Rover, Gracie, Booker, Redd, Jingle, Phyllis, and Nook are not approved merely
because their command signatures resemble resident conversation.

## Native-specific originals

`translations/n64-town-advice.json` contains eight source-hashed original drafts
for references that change the native event, weather, colour, advice, or fee.

| Native ID | Retained meaning |
| --- | --- |
| `0B8D` | Courtesy Valentine's chocolates, White Day return gifts, and effortless popularity |
| `0B96` | May carp streamers and confusion about whether to put them up, display them, or make them swim |
| `0BA8` | Thirteenth Night, lunar ninth-month day 13, the pond, and this year's converted date |
| `0BC9` | Black-bass size, visible size clues, delaying catch submission, and winning multiple prizes |
| `0F35` | Staying home to read during rain, not avoiding indoor reading during sunshine |
| `0F42` | Native yellow-green paint and using leftover paint |
| `0FA9` | The player's slightly dissatisfied town rating, not moving away |
| `1082` | Nook's 498,000-Bell final renovation, furniture space, instalments, final house size, and debt obligation |

Every native command and argument stays ordered and exact except the single
post-office colour-span length in `1082`: `7F504BA00007` becomes `7F504BA0000B`,
followed by the complete eleven-character term `post office`. That draft uses
the existing `reference_layout` validator; its focused test restricts the
exception to this one span. All twelve native pages and their waits/pauses
remain. Nook does not receive a resident-expression permission.

Fishing request `0C/5/0001`, reading request `0C/9/0003`, painting request
`0C/0/0004`, item field `33`, and the native player/town/catchphrase fields remain.
The fishing draft keeps the native hint without adding a new tournament rule.
English lines are composed within native pages; unrelated GameCube text is not
shortened or relabelled to fit.

`0BA8` requires `ordinary_dialogue_dates`. Its `3E/3F` insertions retain free
fields 18/19, prepared from lunar ninth-month day 13 by the unchanged native
conversion. The [date patch](DIALOGUE_DATES.md) supplies the English month and
ordinal day. Without that patch, the draft is withheld and the incompatible
same-ID GameCube record cannot replace it. The generic layout checker retains
its two conservative warnings for ten-fullwidth-cell free fields; a separate
check substitutes the longest English month and day and confirms they fit.
The existing date-preparation test covers ninth-month day 13, but ordinary
selection/rendering of this message remains gameplay validation.

## Read-only review queue

`tools/resident_review_queue.py` accepts the verified original ROM, the current
candidate file, and the local English reference extraction. It writes only an
ignored local review report, normally under `build/`. It excludes existing
candidates, empty native text requiring flow review, unsupported fields/actions,
out-of-range expressions, overflows, and references that cannot be re-encoded
with their complete supplied hash. A hash mismatch may be an encoding difference
or stale input; neither becomes an approval.

Every output row explicitly says `approved: false` and requires actor/topic
review. Rows contain full comparison text and command streams, not an installable
`translation` or a `resident_animations` permission. Command compatibility alone
cannot establish a matching actor, event, action, or translation. Stale installed
source hashes, mismatched reference IDs, and duplicate reference IDs fail.

## Validation scope

Focused tests verify every native source and complete command stream, the single
colour exception, dates and dependency selection, native topics/actions/fee,
expansion bounds, and layout with the approved font. Reference tests check all
207 complete resident approvals and their fourteen declared article-adapted records.
Five synthetic queue tests verify that reports cannot silently approve text.

All 451 host tests pass. The silent four-MiB batch in
`build/smoke-parcel-advice-01/` passes all 57 complete cartridge loads, with 173
assertions and 294 recorded steps. Complete headers/text, adjacent/module guards,
checkpoint restoration, blank FlashRAM, and graceful shutdown pass. Basic
generation withholds the date-dependent draft and keeps the other seven.
All previous 10,657 candidate edits remain identical. Comparing every extracted
DMA file finds changes only in main text, its pointer table, and the DMA
directory rows; the directory container's other bytes also remain unchanged.

These checks do not execute parcel handoffs, moved-resident searches, rewards,
roof painting, debt repayment, seasonal selection, or ordinary conversation.
Normal gameplay, final wording/layout, saves, human playthrough, and hardware
acceptance remain in the completion queue. Production code, runtime bindings,
font assets/spacing, and saved layouts are unchanged by this content batch.
