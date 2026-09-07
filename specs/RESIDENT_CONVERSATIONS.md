# Complete resident conversations and clothing errands

## English reference batch

Sixty-five additional complete English references use the individually approved
[resident animation contract](RESIDENT_ANIMATIONS.md). Each binds its complete
native source, supplied English reference, and final payload. Only NPC0 slot-zero
standing expressions may differ; other actor operations, available fields,
gameplay decisions, and buffer limits remain guarded. No runtime, font, or saved
layout changes are required.

| Conversations | Native records |
| --- | --- |
| New homes, reunions, friendship, and indoor introductions | `05CD 05DA 06C6 06FB 0769 076F 20E1 20EB 210B 210E 2115 2116 2175 21A4 220C 2274 2276 2289 22B3 22FC` |
| Locusts, late rain, weather, and cold-weather clothing | `1F70 1FB4 206F 23BE` |
| Furniture/carpet/wallpaper rewards, sale, no available errand, and roof colour | `2062 2063 2064 2373 23CE 23DD` |
| Gracie/Saharah rumours, guessing games, collecting, tact, friendship, eyesight, and the empty-head joke | `2120 2129 23D2 23D7 2430 243C 2527 2580 2589 2596` |
| Clothing-delivery requests and reminder | `0152 0154 0156 0157 0158 016A` |
| Recipients trying on delivered clothing | `0176 017E 017F 0180 0181 0182 0183 0184 0185 0186` |
| Failed clothing deliveries and return demands | `0190 0191 0192 0193 0194 0195 0196 0197 0198` |

All English wording, manual lines, pages, emphasis, and pauses are retained.
The existing pre-field `CUTARTICLE` adaptation removes one redundant command
from each of `0156`, `0158`, `2373`, and `2580`: native field insertion never
prepends that article. The full original reference hash is checked before this
adaptation; no English text is removed. All other references remain identical
to their complete encoded English source.

## Semantics and field ownership

The clothing requests retain recipient `25` and item `26` where supplied.
Recipients identify sender `24` and keep the native clothes-changing operations.
Failure responses still demand the original clothing back; they are not treated
as successful deliveries or replaced with generic disappointment. Complete
non-expression actor requests and gameplay command order remain enforced.

Furniture sale `2373` still asks exactly 3,000 Bells and uses native item `32`.
Roof-colour response `23DD` retains the native selected colour in `2E` and the
painting controls. Zodiac guess `2580` keeps native field `31` and its original
response mapping. The visitor's former town in `21A4/220C` comes from native
prepared fields `36/37`, not a substituted current-town field. Reunion `22FC`
retains elapsed weeks `2C`. None of these is an added-field permission.

English localisation changes some humour: the locust-name pun becomes flying
locust enthusiasm, an unknown home visitor is briefly mistaken for a plumber,
and successful zodiac guessing inspires a psychic-powers joke. These retain
the conversation's actor and outcome rather than changing a quest or event.
The Saharah wallpaper suggestion remains speculation, not an actual trade.
Gracie, Booker, Redd, Jingle, and Gulliver records are not included merely because
their command signatures resemble resident dialogue; special actors need their
own consumer/context review.

## N64-specific additions

Five original drafts in `translations/n64-seasonal-conversations.json` cover
records whose same-ID English references omit native instructions or change
the topic:

| Native ID | Meaning retained | Conservative expanded bound |
| --- | --- | --- |
| `2008` | Complete fishing advice, including reeling timing and learning the trick | 704 bytes |
| `252D` | Flowers losing vigour in cold weather and blooming in warmer weather | 287 bytes |
| `26F4` | White Day gifts in return for Valentine's gifts, and the embarrassed resident | 254 bytes |
| `26F5` | March 14 White Day and homemade presents | 176 bytes |
| `26FD` | May carp streamers and rice cakes in oak leaves | 169 bytes |

Every original native command and argument, pause, page, field, and terminator
remains exact and ordered. English lines are composed within native pages.
The full seven-page fishing explanation fits without a split or truncation.
Groundhog Day, February 2, the Harvest Festival, and the unrelated weeding
complaint are not imported into these native conversations.

## Verification boundary

Host checks cover all approved complete reference hashes, the unchanged native
consumer and actor/field/flow guards, all 26 original seasonal/advice drafts,
and the complete fishing/holiday meanings. The five original drafts have no
conservative layout warnings with the approved font metrics. Reference-layout
warnings remain visible for the later polish pass; no automatic reflow occurs.

All 440 host tests pass. A focused final animation check also confirms that
exactly the four declared references use the existing article adaptation.

The batch in `build/smoke-resident-conversations-01/` passes all seventy new
native cartridge loads: seventy calls, 212 assertions, and 359 recorded steps.
Every complete message/header matches its candidate; adjacent/module guards,
checkpoint restoration, blank FlashRAM, and graceful shutdown pass. It does not execute the
clothing handoff, subsequent outfit animation, inventory return, sale, painting,
or normal conversation. Existing native expression-selection evidence applies
only to the tested unchanged selector and values, not those ordinary gameplay
flows. Normal gameplay, final wording/layout, saving, and hardware acceptance
remain separate requirements.
