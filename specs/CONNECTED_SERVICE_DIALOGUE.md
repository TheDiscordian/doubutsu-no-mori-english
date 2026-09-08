# Native service conversations and connected answers

## Complete native-specific drafts

Fifteen original drafts in `translations/n64-connected-services.json` preserve
complete native meanings where the supplied English script changes gameplay,
adds an unavailable field, or changes the native topic. Every native command
and argument remains exact except complete echo colour/scale spans below.
No new runtime action, missing-field permission, or saved format is introduced.

| Records | Native meaning and action retained |
| --- | --- |
| `1722` | Special event and rare-item sale, with two complete twin-speaker pairs. |
| `172A` | Unavailable order, different supplier, separate apology, and all five exchanges; original four-service order. |
| `1737` | Taking unwanted items, separate acknowledgement, three exchanges, and original four-service order. |
| `1889` | Gracie's popular clothes are unavailable for money; advice criticises the current outfit. No new catchphrase field. |
| `1CD7` | Remembering a resident after moving away: Naturally! / I have no idea. retain `1CD8/1CD9`; no third answer. |
| `1D27` | Thanks for offering help in bad weather, but no current errand; no GameCube-only quest request. |
| `2065` | Gift-category insistence retains both native preparations; No way! repeats this same question. |
| `2077` | Uncool catchphrase question and accidental repetition; Maybe... requests a replacement, while denial reassures. |
| `23DC` | Selected paint colour is compared with falling rain, not the sky. |
| `2769` | Brown paint and almost-forgot aside, retaining native `276A/276B/276C`, not GameCube `276D`. |
| `2798` | Suspenseful lead-in retains all four pauses, `2799/279A`, and the original `19/01` ending. |
| `2CD0` | Full forced-sale item/price/catchphrase, original item and transaction requests; no extra preparation. |
| `1502/1D3D` | Disappointed repayment answer and angry attention/advice response; no added GameCube persistent-mood orders. |
| `28EE` | Complete mock-shopkeeper sale, last-moment purchase, panic question, final unchosen item, and invitation to play again. |

The original gift menu is Furniture! / Carpet! / Wallpaper! / No way!.
Its fourth branch returns to `2065`; GameCube's alternative `2068` is an empty
native message. The moving question's third GameCube destination `1CDA` is
also empty natively. Neither is made into a new native action. Catchphrase
answers retain `2774` for the existing editor and `2775` for reassurance.
The native brown-paint follow-up can still select its original too-flashy
remark; this text batch does not rewrite the actor's selection logic.

All existing shared choice labels remain unchanged. Ordinary menu selection,
custom catchphrase entry, trades, paint, friendship, and moving behaviour
remain gameplay checks, not consequences inferred from translated questions.

## Complete twin-speaker echoes

`1722/172A/1737` retain two, five, and three native `5C/5D` pairs respectively.
The complete English echo lengths are 8/7, 6/10/8/7/8, and 7/12/8.
Retain RGB `198CDC`, eight-pixel line anchors, and 26/32 character scaling
across every English character, including punctuation. Only exact colour
lengths and repeated scale controls change. The existing `reference_layout`
guard handles those spans; all speaker/page/wait/pause/gameplay controls stay
exact. No incomplete echo or GameCube-only speaker boundary is imported.

The three echo records retain explicit-formatting warnings for the polish pass.
The other twelve drafts have no conservative layout warning. Original English
draft lines are placed to fit complete dynamic fields; this does not reflow any
GameCube reference or alter its timing. The separate
[random-response imports](NATIVE_RANDOM_REFERENCES.md) retain all supplied
English wording and presentation with only their native branch restored.

## Verification boundary

Five focused tests check all complete sources, original commands, buffer bounds,
menu/reply relationships, unavailable empty branches, retained fields/requests,
ten complete formatted echoes, and basic/full draft availability. They pass.
Cartridge loading, regression results, exact artifacts, and remaining acceptance
are recorded in the work log. No ordinary service, twin rendering, saved-game
round trip, or original-hardware validation is implied by those text checks.

The combined native batch passes 39 complete cartridge messages, eighteen menu
labels, 57 calls, 39 declared expected returns, and 137 memory assertions over
276 recorded steps. All nineteen new original/reference records and twenty
connected replies load completely. Independent scenario regeneration, every
call argument/return/read, guards, one restored checkpoint, silent shutdown,
and blank isolated FlashRAM/Pak pass. All 104 reference tests also pass,
including the eight separate random-reference checks. All 12,557 installed
edits and full UPS reconstruction pass; earlier full/basic edits are unchanged.
