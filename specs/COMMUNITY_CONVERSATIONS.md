# Community conversations and native event details

## Complete English references

Seventy-five complete supplied English references have individually reviewed
native resident contexts under the [expression contract](RESIDENT_ANIMATIONS.md).
Every approval binds the full native source, complete reference, and final output.
No gameplay command, unsupported field, non-expression actor request, or buffer
limit is relaxed. The English wording, manual lines, pages, emphasis, and pauses
remain intact, even where the localisation uses fewer or more pages than N64.

| Context | Native records |
| --- | --- |
| Weather, happiness, and ordinary introductions | `0BE8 1252 1256 1257 12C4 1D3A 2A3B` |
| Fruit help, money rewards, trade offers, refusal, gifts, and bug help | `1143 1175 117A 13C8 13E5 157C 15CA 15F6 15FF 1869 1CAB 28D6` |
| Fishing, Redd, Katrina, Gracie, clothes, reading, trust, weight, and zodiac | `11D0 11E1 11E8 14E6 14E7 150C 1528 1529 16AC 16B3 16C3 16CC 16CE` |
| Blossoms, Halloween, New Year's Eve, year reflection, snow, rain, mushrooms, and turnips | `17F8 1815 181E 182A 1D6D 2772 2799 27DB 27F0 285D` |
| Hungry artist, letter impressions, former friends, rewards, letters, and bee stings | `188F 18B0 18BD 18C0 18DE 1AF1 1B16 1B26 1B69 1B8A 1C6D 1C70 1CF3` |
| Autumn, indoor food/reading/music, games, and supervising construction | `2A1A 2A46 2AAB 2C94 2CDF 2D05 2D1A` |
| New/moved residents and alternate first-meeting records | `2BB0 2BBB 2BBC 2BBD 2BC4 2BC6 2BE3 2C0B 2D4C 2D75 2DBD 2DC8 2DC9` |

The existing redundant `CUTARTICLE` adaptation applies to seven records:
`15F6 15FF 16CC 16CE 1869 18DE 2C94`. Two commands are removed in each of
`1869` and `2C94`; the other five remove one. These are nine command removals,
not removed English words. Complete original reference hashes are checked first.
All other records retain the complete encoded reference unchanged.

English localisation changes jokes and sometimes omits repeated native asides.
Examples include cheesy letters, sudden moves, celebrity vanity, zodiac-reading
compliments, and the snow/makeup pun becoming a fluffy-snow comparison. These
differences are recorded in the per-record evidence, not hidden by command
compatibility. The N64-only event, venue, schedule, or feature differences below
receive original drafts instead.

## Native actions and connected dialogue

Trade offer `13C8` retains choices `00AD/00AE/00B0`, branches
`13CD/13CE/13CF`, and the native preparation requests. The used carpet in `13E5`
still costs exactly 1,000 Bells. Outfit, fishing, weight, and zodiac questions
retain their respective complete choice and branch sequences. Zodiac response
`16CE` retains the same prepared animal/year field and quest result.

Fruit trade `1869` retains item `31`, fruit `34`, choices `0043/0034`, and
branches `186F/1870`. The native acceptance supplies field `34` and recommends
planting it; the refusal describes catching the wanted creature independently.
Letter-impression parent `18A3` retains its third choice `00A2` (`Orange`) and
target `18B0`. The English response therefore refers to the selected impression,
not an inferred roof colour. Snow question `207A`, sibling `2771`, and response
`2772` keep their connected English girls/snow joke and native decision order.

Game result `2C94` retains price `3F`, item `32`, transfer `0C/3/0012`, and
completion `0C/3/9`. `2CDF` retains `0C/3/0016` and `0C/3/000D`; `2D05`
retains the supplied payment and `0C/3/0016`. No English gambling joke adds a
wager or a new transaction. Introductory actor requests `09/2/5` and `09/8/0`
remain where supplied. Former-town field `36` stays available; references that
omit it never substitute a different town or change saved identity.

