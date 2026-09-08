# Scoped number-game answers

## Current gap and intended result

The three number questions `2D01/2D06/2D0B` share native answer labels
`01B0/00F0` with clothing question `1772`. The current English labels,
Too small. and Huge!, fit the clothing context but not numerical comparison.
Use the supplied English number-game answers Less and More for the three
number questions only. Preserve clothing labels, answer indices, branch
destinations, random weights, and every English question word and timing cue.

This document records the verified source and proposed integration. No extra
choice records, count patch, numeric-menu approval, or implementation is installed.

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
An explicit answer-permutation approval must restore the original index mapping
while retaining every question byte outside those exact menu/route spans.
The existing generic native-menu adapter does not permit branch changes.

The other two complete references already retain their native menu and route
order. Their full hashes are
`cdd7eff801df84ce6474e06bf42d098b09a7f07423c8c2414f0234fc52d9fba1`
and `1adf434c92828332b9dc3d5ace590c4356d4888195acb7aed2d6484230352656`.
Use the existing complete-unchanged-menu parent contract for those two records;
do not add an unnecessary branch permutation.

The complete supplied four-byte labels are `select:025C` Less, hash
`ae5239ec63f28cd401ccd63e9f56e4ede8254a738a135ebcd33e844c18dd247f`,
and `select:025B` More, hash
`d47d7cb0e4f8fd2be5ee07826694c18917d83ca77d0a01698582d05f432db996`.
Neither has an equivalent complete existing native-bank slot. Proposed appended
slots are `01CC` for Less and `01CD` for More. Extracted reference data stays local.

## Choice-bank extension requirements

The original bank contains 460 labels. Native `m_choice_main.c` has two count
checks, confirmed in the cartridge: `80065544 = 2A0101CC` and
`80065DAC = 288101CC`. The index limit would become 462 only with the exact
appended labels and independently validated contextual menus.

The cumulative-end table stays at `00D06000`; translated data already relocates
to `02400000`. Native odd/even table reads include neighbouring words, so retain
the following zero terminator and sufficient aligned DMA padding. Follow the
guarded append-after-rebuild pattern used for Pelly's two additional messages,
without relaxing `Bank.rebuild`'s general prohibition on count changes.

Generator and builder must independently bind each new label's full reference
and final encoding, both complete question hashes, and the exact display-menu
span. A candidate's metadata cannot enable a different label or count patch.
Missing resources, stale count instructions, changed table padding, wrong label
order, or altered clothing text must fail. The native 460-slot coverage
denominator remains separate from the two added labels; do not claim two native
translations merely by extending the bank.

## Batch verification

Extend the existing contextual-menu test to load the new odd/even tail entries,
exercise both answers in all three questions, and check exact selected text,
length, index, and branch. Include invalid indices, the first/previous/last
native labels, the new exclusive count boundary, and the complete unchanged
clothing question and all three clothing replies.

Retain the number-game follow-ups and weighted outcomes: `2D02/2D03` share
`132D042D05`, `2D07/2D08` share `132D092D0A`, and `2D0C/2D0D` share
`142D0E2D0E2D0F`. Verify connected English wording agrees with smaller/larger
meaning; do not execute random payouts merely to inspect labels.
Normal choice input, all three rounds, prizes, and clothing interaction remain
gameplay/playthrough checks after the isolated cartridge batch.
