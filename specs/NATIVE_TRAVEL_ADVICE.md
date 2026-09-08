# Complete native travel advice

## Native meaning

The four messages `0848/0866/0870/087A` explain visiting another town by train
using a Controller Pak. The supplied same-ID GameCube records add second-Memory-
Card and destination-town-data rules. These are different instructions, not
compatible references awaiting punctuation support. Use complete original
translations of the N64 records and retain the native personalities and advice.

`0848` asks about friends in other towns, explains reciprocal visits and avoiding
boredom, identifies the station and Controller Pak, and asks the player to
remember. It then explains writing on another town's bulletin board, later
visitors reading the player's message, writing for that audience, and using
the home town's board the same way. All of those details remain.

`0866` retains the jock's call for a man's adventure/romance, leaving familiar
ground, new people/places, the train, the mandatory Pak, and the final reminder.
The coloured name-call suffix retains its two-character length. Its `04` wait
without a following `02` inside the station advice is retained, not normalised
into another page or silently removed. `0870` retains the cranky invitation to
barge into friends' towns or invite those friends here, broadening one's world,
the station/Pak instructions, and the warning not to forget. `087A` retains
the frog-in-a-well proverb, the country-bumpkin insult, seeing the outside
world, rejecting the idea that every town is the same, and assuming that the
player already knows how to travel because the player arrived here.

The three ordinary drafts live in `translations/n64-travel-advice.json`.
The complete long `0848` draft lives inside its explicit sequence approval.
All original commands, fields/order/page, actor arguments, pauses, page waits,
and final `00` remain; only individually checked colour-span lengths change.
All four layouts fit the six fullwidth current-town cells with other fields'
conservative estimates unchanged. Generic `2F` warnings remain on three messages.
No real GameCube reference is reflowed and no field allocation is narrowed.
The three ordinary expansion bounds are 861, 695, and 828 bytes respectively.

## Complete original translation sequence

The existing sequence approval file also accepts `source_kind: native_original`.
This is explicitly original work, not text attributed to the supplied disc.
The complete original translation is stored once with its native root ID and
encoded hash. Every member names that same complete text/hash and an ordered
slice; all slices together must reproduce the full text, with only the existing
`04`, newline, `02` boundary replaced by a continuing-record transition.
Existing GameCube groups keep their original source and permission rules.

`tools/native_sequences.py` checks the original source independently of the
member hashes. The complete draft's command sequence must match the native
root exactly except listed colour-length changes. Each colour approval binds
its command index, complete original command, and complete replacement command;
only the final nonzero length byte may differ. Additional actor permissions,
article suppression, unknown source kinds, mixed text sources, missing text,
changed pages/fields/pauses/flow, and malformed colour approvals are rejected.
The ROM builder reconstructs the complete approved slices as well as checking
the native source, each payload hash, all-or-nothing membership, incoming native
branches, final terminators, and normal per-part expansion limits.

The approval `native_normal_travel_advice` uses `0848 → 0A27`. The full draft
is 818 stored bytes with a 1,134-byte conservative expansion bound. Part one
keeps `[0,460)` and appends `0E 0A27`, newline, `01`. Part two keeps `[465,818)`,
including native final `00`. The removed `[460,465)` span is exactly the existing
page transition before the bulletin-board advice. Part bounds are 663 and 489
bytes. No wording, pause, other page, or dynamic-field occurrence is omitted.

Native `0A27` is an exact letter-show reserve label with its source hash bound.
It has no incoming native message-script target. The pinned executable-section
scan finds no arithmetic/comparison/logical/load-upper immediate and no aligned
non-executable halfword equal to `0A27`. This is specific supporting evidence,
not an exhaustive indirect-call proof or permission to reuse arbitrary labels.
Both basic and resident builds install both members together. The old reserve
label is replaced only as part of this complete approved group; its source
characters remain excluded from the unchanged text-volume denominator.

## Validation boundary

Focused tests check full reconstruction, honest original provenance, unavailable
disc donors, complete native commands even after all English hashes are changed,
colour restrictions, malformed source kinds, changed parts, omitted words,
partial groups, stale native slots, incoming branches, and the exact reserve
audit. Retail tests check all four complete meanings, capacity/layout, exact
native controls, the jock's special wait, and both generation modes.

The native scenario checks complete cartridge loading, the internal continuation
assignment, both native termination phases, adjacent/module guards, and restored
state. It does not run normal actor traversal, render live fields, travel to
another town, write a bulletin-board post, or prove save/hardware compatibility.
All twelve focused tests and the full 644-test suite pass. The combined native
batch passes five complete loads, the link, and both termination phases: ten
calls, 25 assertions, and 56 recorded steps, with restored checkpoint, graceful
shutdown, and blank isolated FlashRAM/Pak files. All 11,941 installed edits and
the UPS round trip pass. Exact results and artifacts belong in `docs/WORK_LOG.md`. No runtime code,
font metric, message buffer size, or saved structure changes.
