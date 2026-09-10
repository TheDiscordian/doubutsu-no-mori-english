# Complete English shop quantity units

## Native contract

Five native actors share the same eight quantity-counter families: Cranny,
convenience store, department store, supermarket, and the shop twins. Their
preparers subtract one from the displayed count before choosing a string.
Counts one through fifteen therefore select each family's fifteen entries in
order. The native bases are `0566/0575/0584/0593/05A2/05B1/05C0/05CF`.
Only eight bases belong to this array; the following words are price constants,
not the two additional families found in the GameCube code.

Each preparer uses a 56-byte frame, a ten-byte local at `sp+2C`, and the existing
ten-byte message free-string slot 8. All complete English values fit those
unchanged buffers. The native free-string setter clamps to ten, and normal
message insertion trims its space padding. No actor instruction, allocation,
resident code, RNG, item transfer, price, quantity, or saved layout needs changing.

`--english-shop-units` requires the complete source-bound 120-entry group and
verified actors, relocation files, category tables, and free-string consumers.
It shares the general-string relocation at `02600000`; no unrelated string
receives extra capacity. It works without a resident module.

## Wording and item identity

The first seven families agree completely with the supplied English references
and legacy bank. They preserve piece/pieces, sheet/sheets, suit/suits,
bunch/bunches, and bag/bags. Tool/long-object and animal counters are intentionally
empty in English. All thirty omissions are explicit, source-bound members of
the group, not missing references or deleted dialogue. The combined counter
credits these thirty exact source-bound omissions after verifying the complete
installed group and five-shop selection/capacity code; it does not treat them
as visible English words or grant credit to arbitrary empty translations.

The eighth native family counts saplings: category `29`, index zero, selects
it in all five actors. The native item is `きのなえ`; its Japanese counter `かぶ`
counts plants. The same-ID supplied English rows say turnip/turnips, which would
mislabel the native sapling. This family instead uses original sapling/saplings
drafts. Native turnip bundles continue to use family 4, bunch/bunches. No
category mapping is changed. Reserved rows beginning at `05DE` stay untouched.

The two complete native shop offer messages `108A/173D` use their supplied
English count-only wording, omitting the unit field. Preserve that wording;
do not insert counters into the messages merely to make the new resource visible.
Native preparation still supplies the complete field, and isolated insertion
fixtures test it without claiming a changed ordinary shop sentence.

One original relocation constant per actor addresses the turnip-price table
using a full item ID multiplied by four. The biased constant itself precedes
the actor; its `2F00..2F03` effective addresses are the internal `10/50/100/0`
table. The independent relocation model permits only those exact hash-bound
constants. It does not loosen arbitrary address bounds or change native pricing.

## Verification requirements

- Bind all actor/relocation hashes, the sixteen category pointers and arrays,
  all eight native bases, count arithmetic, frame/local lengths, and slot 8.
- Require complete reference/legacy agreement for the first 105 values and
  complete native sapling wording for the last fifteen. Reject partial groups,
  stale sources, shifted singular/plural values, altered wording, and other-bank
  or unrelated capacity permissions.
- Check actual native item-category boundaries and each family's counts 1..15;
  do not interpret alignment bytes or GameCube-only categories as native items.
- Verify construction both with and without resident code. Reconstruct all
  installed candidates and preserve every unrelated resource and actor.
- Load actual cartridge actors with their original relocation loader. Verify
  complete counter preparation, displayed count, empty counters, message
  insertion, stack/heap/module guards, complete save retention, checkpoint
  restoration, and blank isolated saves in a silent bounded batch.
- Leave normal shop transactions, visual polish, and original hardware as
  distinct gameplay checks until corresponding evidence exists.

## Current evidence

Seven focused tests and all 829 host regression tests pass. The independent
builder test verifies all 120 entries without resident code and every unrelated
general string. Full/basic generation adds 119 candidates, retaining the existing
bag text; disabling the option reproduces the previous candidate file exactly.
The complete pilot contains 12,876 edits, all independently reconstructed from
the cartridge, and its UPS reconstructs the complete output from the verified
original ROM. Only string data, its offsets, and DMA metadata differ from the
engine-diagnostic pilot. All five shop actors and the resident module are unchanged.

The silent native batch `build/smoke-shop-units-02/` passes 555 calls and 746
memory assertions across 2,269 recorded steps. It loads all 120 counters,
prepares counts 1, 2, and 15 for all eight families in all five actors, and
inserts 250 complete fields. Ten complete cartridge shop-message loads retain
their count-only English wording. Every actor including BSS, its provided
relocation workspace, complete saved memory, and all guards remain intact.
The emulator checkpoint is restored, isolated FlashRAM/Pak remain blank, and
shutdown succeeds. Normal transactions, visual acceptance, and original hardware
are not established by these isolated function calls.
