# Native questions, choices, and connected replies

## Complete reference imports

The 135 native-menu approvals in `translations/reference_matches.json` retain
complete GameCube English text while substituting each original N64 choice
command in the canonical payload. The explicit batch IDs are checked in
`tests/test_native_menus.py`. Together with the 22 shop, two police-station,
five additional contextual-menu approvals, the complete old-calendar quiz, and
two birthday references, 167 records use the
[native-choice contract](REFERENCE_CHOICES.md). Twenty-four reference display menus
and two original quiz drafts have separate
[contextual-label approvals](CONTEXTUAL_CHOICES.md), including
fourteen reference quiz questions in this batch.

The batch covers Halloween candy, found items, trades and rewards, guessing
games, event quizzes, resident opinions and advice, singing, early K.K.
invitations, and letter/clothing responses. Each approval follows native and
English question/label comparison, not only a matching control signature.

Each approval binds the complete Japanese source, supplied English reference,
one exact menu span, original N64 menu bytes, and complete final payload.
Choice counts and selection order cannot change. Every GameCube character,
manual newline, page, emphasis, and pause remains. Native gameplay controls
`0E..19` remain in their original order. Ordinary field, actor-argument,
command, and 1,024-byte expansion checks still apply. Candidate metadata does
not bypass the builder's independent payload guard.

The host choice adapter recognises reference-only `74` while parsing the
complete GameCube donor. It retains that command through the exact menu edit;
the existing general adapter removes it only directly before an already
supported native string insertion. A displaced or otherwise unsupported `74`
still fails. This parser change does not install a runtime command or permit
other missing fields. The native descriptor table is not modified.

## Native-specific drafts and connected corrections

`translations/n64-native-menus.json` supplies ten original dialogue drafts and
eight shared choice-label corrections. All ten dialogue drafts preserve every
native command and argument, including choice IDs, quest values, branch order,
continuations, pages, pauses, and individual scale controls. No highlight-length
exception is needed. Five drafts fill missing records; five correct existing
English candidates whose native context differs.

| Native record | Required native meaning |
| --- | --- |
| `077E` | Booker asks whether to take the item home, not whether it belongs to the player. His hesitation and shrinking speech remain. |
| `152B` | The resident explains burying and repeatedly forgetting belongings, then asks for advice. |
| `1784` | The question concerns taking a bath yesterday, not showering today. |
| `29B0` | The first real eye-chart answer is the third choice. Its English label is M, so the chart displays M. |
| `2CF3` | The speaker can afford the price; the same-ID English reference says the opposite. |
| `0AE5` | The wrong-answer reply concerns missing fireworks, not a meteor shower. |
| `1212` | The successful summer-event answer is fireworks, not a meteor shower. |
| `1218` | The native Sports Fair months are April and October. |
| `1219` | The wrong-answer explanation concerns the two annual moon viewings, not fishing tournaments. |
| `1783` | The shared wrong-answer response retains a general denial and occasional forgetfulness, without the reference's incompatible morning or mint clauses. |

The eye chart retains `01A3/01A4/01A5/01A6` (A/O/M/X), its original position
and scale, third-choice success at `29B2`, and all other choices at `29B1`.
The following `29B2` chart still displays A and keeps its original random
continuation. This is not permission to change the game's answer-selection
logic. Booker retains take/refuse destinations `0780/077F` and cancellation.
The four event replies retain `0AE0`, `121C`, and `121B` continuations and their
original quest-success/failure requests. The bathing question's random reply
routes remain, including the general `1783 → 1789` failure continuation.

The conservative bounds for these drafts range from 99 to 249 bytes. `077E`
and `29B0` retain explicit-formatting warnings for the later presentation pass;
the other eight have no conservative layout warning. These checks do not
replace final wording or rendering review.

## Shared labels

The native main-bank scan counts each occurrence inside a decoded choice
command. These eight labels have 66 total uses; changes must suit their shared
meanings, not just the newly imported question. Every replacement fits the
existing sixteen-byte English capacity; the full pilot uses its existing
twenty-byte choice implementation. No native action, saved value, or row
capacity changes.

