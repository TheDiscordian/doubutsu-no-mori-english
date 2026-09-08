# Context-dependent English answer labels

## Native behaviour

The native choice bank stores labels, not actions. Main-dialogue commands
`16/17/18` load two, three, or four labels into ordered rows. Determination
copies the selected row and its length and records the zero-based row index.
Conditional commands `0F..12` consult that index to select the next message.
Changing a displayed label ID does not require changing its answer index or
the associated branch destination.

The pinned `m_choice_main.c` defines this separation in
`mChoice_Load_ChoseStringFromRom`, `mChoice_Set_choice_data`,
`mChoice_determimation_set`, and `mChoice_Get_ChoseNum`. The guarded original
ROM is the execution authority. Native loading, setting, width, determination,
selected-text insertion, and conditional-command dispatch are tested together;
the source description alone is not gameplay proof.

Shared native labels are context-dependent. Circle/X can mean shapes in one
game and correctness in a quiz. Native `00B7` can mean either none or pear,
and `0010` can express agreement or refusal. Unconditional English replacements
cannot resolve those meanings. Existing English bank entries already supply
the required answers, so this implementation adds no label records, table
capacity, command, runtime hook, or saved field.

## Two complete payload approvals

`translations/contextual_choices.json` contains nineteen explicit approvals.
Each requires a complete [native-menu reference approval](REFERENCE_CHOICES.md)
and binds its original source hash, complete canonical English payload hash,
exact native menu, exact menu offset, replacement display menu, complete final
payload hash, and every destination label's source and encoded-English hashes.
There must be exactly one menu, with the same command kind and answer count.
Only existing label IDs below 460 are allowed. Each review establishes the
meaning of the question and each answer index; these are not automatic
label substitutions based on English words.

The generator first performs all ordinary source/reference, native-menu,
field, actor, layout, and capacity validation. After all bank edits are available,
it replaces only the approved menu span. Every surrounding byte stays unchanged,
including GameCube words, newlines, pages, emphasis, pauses, and native branch
assignments. Native instruction and resource files are unchanged.

The builder independently requires the final display payload, even if all
adaptation/provenance metadata is removed. It reverses only the exact menu
span, checks that the complete recovered payload matches the existing
native-menu approval, and applies every existing independent validation guard
to that recovered payload. The actual final payload, not the recovered one,
is written to the ROM. Both payload hashes, their equal lengths, and the
unique menu constrain the only permitted difference to label IDs. No generic
control-signature exception or alternative branch policy is introduced.

All referenced English label edits must be in the same build input. Their
complete source and output hashes must match, they must be nonempty plain
text, and ordinary choice-capacity validation still applies. Missing label
dependencies withhold the affected generator candidate rather than publishing
an incompatible menu. Altered labels, stale sources, displaced menus, different
answer counts, changed text, or changed actions fail validation. Basic generation
therefore retains only the mappings whose complete English labels are present;
it is not permission to ignore the English runtime's capacity requirements.

## Approved contexts

| Messages | Displayed answers | Native meaning retained |
| --- | --- | --- |
| `0B67/0B68/0B6A/0B6C/0B6D/0B6E/0B6F/0B71` | `0025/0026`: That's right! / That's wrong! | True versus false, preserving each question's actual success/failure order. |
| `1C91` | `0003/0004`: Yes. / No. | Affirming or denying yesterday's workout. |
| `246A/246B/246E/246F/2471` | `0025/0051`: That's right! / Nope! | Correctness statements, including native inverted branch-command order where present. |
| `136E` | `001E/00F9`: Just a little... / Not really. | Interest in the resident's friends versus no interest, not a pear. |
| `1868` | `0027/0056`: Let's trade! / Sorry! | Trade agreement versus refusal. |
| `1CE0` | `00DF/00DE`: PLEEEASE! / No! No! No! | Telling the resident to move versus asking the resident to stay. |
| `1FAE` | `0051/0103`: Nope! / Somewhat. | No excitement versus qualified agreement about rainy nights. |
| `20CA` | `0003/0004`: Yes. / No. | Knowing the music versus not knowing it, not cancelling the conversation. |

Eighteen menus use the complete supplied GameCube answer pairing. `1FAE`
retains the original native moderate second answer using the independently
corrected shared `0103` label, rather than importing stronger agreement.
The twelve distinct destination label records remain unchanged by this batch.
Unmapped Circle/X shape-game messages retain their exact previous payloads
and labels. Other contexts require their own approvals.

## Connected native replies

`translations/n64-contextual-choice-replies.json` adds four original drafts.
Every native command and argument stays exact, including pauses, pages,
expression requests, field repetitions, and complete endings.

- `186E` retains all three emphatic item repetitions and the original two-way
  random continuation `187B/1880`, not the reference's different weighting.
- `187B` asks for the item free of charge, retaining acceptance at `187A` and
  refusal returning to `186E`.
- `1880` retains the distinct free-item request whose refusal leads to `1872`.
- `1CE3` retains the complete native memories, refusal to change course, and
  farewell. It ends normally without the GameCube-only follow-up menu.

The existing I suppose.../Nope! labels suit the native free-item requests.
These drafts complete the directly identified Japanese reply gaps; they do
not establish ordinary item transfer, random selection, moving, or friendship
behaviour. Final wording and presentation review remain.

## Verification and boundaries

`tests/test_contextual_choices.py` checks schema and duplicate rejection,
complete native-menu parent binding, both payload directions, exact label
dependencies, source/layout/menu/action mutations, missing-label withholding,
all nineteen retail-reference cases, unmapped shape games, the native moderate
answer, builder rejection without metadata, and all four original replies.

`tools/contextual_choice_test_scenario.py` uses real cartridge text and labels.
It checks forty unique messages, including all changed/new messages, sixteen
connected replies, and an unchanged four-choice shape game. The nineteen
contextual menus supply 38 answer cases; the shape game supplies four more.
Actual native loaders, row setters, width calculation, determination, selected
text insertion, and conditional handlers execute in one isolated checkpoint.
Every selected answer is checked against its complete label, length, original
index, and exact branch destination. The shape game's original random outcome
is not executed or claimed by this test.

The conditional handlers consult singleton selection `80142640`; the tested
choice object starts at `801425C0`. Selected-text insertion uses that object's
parent message window, `80142410`, because the selection length belongs to
the parent. A separate scratch window holds the loaded text for conditional
dispatch. The fixture must not mix the scratch window's empty choice length
with the singleton's selected label. All writes are test-only and the complete
checkpoint is restored. Host audio and FlashRAM/Pak writes remain disabled.

The retail width helper rounds its sum up to an even pixel count. Instructions
`8009031C..80090328` test bit zero and add one for odd sums. Expected menu widths
apply this rule without changing any glyph advance. The pinned GameCube source
does not contain this final rounding step; the original N64 instructions take
precedence for this native width assertion.

Results and hashes belong in `docs/WORK_LOG.md`; current status belongs in
`docs/PROGRESS.md`. Broader contextual-label review, remaining native dialogue,
dynamic fields, ordinary menu rendering/input/actions, saves, human playthrough,
and original-hardware validation remain separate requirements.
