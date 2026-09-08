# Remaining native menu and dialogue variants

Nine original English drafts preserve complete native meanings where the same-ID
GameCube script changes menus, branches, endings, or speaking state. They are
original translations, not shortened reference imports. No font, runtime, actor
allocation, label table, or save format changes.

| Message | Complete native meaning and retained behaviour | Expanded bound |
| --- | --- | ---: |
| `0467` | Ignore seat refusal, sit anyway, and request the player's name with native `09/09/0001`, `55`, and `01`. No train-specific expression is borrowed. | 113 |
| `0970` | Full two-line incantation and 50-Bell fortune offer, with every syllable pause, original choices, cancellation, and `0973/0970` routes. | 226 |
| `09D0` | Sound-setting confirmation: Yes reaches `09C9`; Once more returns to `09C8`. | 69 |
| `0D3F` | Entire sleeping apology to Daddy, long-ago precious turnips, admission of eating them, mumbling, and final snore. | 493 |
| `0F10` | All-day snow, wondering where the sky kept it, and the mystery observation; native `00`, without a new random follow-up. | 207 |
| `10B7` | Empty music player: listen or leave, retaining the native two-answer menu. | 100 |
| `10B8` | Named music inside: Turn on, Remove, Swap, Nothing. | 143 |
| `10BE` | Named music inside: Turn off, Remove, Swap, Nothing. | 143 |
| `17B1` | NES launch question with original play/refuse choices and `17B5` instructions. | 62 |

Every original command and argument remains exact except the two NES highlight
lengths: blue NES is three characters, and the brown question mark is one.
Their colours, order, and all other controls remain. No GameCube-only `62`
cancel behaviour or registration menu is introduced into the native music/NES
questions. All original pages and deliberate pauses remain; English phrasing
fits the existing halfwidth font without an automatic reference reflow.

The sleeping conversation keeps native `4F`, expression `13`, its complete
syllable-level pauses, and the sleeping ending. It does not invent the English
reference's waking expressions or embarrassed spoken question. The incantation
is fully transliterated from the native two distinct lines. Native `0970`'s
second choice really targets `0970`, unlike GameCube `0971`; preserve that
source branch and keep ordinary decline/cancellation traversal in the gameplay
queue rather than claim that the apparent loop is fixed or fully understood.

## Connected questions and validation

Check all nine full native command streams, source hashes, exact permitted colour
lengths, bounds, basic/full draft selection, and conservative layouts. Batch all
nine cartridge messages with the directly connected fortune/sound/music/NES
replies and every referenced choice label, using one restored silent checkpoint.
Normal item removal/swapping, music output, fortune payment/refusal, name entry,
NES start/quit, sleeping-resident animation, and weather conversations remain
separate gameplay and human-playthrough checks.

The numeric game at `2D01` remains a separate contextual-label task. The same
native size labels `01B0/00F0` occur in all three number questions
`2D01/2D06/2D0B` and clothing question `1772`. Do not rename them globally to
Less than 5/More than 5. The two other number questions already have candidates
and need the same contextual-label review; fixing only the untranslated root
would leave inconsistent answers. No shared label changes are made here.

## Verification evidence

Five focused host tests, 110 reference tests, and seven native-menu tests pass.
All nine drafts fit the native expanded-message capacity and approved font
metrics without new layout warnings. Both full and basic generation include all
nine; every earlier candidate remains unchanged.

`build/smoke-menu-followups-01/` passes 193 recorded steps: twenty full cartridge
message loads and 21 native choice-label calls, including eleven connected
fortune/sound/music/NES replies. All twenty declared returns and 83 memory
assertions pass. Independent regeneration checks every call, argument, return,
read, guard, restored stack/checkpoint, silent four-MiB execution, graceful
shutdown, and blank FlashRAM/Pak. No save files are seeded or permitted to change.
Scenario SHA-256:
`f9e525f529d56969fd527b55b07ea3593ab7031eb0c7f2e29eab71329227b2d0`.

The artifact audit checks all 12,585 installed edits and complete patch
reconstruction. Only the nine added IDs differ from the train-phone candidate
checkpoint. Runtime, font atlases, names/items/mail resources, and save layouts
remain unchanged. These isolated loads establish complete cartridge payloads,
not ordinary menu actions, actor progression, audio, or original hardware.
