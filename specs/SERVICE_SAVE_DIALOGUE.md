# Native service menus, travel errors, and save dialogue

## Scope

`translations/n64-service-save-dialogue.json` supplies 47 original drafts for
native messages whose GameCube references change menus, actor delivery, storage
conditions, or entire topics. Ten cover the post office, four the home gyroid,
fifteen station/Pak conditions, and eighteen six personalities' save prompts and
acknowledgements. Every draft is available without optional runtime features.

These text edits do not change executable code, actor logic, save formats,
fonts, buffer limits, or the English reference permissions. They preserve the
complete native command stream, including page/pause order, fields, voices,
expressions, actions, choices, cancellation, branches, and endings.

Only these colour counts change where the source contains the corresponding
highlighted term:

| Native command | English command | Complete highlighted term |
| --- | --- | --- |
| `50:198CDC:09` | `50:198CDC:0E` | Controller Pak |
| `50:E11ED7:06` | `50:E11ED7:09` | town data |
| `50:4BA000:02` | `50:4BA000:07` | station |

Those drafts use `reference_layout`. The focused tests impose the stricter
whole-command comparison with only these exact substitutions, then check the
complete following term. All other drafts use `exact`. Native English drafts
are composed within the retained native pages; no GameCube text is automatically
reflowed, truncated, or treated as equivalent merely because its ID matches.

## Post office

`08CF/08D0/08D1/08D2/08DD/08DE` retain the native three-choice service menus:
Mail a letter, Save a letter, and Never mind. All selection indices and targets
remain. The GameCube e-Reader service and its fourth branch are not imported.
Native `08DE` targets `1BE7` for storage despite the legacy's `1BE8` substitution.

`08B2` is the distinct four-choice Phyllis menu: Mail a letter, debt payment,
Save a letter, and Never mind. It retains choices `005B/005D/009D/0015` and
targets `08B6/08D4/1BE8/08B4`. The longer native greeting and every expression
remain; no standing-resident expression permission is granted to Phyllis.

`08D3/08D4` retain the two original amount fields `25/26`, Pelly's polite
payment prompt, and Phyllis's muted disbelief. Native `04`, `19`, and `01`
remain at the hand-back boundary; the GameCube's `55` is not substituted.
The two generic free-field width warnings stay visible. Actual payment amount
preparation and rendered width remain gameplay validation, not loader evidence.

`08B0` is Phyllis's full outgoing-mail queue refusal. It retains her four grey
inner remarks, asking Pete for an extra delivery, telling the player to return
later, and the impatient farewell. Every native expression, voice toggle, and
pause remains. The GameCube's different expression sequence is not installed.

## Home gyroid

`0925/0927/0936` retain Revise, Store an item, Save, and Never mind, in native
choice order `0013/0014/005E/0015`, with targets `0927/0927/092D/0926`.
`0936` still adds sale proceeds to carried Bells and retains its sound command.
Neither the GameCube's house-options submenu nor its different save route is
introduced. Connected native `092D` tells the player to enter the house.

`0932` is the native saving notice, with the power-off warning, save request,
and continuing end. Its GameCube same-ID door-management menu is unrelated.
The different GameCube uses of native diagnostic `092F/0930/0931` and blank
`0933` are not permissions to transplant their action trees. Those native
records remain in the separate coverage/flow queue.

## Station and Controller Pak

| IDs | Native condition retained |
| --- | --- |
| `0946/0947` | Declined/accepted erasure of the named existing traveller record at `0945` |
| `0948/0951` | Insufficient free bytes versus no available note-directory slots |
| `094C/094D` | Cannot travel after refusal versus acknowledgement of trying Pak organisation |
| `094F` | Save the player to the Pak and update native town data; both power and removal warnings |
| `0952` | Damaged Pak: ask to repair, with explicit possible saved-data loss before the choice |
| `0953` | Repair in progress; do not remove the Pak |
| `0954` | Repair declined: connect another Pak and return |
| `0955` | Repair succeeded: continue departure preparation through `094B` |
| `0956` | Repair failed: offer retry/refusal through `0953/0954` |
| `0957` | Pak removed during an operation; reconnect and return |
| `095E` | A connected Controller Pak is required to board the train |
| `0967` | Pak write failure; reconnect and return |

The legacy mislabels several conditions: `0947` describes missing town data
instead of approved record erasure, `0952` describes failed repair instead of
asking to repair, `0954` claims successful repair after refusal, `0955` describes
saving instead of repair completion, `0956` asks to format instead of retrying
repair, and `0967` describes changed town data instead of write failure.
The drafts preserve the native meanings and exact action targets. They do not
attempt repair or formatting, diagnose user storage, or add any destructive
operation. Actual Pak actions remain covered by the separate
[persistence contract](PAK_MAIL.md) and gameplay acceptance requirements.

## Save and quit versus save and continue

The six native question/quit/continue triples are `2B09/2B0A/2B0B`,
`2B0C/2B0D/2B0E`, `2B0F/2B10/2B11`, `2B12/2B13/2B14`,
`2B15/2B16/2B17`, and `2B18/2B19/2B1A`. Every question retains choices
`01AE/01AF` and its exact two successors. All twelve acknowledgements retain
the power-off warning before `59:04` and `09:09:0001`, the wait before the
completion page, original expressions, and final `00`. Quit variants say
farewell; continue variants invite continued play and retain their extra pause.
GameCube same-ID card/region/town-data errors are not imported.

## Verification boundary

Host checks compare every complete native source and command sequence, all
three colour substitutions, capacity, menu/action mappings, repair conditions,
warning placement, save-versus-continue wording, native choice identities, and
layout. All drafts fit the unchanged 1,024-byte expansion budget. Only the two
documented payment amount-width warnings remain; no warning is suppressed.

The cartridge-load batch includes all 47 drafts and seventeen connected unchanged
messages: `08AF 08B1 08B3 08B4 08B5 08B6 1BE7 1BE8 0926 092D 0945 094B
0950 0962 0963 0964 0965`. Complete loaded headers/text, adjacent/module guards,
and checkpoint restoration are checked in a fresh silent four-MiB process.
This only loads message data. It does not execute service selection, payment,
Pak management/repair, saving, ordinary actor interaction, or real-console tests.

Normal UI flows, amount preparation, dynamic rendering, original wording/layout
review, save/reload, and hardware remain acceptance requirements. Exact results
and artifact hashes belong in `docs/WORK_LOG.md`; generated evidence stays in
ignored `build/service-save-*` and `build/smoke-service-save-01/` paths.
