# N64-specific seasonal dialogue

`translations/n64-festivals.json` translates four complete native conversations.
The GameCube same-ID records describe different events and are not imported.

| ID | Native meaning retained |
| --- | --- |
| `119C` | Approaching carp streamers; whether sea bream would be more festive |
| `27C0` | A lazy resident mistakes the coming giant carp decorations for edible fish |
| `11AC` | Lunar eighth-month day 15, its converted date, the harvest moon, and gathering by the pond |
| `180B` | Two moon-viewing nights, this year's first date, and looking up Thirteenth Night separately |

Every native command and argument remains exact and ordered: actors, pauses,
page/button waits, fields, choices, branches, and terminators. Original English
lines stay within the native pages. No matching GameCube wording or presentation
is discarded; these references concern incompatible Harvest Festival or
meteor-shower conversations.

`27C0` keeps choices `0010/0018` and branches `27E8/27E9`, not the reference's
pie question or choice `0066`. Existing response candidates fit the native
eating/refusal joke and retain its actor controls. The sea-bream/festive wordplay
in `119C` is conveyed as a comparison rather than an unrelated new joke.

The dated drafts require [English resident-date preparation](DIALOGUE_DATES.md).
Their `3C/3D` fields remain the year's actual native lunar-to-Gregorian result,
not fixed dates, current-date commands, or the GameCube meteor-shower schedule.
The builder rejects these drafts without their complete required patch.

Host tests verify all original hashes, complete commands, dependencies, native
choices/branches, and expansion bounds. Native loading covers all four drafts;
both dated messages also pass actual insertion for different years. Final
wording/layout, ordinary event conversations, and seasonal hardware acceptance
remain review and playthrough work.