| Choice | English label | Native main-bank uses |
| --- | --- | ---: |
| `002F` | Tell me! | 34 |
| `0036` | Again! | 9 |
| `00BF` | Moon Viewing | 4 |
| `00C1` | Christmas Eve | 3 |
| `00F8` | Play it! | 3 |
| `0103` | Somewhat. | 8 |
| `011F` | Won't warm you! | 1 |
| `0130` | It's fine! | 4 |

`002F` requests information beyond advice. `0036` repeats explanations,
exchanges, guesses, or price rounds. `00F8` requests a performance or encore.
`0103` expresses a qualified degree across several topics; `0130` reassures.
The one `011F` caller rejects food as a way to warm up. Native event labels
must agree with native schedules and linked event replies.

Do not globally rename `00CD/00CE` to True/False. The same Circle/X labels occur
in 35 menus across 33 records, including both quizzes and shape-guessing games.
The shared labels preserve the shape games. Seventeen approved quiz questions
have separate complete English answer mappings, with selected-text and native
branch verification. Explicit contexts for `00B7` (none versus pear) and `0010`
(agreement versus refusal) also have per-message mappings; their shared labels
remain unchanged. Further contexts require individual review and approval.

## Complete reviewed menu comparisons

The reviewed comparison pool contains 154 same-ID/legacy-agreeing references
that pass mechanical checks after native menu substitution. Of these, 143 have
complete donor approvals, including eight requiring contextual English labels.
Eleven receive complete original drafts: five above and six
[native-topic questions](NATIVE_TOPIC_GAPS.md). The complete `088B/2586` references
require [English birthday preparation](BIRTHDAY_FIELDS.md) and their exact
contextual acknowledgements. Runtime dependencies do not establish normal
birthday-entry, gift, or horoscope gameplay.

The complete `246D` reference requires its verified
[native old-calendar request](DIALOGUE_DATES.md#actual-old-calendar-quiz-request)
and English date preparation. Its full contextual labels retain both branches;
normal request polling, rewards, and rendered calendar text remain gameplay checks.

The original questions retain the native Pon Curry claim, row-six wording,
this-season statement, positive item-attachment question, and both meal-greeting
jokes. The related `25FD` reply retains the daytime hello correction. The actual
date-selector range, native poster readability, and eventual map artwork remain
separate integration/image checks; translated wording does not prove those.

Separate `1C6F` has a complete original two-answer letter-reaction question in
`translations/n64-letter-question.json`. Every native command stays exact:
Funny! reaches `1C70`, and Like a star! reaches `1C71`. The GameCube-only third
answer and empty native `1C72` destination are not imported. Mechanical
compatibility never approves a changed
question, platform feature, date, or action. Broader native-only dialogue,
cross-ID matching, general strings/names/mail, and special-actor controls remain.

## Verification

Seven retail-input tests check all 135 complete reference adaptations, exact
native gameplay controls and reference presentation sequences, independent
builder mutation rejection, all ten original drafts, connected quiz corrections,
shared label source/capacity/use counts, and the unchanged Circle/X policy.
The choice-adapter regression checks retained pre-adaptation `74`, its narrowly
permitted removal, and rejection outside that insertion context.

`tools/shop_menu_test_scenario.py --message-id message:XXXX` selects explicit
messages and every choice label referenced by their decoded command streams.
Without an explicit selection, it retains its all-approved-menu batch. It
verifies the complete built text before generating calls, loads real cartridge
messages and labels through the native routines, checks complete output and
adjacent/module guards, and restores the isolated checkpoint. Scenario metadata
records all selected message and choice IDs. It does not execute answers,
events, trades, item claims, or ordinary gameplay, and it produces no host audio.

The current pilot's exact test results, input/output hashes, and remaining
acceptance work belong in `docs/WORK_LOG.md` and `docs/PROGRESS.md`. Normal
question selection, answer actions, live dynamic fields, menu presentation,
save/reload, and original-hardware acceptance remain separate requirements.
