# Native Pak storage and festival dialogue

## Scope

Two original draft files supply 51 messages: 26 post-office/Pak messages,
24 native carp-streamer/fireworks conversations, and a corrected existing
carp-streamer response. Fifty fill missing records; one replaces an English
candidate with the wrong conversation topic. All other candidates remain
unchanged. There are no new runtime permissions, code patches, save changes,
font changes, or wider buffers.

Every native command and argument is retained, except the explicit Controller
Pak colour count changes from nine Japanese glyphs to fourteen English
characters in messages that contain the highlighted device name. Those records
use the existing `reference_layout` policy, and tests compare the full command
sequence with only that precise substitution. All other drafts use `exact`.
There is no automatic reference reflow. The original English drafts keep native
page, pause, field, actor, choice, branch, voice, and terminator order.

## Post-office and Controller Pak messages

`translations/n64-pak-storage-dialogue.json` covers these native cases:

| Condition | Pelly | Phyllis | Retained distinction |
| --- | --- | --- | --- |
| Follow-up service menu | `08DF` | `08E0` | Mail a letter, Save a letter, Never mind; no GameCube fourth service |
| No Pak connected | `08E7` | `08E8` | A Controller Pak is required; connect one and return |
| Insufficient data capacity | `08EB` | `08EC` | Not enough free space for letters; offer native data-management route |
| Cannot continue storing | `08ED` | `08EE` | Return later; do not invent a successful save |
| Read failure | `1BD5` | `1BD6` | Check the connection and retry |
| No free note-directory slot | `1BD9` | `1BDA` | Cannot create another note, distinct from free-byte capacity |
| Damaged-Pak repair confirmation | `1BDB` | `1BDC` | Saved data may be lost; warning precedes the existing choice |
| Repair in progress | `1BDD` | `1BDE` | Do not remove the Controller Pak; retain original action and return |
| Repair declined | `1BDF` | `1BE0` | Connect another Pak and return |
| Repair succeeded | `1BE1` | `1BE2` | Continue through native `08E9/08EA` |
| Repair failed | `1BE3` | `1BE4` | Offer the original retry/refusal pair |
| Pak removed during operation | `1BE5` | `1BE6` | Do not remove it during use; check connection and retry |
| Checking Pak | `1BE7` | `1BE8` | Retain both row-nine actor requests and script return |

The supplied legacy English for `08E7/08E8` confuses an absent Pak with
unreadable/corrupt storage, while several later native errors are replaced with
bare terminators. These drafts distinguish the actual native conditions.
They do not diagnose or repair a user's Pak.

Menus retain choices `005B/009D/0015`. Both native follow-up menus route their
storage choice to `1BE7`; the draft deliberately retains that native target,
including `08E0`, where the legacy substitutes `1BE8`. Capacity prompts retain
`1BE7/08ED` and `1BE8/08EE`; directory prompts retain `08E9/08ED` and
`08EA/08EE`. Repair retry/refusal pairs remain `1BDD/1BDF` and `1BDE/1BE0`.
Repair-in-progress commands `59:04` and `09:09:0001`, successful continuation,
and `1BE7/1BE8` commands `09:09:0001`, wait, `09:09:0002`, and `19` remain.
Phyllis's grey inner remarks retain both voice controls `51:00/51:01`.

These text edits do not replace the separate [Pak persistence](PAK_MAIL.md)
implementation or its testing limitations. Native repair, note management,
storage UI progression, and error recovery still need gameplay validation.

## Carp streamers and fireworks

`translations/n64-carp-fireworks.json` covers these native conversations:

| Topic | Messages |
| --- | --- |
| Streamer appearance, symbolism, storage, and jokes | `0B97 0B98 119E 119F 17FD 17FE 26FE 26FF 27C2 27C3 2816 2817` |
| Fireworks beauty, cost, fatigue, dates, invitations, and dreams | `0BA3 0BA4 11AA 11AB 1809 180A 270A 270B 27CE 27CF 2822 2823` |
| Corrected tunnel-game response | `0BC4` |

The carp conversations retain the song's father/mother complaint, the
waterfall/advancement symbolism, outdoor versus indoor storage, mistaking
streamers for edible carp, and the backbone joke. Hungry `27C3` calls the
holiday the `Dumpling Festival`, retaining the native Tango/Dango confusion;
it does not add a food event. Its non-expression actor requests stay exact.

Question `0B98` asks whether the player has crawled through a carp streamer,
with choices `00DC/00DB` and branches `0BC3/0BC4`. Existing `0BC3` fits its
childishness/affection response and stays unchanged. Existing English `0BC4`
instead discusses social visits. The corrected native draft restores entering
through the tail, poking a head out of the mouth, shouting, and the joke about
not being a proper grown-up until trying it. Its original quest action
`0C:05:0066` and every following command remain exact.

Fireworks dates retain August, weekly Saturdays, and 7:00 p.m. where stated.
Most location remarks name the pond. Native `2823` specifically names the
shrine plaza as a place to see fireworks; that viewing-location distinction is
retained, not silently replaced. `2822` localises anticipation of happy Fridays
before Saturday shows. `27CE` retains dreams about morning aerobics.
Question `1809` retains choices `004C/0052` and branches `182F/1830`; existing
English replies about pond reflections and festival stalls fit and stay intact.

## Verification boundary

All 51 drafts are available in basic generation and require no new runtime.
Host checks compare complete original command streams, source hashes, exact
colour substitutions, capacity, native meanings, menu/repair branches, and
connected seasonal responses. Every draft fits the unchanged expansion limit.
The generic layout warnings for `27C2/2816` retain the checker's sixteen-cell
town assumption. Separate checks use the unchanged native six-cell limit with
fullwidth Japanese, and all draft lines fit. No warning is suppressed.

The cartridge-load batch includes all 51 edited records and five connected
unchanged responses: `0BC3 182F 1830 08E9 08EA`. It checks complete headers and
text, adjacent/resident guards, and checkpoint restoration in a fresh silent
four-MiB process. It calls only the loader: it does not execute repair or data
management, write a Pak, play through letter storage, select seasonal dates,
dispatch normal actor actions, or establish real-console compatibility.

Final draft wording/layout and normal gameplay remain acceptance requirements.
Generated candidates, pilot, coverage, scenarios, and test evidence stay in
ignored `build/pak-festivals-*` and `build/smoke-pak-festivals-01/`. Exact run
results and artifact hashes belong in `docs/WORK_LOG.md`.
