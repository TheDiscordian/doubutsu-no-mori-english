# Complete native topics and connected English replies

## Scope

Ten original drafts in `translations/n64-topic-gaps.json` preserve N64-only
instructions, question meanings, and the complete meal-greeting jokes. Nine
fill missing records; `25FD` corrects a connected reply whose supplied English
belongs to a different joke. One separate complete GameCube approval fills
`2773` after reviewing its entire already-English snow conversation.

| Records | Native meaning |
| --- | --- |
| `0B69` | The quoted Pon Curry sign claim is false: `0B65` is failure and `0B64` success. Do not substitute the GameCube product name for unchanged native artwork. |
| `11FC` | The resident wants to move but depends on the player taking the train, and requests a trip. |
| `1D47` | Romance blossoms in this season; do not invent an explicit September date without checking the selector. |
| `2006` | Hold a net and sneak like a ninja to catch cautious insects, not a Game Boy Advance ownership question. |
| `2018` | Refill shovel holes; the resident is surrounded by holes and cannot return home all night, not an island-visit question. |
| `204B` | Ask positively whether the item is precious. Maybe... retains it via `2059`; That's not true! leads to the existing trade via `2058`. |
| `246C` | Ocean fishing along row six is true; retain `2472` success and `2476` failure, not an unverified F label on the native map. |
| `25E6/25FD` | A shy resident tries a bold greeting but says Let's eat!; Hi! elicits the proper daytime hello and thanks for the reminder. |
| `25EB` | The resident mistakenly greets with Thanks for the meal!; Evenin'! corrects it and You're welcome! continues the meal joke. |

Every native command and argument stays exact except the two complete shout
formatting spans and the separately approved display labels described below.
No missing field, new action, changed reward, altered branch, or shortened
complete translation is permitted. The original bounds in file order are
`117 340 153 209 361 267 106 211 228 235` bytes. Eight layouts have no warning;
the two shouts retain explicit-formatting review warnings.

## Complete translated emphasis

The native meal greetings each highlight eight Japanese characters and apply
`54 2D` before every character. Translate the full phrases, not an eight-letter
abbreviation: Let's eat! contains ten characters and Thanks for the meal!
contains twenty. Retain RGB `E1 1E D7`, set the exact colour count, and apply the
original 45/32 one-character scale before every English character, including
spaces and punctuation. Only the colour count and scale repetitions change.
The existing guarded `reference_layout` policy supports this formatting.

All other commands remain in their original order, including pauses, pages,
expressions, quest requests, choices, and exits. The complete scaled English
phrases fit the native line width using the unchanged approved glyph advances.
No font texture, glyph metric, voice instruction, or buffer capacity changes.
Normal rendering and final visual review remain required.

## Contextual answers for original drafts

`contextual_choices.json` permits an explicit `source_kind: native_original`
for these two original quiz drafts. A GameCube/native-menu reference parent
remains mandatory for the default source kind. An original approval cannot
collide with a reference approval and independently checks that the complete
canonical draft has every native command and argument in the original order.

Both source/candidate/display hashes, the unique menu offset, the exact two
menus, and every complete destination label remain bound. Only the menu IDs
change in the displayed version. Reverse validation reconstructs and checks
the canonical native-ID payload even when caller metadata is absent. This is
not a new control policy or permission to change gameplay. `0B69` displays
`0025/0026` and `246C` displays `0025/0051`; native answer indices and branch
ordering remain. Shared Circle/X labels remain unchanged for shape games.

Original drafts retain original-draft accounting, not reference-import credit.
Missing full English labels withhold a contextual original and remove its draft
count; they never subtract an unrelated reference candidate. Basic generation
withholds both quizzes because their complete affirmative label is unavailable
under the native ten-byte limit. All ten canonical drafts are otherwise
available without a new runtime requirement. The full pilot uses the existing
twenty-byte choice implementation.

## Complete snow conversation

Native `207A` asks whether girls use snow as makeup. Its three answers lead to
`2771/2772/2773`. The installed complete GameCube parent and the first two replies
use the English fluffy-snow/girls comparison; `2772` has its own complete
standing-expression approval. The third reply retains the same complete
GameCube localisation, preserving conversation coherence instead of mixing the
native makeup expression into that English joke.

Both versions finish happily admiring snow. Restore the native mood-one and
duration-one pair at the start of the final English page, immediately before
the same expression `0A`. Native encoded offset 64 and decoded-reference offset
192 are individually bound. Every English word, line, page, pause, original
actor-command order, catchphrase, and ending remains; the expanded bound is
281 bytes. This uses the existing page-start mood contract, not a new permission
for unrelated topics or actor values. The whole native parent answer mapping
and all three complete English reply contexts are checked together.

## Verification boundary

Host checks cover source hashes, complete native commands, full per-character
shout emphasis, exact answer mappings, independent builder rejection, draft
accounting, complete snow-reference retention, and unchanged shared shape labels.
`tools/topic_gap_test_scenario.py` batches the existing contextual-answer,
complete-message, and mood-order scenarios into one isolated checkpoint. It
retains every body assertion, rejects conflicting restore expectations, and
performs one final restore before resuming. Exact completed runs and artifact
hashes belong in the work log.

The completed combined run passes 423 native calls, 309 explicit return
assertions, and 763 memory assertions over 1,754 recorded steps. It includes
107 actual cartridge message loads, all 46 selected-label/insertion cases,
42 contextual branch cases, and all 25 mood messages with 50 order dispatches.
An independent audit checks every call and argument, every declared expected
return, restored stacks, and all complete memory reads. One checkpoint restore,
guards, silent graceful shutdown, and unchanged blank isolated saves pass.
Host verification passes nine topic, twelve contextual, 96 reference, seven
native-menu, and seven coverage tests. All 12,528 ordinary installed payloads
and complete UPS reconstruction match their independently encoded expectations.

Normal conversation selection, net/holes/moving actions, actual quiz rewards,
shout rendering, mood progression, saving, and original hardware remain separate
requirements. The poster artwork and eventual English map labels still need
their own image review. The title screen remains the first image priority.
