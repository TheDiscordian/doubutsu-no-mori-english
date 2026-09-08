# Scoped number-game answers

## Installed behaviour

The three number questions `2D01/2D06/2D0B` share native answer labels
`01B0/00F0` with clothing question `1772`. Too small. and Huge! remain in
the clothing context. The three numeric questions instead use the complete
supplied English answers Less and More through dedicated appended slots.
Clothing labels, answer indices, branch destinations, random weights, and
every English question word and timing cue remain intact.

`tools/extended_choices.py` appends the two four-byte labels and patches only
the two native choice-count instructions. It requires a successfully validated
contextual display menu; builds without those messages do not append labels
or change the count. No resident module, font, or saved layout changes.

## Exact reference mapping

| Native question | English menu offset | Native answer-zero / answer-one destination |
| --- | ---: | --- |
| `2D01` | 115 | `2D02 / 2D03` |
| `2D06` | 92 | `2D07 / 2D08` |
| `2D0B` | 94 | `2D0C / 2D0D` |

All three native menus are `7F16 01B0 00F0`: smaller first, larger second.
The supplied English `2D01` instead uses `7F16 025B 025C`, More then Less,
and swaps the two branch destinations. Its full hash is
`645ae0a5fada2ef27938a8d692237d6aeb3b7077ebf03dd7350299de6a42f24b`.
Its menu starts at 115, `0F 2D03` at 125, and `10 2D02` at 129.
An explicit answer-permutation approval restores the original index mapping
while retaining every question byte outside those exact menu/route spans.
The optional `answer_permutation: [1, 0]` maps each native answer index to its
corresponding reference index. Both scripts must have one contiguous ordered
branch per answer. Each mapped destination must agree before adaptation, and
the adapter restores the exact native destination for each opcode. Duplicate,
missing, identity, non-integer, partial, and destination-changing mappings fail.
Only this root declares the permission; ordinary menu approvals retain their
menu-only behaviour. Full reference and adapted-output hashes remain mandatory,
and the independent builder retains the normal native flow check.

The other two complete references already retain their native menu and route
order. Their full hashes are
`cdd7eff801df84ce6474e06bf42d098b09a7f07423c8c2414f0234fc52d9fba1`
and `1adf434c92828332b9dc3d5ace590c4356d4888195acb7aed2d6484230352656`.
The complete-unchanged-menu parent contract applies to those two records;
neither has a branch permutation.

The complete supplied four-byte labels are `select:025C` Less, hash
`ae5239ec63f28cd401ccd63e9f56e4ede8254a738a135ebcd33e844c18dd247f`,
and `select:025B` More, hash
`d47d7cb0e4f8fd2be5ee07826694c18917d83ca77d0a01698582d05f432db996`.
Neither has an equivalent complete existing native-bank slot. Appended
slots are `01CC` for Less and `01CD` for More. Extracted reference data stays local.
Label bindings explicitly use `source_kind: appended_gamecube`, with complete
reference IDs and hashes; their source hashes do not identify absent N64 labels.
Only these two registered bindings are accepted. Generation checks the actual
supplied references, while construction verifies the complete registered
encodings independently of candidate metadata.

## Choice-bank extension requirements

The original bank contains 460 labels. Native `m_choice_main.c` has two count
checks, confirmed in the cartridge: `80065544 = 2A0101CC` and
`80065DAC = 288101CC`. The index limit becomes 462 only with the exact
appended labels and independently validated contextual menus.

The cumulative-end table stays at `00D06000`; translated data already relocates
to `02400000`. Native odd/even table reads include neighbouring words. The
following zero terminator and aligned DMA padding remain. The guarded
append-after-rebuild pattern follows Pelly's additional messages;
`Bank.rebuild`'s general prohibition on count changes remains unchanged.

Generator and builder independently bind each new label's full reference
and final encoding, both complete question hashes, and the exact display-menu
span. A candidate's metadata cannot enable a different label or count patch.
Missing label resources withhold the affected contextual candidate. Changed
references or label bytes, stale count instructions, changed table padding,
wrong label order, and altered approved question text fail. The native 460-slot coverage
denominator remains separate from the two added labels; do not claim two native
translations merely by extending the bank.

## Batch verification

The contextual-menu batch loads the new odd/even tail entries, exercises both
answers in all three questions, and checks exact selected text, length, index,
and branch. Eight boundary indices are `-1, 0, 459, 460, 461, 462, 463, 32767`;
the test calls both the actual table reader and label loader, including unchanged
destinations on invalid input. It includes all 29 contextual menus, the complete
unchanged clothing question and its three replies, all number-game follow-ups,
and the unchanged shape menu: 73 complete messages and 66 answer cases.

Retain the number-game follow-ups and weighted outcomes: `2D02/2D03` share
`132D042D05`, `2D07/2D08` share `132D092D0A`, and `2D0C/2D0D` share
`142D0E2D0E2D0F`. The connected complete English references explicitly repeat
smaller/less versus bigger/more than five, matching the preserved indices.
Random payouts are not executed merely to inspect labels.
Normal choice input, all three rounds, prizes, and clothing interaction remain
gameplay/playthrough checks after the isolated cartridge batch.

## Verified scope

All 26 choice tests pass, including seven number-game/extension tests. The full
803-test regression suite passes. The complete installed audit verifies all
12,603 candidate edits, both additional labels, unchanged original 460 labels,
exactly two changed executable instructions, and original-ROM UPS reconstruction.

`build/smoke-number-game-01/` passes 2,003 recorded steps, 510 native calls,
331 declared returns, and 817 complete memory assertions. All six numeric
answers retain their native routes; all three clothing answers remain intact.
Independent scenario regeneration checks every call/argument/return, complete
read, and fixture write. Buffer/module guards, stack/checkpoint restoration,
silent four-MiB configuration, blank isolated FlashRAM/Pak, and graceful shutdown
pass. These isolated calls do not establish ordinary gameplay or hardware.
