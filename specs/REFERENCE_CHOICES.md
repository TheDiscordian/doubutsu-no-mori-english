# Native choices in English dialogue

## Contract

GameCube shop menus can reorder actions or expose different submenus. Importing
their choice commands unchanged can attach English labels to the wrong native
selection indices. The `native_choices` approval keeps the original N64 choice
command while retaining the surrounding complete English reference.

Each record in `translations/reference_matches.json` binds the native source,
complete GameCube reference, exact choice-command span and offset, complete
native command, and final adapted payload. There must be exactly one choice
command in each source/reference record. Both commands must have the same number
of choices, and the replacement must be the actual complete native command.
Arbitrary branch changes, new choices, multiple menus, stale sources, altered
layout, and partial final-payload changes are rejected. Normal command, dynamic
field, native actor-argument, and capacity checks still run after adaptation.
The builder verifies the approved final hash independently of candidate metadata.
Controller-text and native-choice adaptations cannot share an approval.

The host parser recognises reference-only `74` without adding it to the native
command table. The ordinary adapter still removes it only directly before an
already supported native string insertion. Other occurrences remain rejected.

## Shop-service batch

The approved Nook records are `1092`, `1097`, `1098`, `10A8..10AD`, and
`10B4..10B6`. The twin-shopkeeper records are `1714`, `1719`, `171A`,
`172B..172F`, `1736`, and `1738`. These cover the service question, successful
and declined sales, orders, unavailable or unaffordable orders, full order lists,
furniture-only ordering, entrusted items, and disposal/retention decisions.

The native four-choice order is `0009/000A/01C4/000B`: turnip prices, selling,
catalog, and leaving. GameCube uses `000A/01C4/0009/000B`, and its `0009` label
means Other things. Native `0009` explicitly asks today's turnip price, so
`translations/n64-shop-menus.json` supplies the original fourteen-byte English
label `Turnip prices?`. The existing expanded choice runtime handles it without
changing any action, saved field, or controller mapping.

Sale follow-ups retain native `000C/00FA` and their sell-again/stop indices,
instead of the GameCube `0003/0004` or `004C/0051` labels. These changes retain
the native choices, not the GameCube action table. Every ordinary shop selection
still requires gameplay review; a text match cannot establish that review.

The twins' `172A` and `1737` remain withheld: even after their choice correction,
their speaker/echo control sequences differ. This approval does not relax those
controls. Other menu families require their own source and action review.

## Earlier native shop records

The native `02DC..02F0` shop range has English candidates throughout. The
GameCube's same-ID slots are empty, so five individually reviewed cross-ID
matches use later English shop responses for calling the shopkeeper, turnip
prices, a declined purchase, thanking the buyer, and receiving payment. The
normal adapter retains corresponding native actor arguments and complete
GameCube wording/layout. These are semantic matches, not identical-native-record
aliases or proof that the earlier records are reachable.

Eleven original drafts cover the remaining service, sale, price, purchase,
special-event, bagged-money, and preview records. They preserve every original
native command and argument in order, including the three-choice service menu,
item/price fields, and purchase exits `02E6/02E5`. They do not inherit the later
GameCube catalog action, extra choice, actor handoff, or continuation target.
Shop reserve slots `02F1..02F4` have separate English development labels, not
new dialogue allocations. Caller reachability, ordinary
gameplay, and final wording/presentation review remain separate requirements.

## Police-station explanations

The complete GameCube `0777/0778` explanations retain original native choices
`002F/000B`, with their existing further-explanation/refusal targets
`0778/077C` and `0779/077C`. Only the exact six-byte menu span changes; all
English wording, manual layout, pauses, emphasis, and jokes remain. Both fit
the unchanged message capacity. These two approvals are separate from the
22 shop records and do not permit unrelated actor or item-claim adaptations.
See [complete content and verification scope](GYROID_CHARM_DIALOGUE.md).

## Validation

Portable tests cover exact replacement, changed sources/references, missing or
duplicate menus, wrong offsets, changed action counts, unrelated controls, and
the independent final-payload guard. Retail-input tests check all 159 approvals,
their unchanged native choice commands, complete capacity validation, and the
source-bound original labels. The [broader native-menu batch](NATIVE_MENUS.md)
supplies 135 approvals beyond the shop and police-station explanations, with
native-specific questions and connected reply corrections where required.
The native batch generator loads selected complete messages and all labels
referenced by their decoded menus from the actual cartridge, with buffer/module
guards and full checkpoint restoration. Ordinary selection,
selling/ordering, the twins' echo rendering, and layout warnings remain combined
gameplay and human-playthrough checks. The tool does not display reports or
produce host audio.
