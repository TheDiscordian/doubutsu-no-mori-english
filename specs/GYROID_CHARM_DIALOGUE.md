# Gyroid, resident state responses, and police explanations

## Native-complete drafts

`translations/n64-gyroid-charm-dialogue.json` supplies 21 original translations:
two failed-errand responses, ten earlier gyroid messages, and nine resident
charm-related responses. Every original native command, argument, actor request,
field, colour count, pause, page boundary, and ending remains exact. These drafts
require no runtime extension and are included in basic builds.

`02BD` retains NPC0 slot-five request `006B`, its catchphrase, and criticism of
accepting a task but not finishing it. `02CC` retains request `0065` and the
native single expression while reassuring the player after a difficult task.
The GameCube omits the first request/catchphrase and changes the second request
to the quest row with another expression. Neither incompatible actor stream is
imported. The [native actor-request distinction](ACTOR_REQUESTS.md) remains.

## Earlier gyroid records

Native `0382..038B` have empty same-ID GameCube references. They retain the
complete original greeting, acknowledgement/acceptance, owner-message display,
item enquiry, return invitation, empty-display refusal, saving notice, and
post-save farewell. These are actual native records, not inferred normal-gameplay
reachability or a port of a later GameCube menu.

`0382` retains three choices `0013/0014/0015`: Revise, Store an item, and Never
mind. It gains no save choice or explicit branch assignments. `0386` retains
Check items/Never mind (`0016/0015`) and its original expression after choice
initialisation. The owner-message record `0385` retains insertion `40`, its
existing `0386` link, and continuing ending `01`. It does not change the
[owner-message storage/display contract](GYROID_MESSAGE.md).

The saving notice keeps the full power-off warning, blue Saving text, red
warning text, and original wait/page/continuation placement. Translating this
notice is not a save operation or proof of normal save-menu execution.
Acknowledgements remain distinct from accepting a request and thanking a visitor.

## Complete resident state responses

The nine records are `0761`, `0763`, `0767`, `0768`, `076A`, `076B`, `076C`,
`076E`, and `0770`. All retain native state command `41` at its original place
among the other commands and end with native `00`. Their complete responses
include initial attraction followed by retraction, regaining composure,
waning interest, and puzzlement about changed feelings.

Six same-ID GameCube records contain only the first part and branch to
`3057..3062`, beyond the original N64 message bank. Those partial texts and new
branches are not substituted for complete native responses. The other three
retain native requests `09:02:0001` and `09:08:000A` while keeping `41`, which
the GameCube record omits. The two highlighted shouted names retain their exact
two-character colour spans, using the corresponding English exclamation marks.
No actor-expression permission, state transition, or font change is added.

## Full GameCube police explanations

The individually hash-bound `0777/0778` approvals use the existing
[native-choice adaptation](REFERENCE_CHOICES.md). They preserve all supplied
GameCube wording, lines, pages, pauses, jokes, and emphasis. Only each six-byte
choice command changes to original `16:002F:000B`. The current English labels
are Any tips? and Never mind; their indices preserve further explanation versus
refusal. `0777` still targets `0778/077C`; `0778` still targets `0779/077C`.

`0777` retains twenty-item lost-property capacity, oldest-first disposal, prompt
collection, and the distinction from an ordinary lost-and-found desk. `0778`
retains free entry, claiming recovered items, the lack of punishment for false
claims in the town, and Copper's concern about his role. Both full records fit:
expanded bounds are 833 and 747 bytes. Neither needs truncation or new pages.
Source/reference/full-payload hashes, exact menu spans, complete native actor
sequences, existing branch targets, and final `01` are independently validated.

Booker's separate `077E` question still needs native wording/context work:
the N64 asks whether the player will take an item, while the GameCube asks if it
belongs to the player. Its control compatibility alone is not an import approval.
Introductions `04D2/04FA` require the unsupported semicolon glyph in their full
GameCube references; they are not rewritten as unrelated native drafts merely
to avoid that font-support task.

## Verification boundary

Host tests cover every full native source hash and exact command sequence,
basic-runtime selection, both gyroid menus, the owner-message continuation,
warning placement, all state commands and final actor requests, coloured shout
lengths, complete retractions, capacity, and the two full reference approvals.
The independent builder rejects changed police payloads regardless of edit
metadata. All new static English lines fit the approved metrics.

Only the generic owner-message insertion in `0385` has a conservative width
warning. It reserves a full embedded-mail field as one line; the actual custom
owner-message formatter has its own bounded wrapping contract and tests. The
warning is retained, not suppressed by reducing generic expansion bounds.

Native cartridge-load checks verify full headers/text, adjacent/module guards,
and restored isolated state. They do not execute ordinary gyroid menus, saving,
custom owner messages, charm state changes, police choices, or item claims.
Normal gameplay, live fields, final wording/presentation review, saves, and
hardware remain requirements. Exact results and artifact hashes belong in
`docs/WORK_LOG.md`; generated evidence stays in ignored build directories.
