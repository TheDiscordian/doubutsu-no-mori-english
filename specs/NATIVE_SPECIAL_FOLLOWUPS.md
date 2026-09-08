# Native special-dialogue follow-ups

Three complete native-original drafts and one complete GameCube furniture-sale
reference fill distinct remaining dialogue gaps without changing runtime code,
font metrics, saved layouts, or shared menu labels.

| Message | Retained complete meaning and behaviour | Expanded bound |
| --- | --- | ---: |
| `203C` | Surprise at the player's money, part-time-job joke, 1,000-Bell sale, choices `0044/0056`, and routes `2041/2042`. Full GameCube wording and presentation, with the exact original mood pair restored. | 445 |
| `23EB` | Repeat the shown phrase; all colours, pauses, free-string field, input request, native `55`, and final `01`. | 145 |
| `23FE` | Waking, disorientation, remembered wave, admission of falling from the safe boat, rescue thanks, the already-said-thank-you joke, and gift offer. | 823 |
| `2513` | Stop resetting, original two answers and acceptance route, plus fallback `2515/2516/2516`. No GameCube-only `2517` branch. | 108 |

The three original drafts retain every native command and argument exactly.
The reset warning keeps `Got it!`/`No way!`; the sale keeps `Sure!`/`Sorry!`.
These are the existing translated labels in their original native slots/order.
Their full wording fits the approved font metrics with no layout warnings.
Gulliver does not request the GameCube-only date field or different expressions.
The furniture-sale reference retains its conservative dynamic-money width
warning for presentation review; it is not automatically reflowed.

## Native sale mood

The original `203C` supplies mood one and duration zero immediately after quest
`0C/02/0003` and before surprise expression `09/00/0002`. Its complete GameCube
reference omits that pair. An exact `after_sale_quest_before_surprise` anchor
restores `09020001/09080000` at the same initial point without changing any
English text. Duration zero is not changed to one, and is accepted only with
this explicit quest/expression anchor. Source/reference/output hashes, complete
actor order, choices, fields, capacity, and native consumer checks remain.
The existing adapter removes only redundant `74` before the native item field.
See [mood contract](NATIVE_MOOD_REFERENCES.md).

## Apology target and editor integration

Native Majin3 overlay `00898220`, linked at `809B4A10`, loads one of sixteen
strings `0484..0493` into the ten-byte prompt field. `809B4FC4` selects the index
and publishes it through `8009D88C`. The index is actor byte `956`; the reply
starts at actor `94C`. `809B4BB8` reloads the same target and compares all ten
bytes. Both display and matching therefore need the same complete padded string.

Fourteen target strings already have complete English candidates. `048E` and
`0491` still require the English sun/skull glyphs. Do not silently substitute
different phrases or claim the apology editor is fully translated because its
prompt is English. Native English-first input still needs caller-level validation
for the complete target set, case, symbols, padding, retry, and acceptance.

The rude-reply detector `809B4C18` scans all 32 strings `04C0..04DF`, using a
hard-coded increasing substring length and ten-byte reply window. Its native
length-transition table at `809B572C` contains `6, 16, 25, 30, 31, -1`,
confirmed from the retail overlay. The GameCube uses different transition
indices. The native match-length starts at two and grows at those indices.
Only `04C0` currently has an English candidate. Importing the other
English strings without updating storage and the length contract would change
matching incorrectly. Keep complete string-bank integration and detector tests
with the apology/editor work; no detector or target string is modified here.

## Acceptance

Verify complete native command streams, source hashes, reference reconstruction,
all four bounds, mood anchor rejection, and unchanged connected menu labels.
Batch actual cartridge loads with connected sale, apology, and reset-warning
replies, and execute the native mood/timer writes in the same isolated run.
Restore the checkpoint, retain blank FlashRAM/Pak, disable host audio, and verify
all complete buffers and guards. Normal purchases, currency changes, apology
entry/retry/acceptance, Gulliver rescue/gift delivery, and random outcomes remain
separate gameplay requirements.

## Verified scope

Five focused tests cover draft selection, full native hashes/commands, bounds,
layouts, apology colours/input handoff, complete Gulliver meaning, and native
reset menus/random destinations. Fourteen mood tests include strict zero-duration
anchor rejection and complete reference reconstruction; all 111 reference tests
and nine topic/batching tests pass.

`tools/special_followup_test_scenario.py` combines fourteen selected messages
(four additions and ten connected replies), their four native choice labels,
and all 26 approved mood messages in one isolated checkpoint. Forty complete
cartridge loads, four label loads, and 52 order writes pass: 96 calls, 92 declared
returns, and 237 memory assertions. Every call, read, fixture write, guard,
restored checkpoint, and blank save matches the independently regenerated
scenario. Audio is disabled and no save seed or write permission is used.

The complete installed-payload and UPS audits pass. Full/basic generation adds
only these four messages, with no reserve allocation or earlier edit change.
Runtime, both font atlases, names, items, mail resources, and saved layouts remain
unchanged. Logs and hashes belong in the work log. These are draft/candidate and
injected-call results, not ordinary gameplay or final semantic/hardware approval.
