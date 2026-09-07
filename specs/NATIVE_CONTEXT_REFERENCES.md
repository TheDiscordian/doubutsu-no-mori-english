# Native-context English references

## Scope

This batch supplies 73 previously missing main messages: 64 complete English
references with individual payload bindings, one existing controller adaptation,
and eight original native-specific drafts. It changes text and pointers, not
runtime code, font spacing, save layouts, or native action consumers.

The GameCube presentation remains the reference. Local wording spans preserve
every reference newline and every non-colour command in their original order,
including their position relative to newlines. Colour counts may change with a
translated name. No page, wait, pause, choice, actor request, or branch is added
by a wording span. Original drafts retain native commands and arguments except
five explicitly tested sets of colour-count corrections.

## Complete-reference contract

`complete_reference` in `translations/reference_matches.json` contains the hash
of the entire adapted encoded message and, where needed, ordered `spans`.
Each span contains an exact decoded-reference character offset, `before`, and
`after`. These offsets count characters in the decoded representation, including
command tags; they are not ROM offsets or glyph-byte offsets.

The generator verifies the complete native and English source hashes before
using any span. The full English hash includes the original article command
where present. Spans must match their exact source positions, cannot overlap,
and cannot alter the combined newline/non-colour-command sequence. The normal
adapter and existing policy ladder then apply. The independent builder looks
up the repository approval and verifies the complete final payload hash, even
if an edit omits the approval metadata. Ordinary field, control, and capacity
checks still run. This contract grants no additional runtime permission and
cannot combine with animation, actor, choice, controller, field, catchphrase,
sequence, or native-alias exceptions.

The separately approved [six opening clock greetings](STARTUP_CLOCKS.md) have
an exact, restricted storage-location omission. That permission does not change
the wording-only rules or the sixty-four approvals described here.

Twelve of the 64 records need no wording changes. Fifty-two use local spans;
their remaining English text is unchanged. Individual source hashes, spans,
output hashes, and meaning notes are versioned with each record.

## Content review

| Context | Message IDs | Required native meaning |
| --- | --- | --- |
| Greetings, games, and item announcements | `050B 0670 08BF 16A4 16A5 17AF 17B5 20A8 20B0` | Evening/reunion context, Phyllis versus Pelly, native Famicom/NES feature, L/R/Z exit combination, unchanged item and choice actions |
| Shrine menu and explanation | `1124 1126` | Town status, entrusted-item apology, original menu IDs and branches; speaking shrine, not an absent well |
| Blossom venue and quiz responses | `0ADE 0AE8 0B91 26F8 26F9 27BA 27E6 287D` | Shrine plaza, fifth through seventh where stated, native quiz branches and following-the-player response |
| Exercise and sports | `0B9E 119A 11A5 11A7 11B0 1749 17FA 27BE 2705 2812` | Shrine venue, daily 6:00 exercise, July 25th where stated, no exercise in rain, April 20th spring sports where the native message gives that date |
| New Year's visits | `118E 118F 174D 17ED 17EE 26EE 26EF 27B2 2806 2807` | Annual shrine visit, January 1st, resolutions/wishes, and original year field |
| House demolition notices | `13FC 1424 144C 1474 149C 14C4` | Native action and successor retained; English power-off/removal warning names the cartridge Game Pak, not a Memory Card |
| Town-erasure notices | `1400 1428 1450 1478 14A0 14C8` | Exact native action and successor, same cartridge warning; no new destructive behaviour |
| Controller Pak errors | `0963 1406 142E 1456 147E 14A6 14CE 14DB` | No removal during use, correct controller connection, original retry/title transition, write failure rather than an invented read failure |
| Resetti | `2360 23E6` | Repeated-reset reprimand, original special-actor/mode/shake/branch commands; Booker and Tom Nook replace absent Blathers and mayor in one reference comparison |
| Development labels and Disk System | `2AE7 2AE8 2B69` | Extra-area labels and missing Disk System software; translating labels does not prove reachability |

`18CA` uses the existing `map_x_to_r` controller approval: Copper gives map item
`251D` and explains R Button viewing. The ordinary adapter restores the complete
native `0A:02:0001` argument from the GameCube's `0000`; `0A:01:0007`, all actor
requests, and the terminator remain native. This is not an animation permission.

The English reference contains two typos, `don't seen you` in `0670` and
`She so dreamy` in `08BF`. They remain visible final-wording tasks. Other
documented localisation flavour includes Copper's scolding, favourite NES
games, and the absent pie-eating contest replacing an absent bread race.
No unavailable gameplay feature is introduced by those remarks.

## Native originals

`translations/n64-native-context.json` contains eight drafts:

- `0852/085C`: Controller Pak train travel and visiting friends, without the
  GameCube destination-card/alternate-travel-card rules; private letters and
  the ticket comparison remain.
- `0962`: return travel requires the original unchanged Controller Pak, rejects
  another or overwritten Pak, and explains prevention of smuggling.
- `0BAA/11CD/2711/27D5`: Sports Day and the fall fair use the second Monday of
  October, not September or an equinox. `2711` retains the former October 10th
  date; `11CD` retains the 9:00 a.m. start.
- `285C`: repay Tom Nook to enlarge the house, not GameCube mayor/event gifts.

All eight are available without new runtime requirements. Basic generation
also admits 64 of the 65 new reference-based messages; `16A5` requires the
existing complete capitalization runtime and stays withheld without it.
Five drafts adjust
only named colour counts; all other commands and arguments remain exact. Their
conservative expansion bounds are `650 694 473 620 292 316 331 206` in file order.
The general layout warnings for town field `2F` remain in reports. A separate
host check substitutes the unchanged native limit of six fullwidth Japanese
cells and verifies these drafts fit; no automatic reflow or width-check bypass
is installed.

## Read-only identity review

`tools/identity_review_queue.py` compares unconfirmed same-ID references under
the existing policy ladder and stopping rule. It verifies reference encoding,
native source hashes, unique IDs, and current candidate state. It distinguishes
a legitimate original fallback with a rejected reference from a stale candidate/
rejection collision. It emits complete comparisons marked `approved: false`,
with no installable translation or approval field.

The current completed comparison pool is empty after these 73 messages. That
does not exhaust missing content. Among the other unconfirmed identities, 1,512
have no visible same-ID English, 102 still need unavailable fields, 38 have
control differences, eight overflow, 36 have no native static text, 24 have
unrepresentable glyphs, and one requires reference-encoding/hash review. Other
rejection categories and the separate fourteen-expression queue remain.

## Validation boundary

Host tests check exact source/reference/output bindings, overlap and stale-input
rejection, no added controls or moved delivery, independent builder rejection,
all 64 complete payloads, the eight native drafts, explicit colour differences,
native meanings, expansion bounds, and conservative layout handling.

The native batch calls only loader `8009E558` for every new record and compares
its complete header and text, adjacent memory, resident guards, and restored
checkpoint. It does not execute menu erasure commands, perform Controller Pak
travel, dispatch Resetti animations, select seasonal events, complete map
handoffs, or test normal saving. Those remain gameplay/playthrough requirements.
No hardware acceptance or final wording/layout approval is implied.

Generated candidates, coverage, read-only queues, tests, and pilot outputs live
under ignored `build/native-context-*` and `build/smoke-native-context-01/`.
Exact completed run results and artifact hashes belong in `docs/WORK_LOG.md`.
