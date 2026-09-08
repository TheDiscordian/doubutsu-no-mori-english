# Native moving conversations and game-launch prompts

## Moving conversations

`translations/n64-moving-conversations.json` supplies eight complete native
drafts: `0FA5..0FA8`, `0FAC`, and `2862..2864`. Preserve every native command,
argument, pause, page transition, field occurrence/order/page, and ending.
English lines stay within the original pages without shortening the content.
These are native-specific translations, not substitutes for missing glyph
support or permissions to alter an actual compatible GameCube reference.

`0FA5` asks whether the player is satisfied with life in the current town.
It retains choices `0103/0104` and replies `0FA8/0FA9`. `0FA8` objects to an
equivocal answer; the existing `0FA9` objects to dissatisfaction and blames
the player for the town's state. The GameCube changes this exchange into a
question about the resident moving away. Its choices and friendship/moving
requests do not describe the original N64 conversation.

`0FA6/0FA7` retain wanting to see new places, following the player despite
refusal, growing beyond familiar surroundings, and considering a move.
`2862..2864` retain a slump, yearning for adventure, a teasing complaint about
the player's grin, physical/mental stagnation, being a drifter, and possibly
following the player to another town. These five messages retain final `00`,
with no menu or new branch. The GameCube adds moving questions and response
targets; native `2865/2866` contain only termination. Do not import those new
choices, replies, or quest actions. `0FAC` retains Tom Nook's shop-expansion
dream and advice to enlarge the player's home, not the unrelated GameCube
furniture-form/function question.

All expansion bounds fit at 281–531 bytes. `0FA5/2862` have explicit generic
current-town width warnings; every draft fits when only `2F` is substituted
with the verified six fullwidth cells, leaving all other field estimates intact.
The existing [current-town contract](REFERENCE_FIELDS.md) supplies that bound;
no global validator or runtime field allocation is narrowed.

## Seven game-launch prompts

`translations/n64-nes-launch-prompts.json` supplies `2B6B..2B71`. Their native
games are Clu Clu Land, Balloon Fight, Donkey Kong, DK Jr MATH, Pinball, Tennis,
and Golf. English titles retain the exact spelling/case in the supplied
GameCube furniture rows `036A..0370`; the Japanese launch titles are checked
individually. Same-ID GameCube main messages instead concern Memory Card errors
or town data and must not replace these prompts.

The original two-choice command remains `16:01AA:01AB`, with the same selection
indices and conditional `0F:17B5` link to the existing quit-button explanation.
Every prompt retains native continuing end `01`. The existing English labels
are I'll play! and No thanks. No embedded game, save routine, launch decision,
or controller mapping is changed.

The blue title span covers the complete English title. English word order puts
Play before that span; the brown following span covers the question mark.
Only these two `50` length arguments change. The existing `reference_layout`
policy admits the colour changes; focused tests require the exact expected
lengths and every other native command/argument. Expanded bounds are 57–66
bytes; all prompts fit the approved font without layout warnings.

## Validation boundary

Both basic and resident-runtime generation admit all fifteen drafts. Tests bind
source hashes, complete native controls, selected title sources/lengths, endings,
page/field semantics, satisfaction-question replies, absent moving menus, full
meaning, and conservative bounds. Native cartridge checks load complete messages
and the unchanged `0FA9/17B5` connections with headers, guards, and isolated
checkpoint restoration. The combined batch passes twelve focused tests, all
632 regression tests, and 116 complete cartridge loads with 350 assertions.
All 589 recorded steps complete, with a restored checkpoint, graceful shutdown,
and blank isolated saves. Results and hashes belong in `docs/WORK_LOG.md`.

No production runtime, font, or saved layout changes. Loader checks are not
ordinary moving selection, live town fields, answer actions, actual game launch
or quitting, final presentation review, save acceptance, or hardware validation.
The four long [native travel explanations](NATIVE_TRAVEL_ADVICE.md) have complete
drafts and a guarded existing-page split. Broader missing dialogue/controls and
all remaining project requirements stay in the work queue.
