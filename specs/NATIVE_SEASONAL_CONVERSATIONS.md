# Native seasonal conversations and related advice

`translations/n64-seasonal-conversations.json` provides 26 original English
drafts for complete N64 conversations. Each record binds its original hash and
explains why the GameCube same-ID record is not imported. These references change
native topics, omit part of the native meaning, or require different fields and
actor commands. Matching GameCube candidates elsewhere remain unchanged.

| Native IDs | Meaning retained |
| --- | --- |
| `1E09`, `1E17`, `1E2A`, `1E2B`, `1E3E`, `1E4E` | Shrine visits, queuing, self-restraint, the middle-of-the-queue aside, planning the new year, and completing the annual visit |
| `1EAF`, `1EB7`, `1ECB`, `1EE9`, `1EEA`, `1EF7`, `1EF8`, `1EF9` | Moon viewing, the inviter, dumpling offerings and appetite, a cherry-blossom-viewing callback, and the rabbit pounding rice cakes |
| `1F55`, `1F6B`, `1F76`, `1F77`, `1F78` | Returning insects, the lambada joke, winter fishing and neighbours, and both answers to the winter bug-catching question |
| `2600`, `285A` | Being too full to eat and different shop stock in other towns |
| `2008`, `252D`, `26F4`, `26F5`, `26FD` | Complete fishing/timing advice, winter flowers, March 14 White Day, and May carp streamers/rice cakes |

## Native delivery and actions

Every native command and argument remains exact and ordered, including all
pauses, pages/button waits, actor/quest requests, text fields, choices, branches,
and terminators. English lines are composed within the original native pages.
The slow proverb recital retains every native one-frame pause. Existing font
assets and advances, GameCube candidates, runtime code, and saved layouts are
unchanged.

The spring question `1F6B` retains choices `011E/0128` and branches
`1F77/1F78`. Existing English labels are `Maybe...` and `That's not true!`.
The first answer celebrates insects returning; the second describes testing
the speaker's winter training. The native quest requests remain `0C/5/0003`
and `0C/5/0067`. GameCube's spring-training question, alternate choice `006C`,
and groundhog discussion do not fit this native exchange.

Moon-viewing `1EB7` retains inviter field `26`, not the GameCube player-name
field `1A`. No field permissions or runtime-date requirements are added by this
file. The complete native text in `1E17` includes a disappointed final aside
absent from the GameCube record. The native shrine remains a shrine, not the
GameCube wishing well.

## Verification and remaining review

Focused host tests check all 26 original hashes, complete command equality,
expansion bounds, native choice/branch order, quest requests, and the inviter
field. Layout checks use the approved font advances. The conservative existing
town-name bound can flag `1F76`; this remains a presentation-review item, not
permission to resize or reflow existing text. The five
[resident conversation additions](RESIDENT_CONVERSATIONS.md) also check the
complete seven-page fishing tip and native White Day/May meanings; all five
fit the unchanged native buffer and have no conservative layout warning.

The existing batched cartridge-loader scenario verifies every complete built
message, headers, adjacent/module guards, and checkpoint restoration. It does
not execute shrine or seasonal gameplay, subsequent quest actions, ordinary
travel, or hardware saving. Final wording/layout and normal event conversations
remain part of the combined gameplay and human-playthrough review.
