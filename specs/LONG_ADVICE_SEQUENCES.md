# Complete phone, furniture, and letter advice

## Content and capacity

Five complete GameCube conversations use the existing
[reviewed sequence mechanism](REFERENCE_SEQUENCES.md). These are full reference
imports, not abbreviated drafts. Each replaces one existing English page
transition with a continuing-record boundary. All wording, manual lines, pauses,
other page breaks, native fields, actor argument tuples, and final destinations
remain. No production code, buffer, font, or save-layout change is required.

| Native root and continuation | Conversation | Full expansion bound | Part bounds | Replaced page span |
| --- | --- | --- | --- | --- |
| `047C → 0486 → 046F` | Rover's phone call for another new resident | 1,049 | 155 / 912 | `[132,137)` |
| `08F4 → 0921` | Lazy resident's furniture advice | 1,031 | 535 / 514 | `[452,457)` |
| `08F8 → 2B05` | Cranky resident's furniture gift/advice | 1,259 | 623 / 654 | `[540,545)` |
| `08FA → 2B06` | Snooty resident's furniture gift/advice | 1,053 | 667 / 404 | `[584,589)` |
| `0910 → 0A26` | Cranky resident's letter-sharing advice | 1,079 | 541 / 556 | `[458,463)` |

Offsets describe encoded reference bytes, after the explicit article adaptation
for `08FA`. Every gap is exactly `04`, newline, `02`. The first part replaces
that gap with `0E target`, newline, `01`; the last part retains the reference's
native ending. All complete references and final parts have independent hashes.
Both parts of every group must be installed together.

Rover's native and English calls seek a home, give the town/player name, and
return to `046F`. The split follows the greeting, before phone mode `06`.
Its entire `06/07` pair stays in part two. Both native row-nine actor requests,
inner voice changes, final `0E046F`, and end `01` remain unchanged. The final
destination is an existing conversation, not another repurposed slot.

Furniture conversations retain collecting/accepting furniture, holding A to
push/pull/rotate it, tapping A for radios/dressers, and the work/life advice.
`08F8` uses the complete supplied English record, including the decorating,
storage, radio, and farewell pages missing from its legacy first part. The
existing legacy `0914` split does not determine this project's allocation.

`08FA` retains native item field `31` and its gift context. The native engine
never prepends GameCube articles, so only redundant `74` immediately before
that field is removed. The explicit `remove_redundant_cutarticle` member flag
requires a Boolean, an actual eligible command, and the complete unmodified
reference hash. The established adapter removes only adjacent eligible string
suppression; arbitrary unknown commands are rejected. All slices of the same
reference must agree on this adaptation and cover the whole adapted text.
The independent builder still checks all complete output hashes and native
field/action/flow restrictions.

`0910` retains jokes about received mail, sharing it, embarrassing writing,
moving with letters by train, and reading letters shown by new neighbours.
Its one-shot capitalization `75` and following catchphrase stay together in
part two. The existing resident implementation supplies this formatting; no
new runtime is added. The whole group requires the verified resident runtime.
Basic generation omits both members, and the builder rejects manual partial
or runtime-less installation. Sequence auditing treats `75` as presentation
only with that runtime, without admitting random, actor, or other flow commands.

## Continuation-slot evidence

All five selected continuation slots are native reserve placeholders with
only an ending command. `0486` is labelled train-demo reserve, `0921` part-time
work-response reserve, `0A26` letter-show reserve, and `2B05/2B06` generic reserve.
Their complete hashes are in `translations/reference_sequences.json`.

The original message-script target scan has no incoming reference to any of
these slots. A separate scan of the pinned executable/data sections finds no
matching arithmetic/comparison/logical immediate and no aligned non-executable
halfword for any of the five numbers. The regression repeats these exact checks.
This evidence applies only to these slots. It is not general proof that all
blank or reserved text is unreachable, nor an exhaustive indirect-flow proof.
Normal actor traversal remains necessary.

## Verification and limitations

Host checks reconstruct all five complete references, verify original and part
expansion bounds, retain the phone-mode pair and final link, keep capitalization
with its insertion, validate basic/runtime selection, and reject partial groups,
stale references, malformed article flags, unavailable fields, and new controls.
Existing sequence rejection tests remain applicable to every new group.

`tools/sequence_test_scenario.py` accepts repeated `--sequence` options to test
all five conversations in one isolated checkpoint. It checks all ten complete
cartridge loads, each internal continuation, Rover's final `046F` link, and both
phases of continuing/final terminators. Complete loaded headers/text, adjacent
buffer guards, module guard, and restored checkpoint remain checked.

The test does not execute the ordinary phone animation, furniture gift/handoff,
normal resident conversation, rendered formatting, or actual mail exchange. It
does not write a save or establish hardware compatibility. These remain part
of the combined gameplay and human-playthrough acceptance work. Exact results,
artifact hashes, and remaining counts belong in `docs/WORK_LOG.md`; generated
files stay in ignored `build/long-advice-*` paths.