## Eighteen native-specific drafts

`translations/n64-community-conversations.json` supplies complete original
English drafts within native pages. Every command and argument remains exact
and ordered, including expression requests, waits, pauses, fields, and terminators.
There is no formatting exception, linked-record split, or larger buffer.

| Native records | Retained meaning |
| --- | --- |
| `1084` | Nook's monument, mock artist's fee, admission that Nook made it personally, no charge, and thanks for the player's custom |
| `1194 1195 17F2 17F3 17F4 27B9 280D` | Giving Valentine's chocolates, White Day return gifts, cookies, the white-chocolate misunderstanding, and March 14 |
| `11F3` | Keeping fish/insects at home without supplying food or tanks, not GameCube museum donations |
| `1689` | Both fireworks calls, Tamaya and Kagiya, and asking the player's father for their meaning |
| `17FB 1D43` | Children's Day carp streamers, the absent local Doll Festival celebration, and girls' disappointment with May |
| `1808` | The fireworks show next month, not the GameCube July 4 schedule |
| `180C 2825` | The harvest moon and pond gathering on the annually converted event date |
| `27D2` | Thirteenth Night's slightly incomplete moon and the joke that someone took a bite |
| `2811` | Blossom viewing on the 6th/7th and remembered 5th at the shrine plaza, with the miso-soup comparison |
| `2837` | The coming countdown, early sleepers staying up late, and finishing year-end cleaning early to attend |

Nook's `1084` uses no resident-expression permission; all of Nook's native
commands remain unchanged. Its seven pages keep the artist/fee joke and the
self-made revelation, rather than changing the latter into ordering a monument.
Fireworks calls retain every native short pause. The English event drafts do
not introduce Groundhog Day, a wishing well, or the Harvest Festival.

The two moon-viewing drafts require `ordinary_dialogue_dates`. Their `3C/3D`
fields are the converted lunar eighth-month day-15 date, not the current date.
The [date patch](DIALOGUE_DATES.md) already supplies English months and ordinal
days for this caller. Basic generation withholds both drafts rather than
importing the incompatible meteor-shower references. Generic fullwidth-field
layout warnings remain visible; substituting the longest permitted English
month/day confirms the actual guarded values fit without moving their line.

## Validation and remaining work

Focused tests compare every original source hash, complete native command list,
buffer bound, date dependency, and original draft layout. Semantic checks retain
native schedules, venues, creature care, reciprocal gifts, countdown invitation,
and Nook's self-made/free monument. Reference tests cover all 207 approved
complete records and exactly fourteen article-adapted records across the project.

All 457 host tests pass. The silent four-MiB batch in
`build/smoke-community-conversations-01/` passes all 93 complete cartridge loads:
93 calls, 281 assertions, and 474 recorded steps. Complete message headers/text,
adjacent/module guards, checkpoint restoration, blank FlashRAM, and graceful
shutdown pass. Basic generation includes the sixteen unconditional originals
and withholds the two date-dependent drafts. A complete extracted-DMA comparison
confirms that only main text, its pointer table, and directory rows differ from
the parcel/advice build; code, fonts, overlays, and other resources are unchanged.

These checks do not establish ordinary trade/game payouts,
bee escape, letter replies, moving, seasonal selection, pose rendering, final
wording/layout, saving, or original-hardware compatibility. No runtime, font,
spacing, executable, or saved-layout change is introduced by this content batch.

The remaining expression-difference comparisons require separate actor/state
review: Rover `0467`, Gracie `0723`, Booker `0785`, Redd `0789`, Jingle `07AA`,
Phyllis `08B0/08B2`, sleeping resident `0D3F`, title-menu records `14A2/14D9`,
and Gulliver `2403/240A/240B/240D`. They are not approved by the ordinary
standing-resident permission. Other missing fields, identity matches, control
differences, expansion overflows, general strings, and the rest of the complete
translation queue remain active.
