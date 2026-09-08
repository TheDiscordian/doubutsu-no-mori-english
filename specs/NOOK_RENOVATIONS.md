# Nook's later renovations

## Complete first-enlargement invoice

Native `107E` and English `107E` describe the completed enlargement and gradual
post-office repayment. The native bill is 49,800 Bells, not 148,000. Keep the
complete English reference, including the dry-rot and mammal-strike asides,
changing only that amount. The resulting 1,023 stored bytes have a conservative
1,039-byte expansion bound and cannot fit in one native message buffer.

The reviewed sequence `107E → 083F` splits the corrected complete reference at
its existing wait/newline/page-clear boundary immediately after the quoted bill.
Part one takes `[0,551)` and appends `0E 083F`, newline, and `01`; part two takes
`[556,1023)`, retaining final `00`. Stored sizes are 558 and 467 bytes; expanded
bounds are 574 and 483. No English word, manual line, emphasis, or explicit pause
is removed. One message transition replaces one page transition.

Native `083F` is an opening reserve with its own source hash. No native message
script targets that slot. The pinned executable-section inventory has no matching
arithmetic/comparison/logical immediate. The sole aligned halfword match outside
executable sections is at `8003C644`, within libultra's `sintable` at
`8003C5F0..8003CDEF`; it is not a dialogue lookup. These checks support this
specific reserve, not arbitrary unused-looking records.

## Numeric adaptation contract

`native_price` belongs to one repository sequence approval. All members must use
the root's same-ID GameCube reference, with no native-original or article-removal
adaptation. It binds an exact decoded-reference character offset, two distinct
positive comma-grouped amounts, a native encoded offset, and the hash of the
complete corrected English reference. Only the numeric span changes. Commands
and newline order must remain exact. The unmodified full reference is verified
first, then the corrected full reference, then complete slice coverage and each
installed payload. Other sequence guards remain in force.

Both generation and the independent builder require the replacement amount,
without commas, to be the complete numeric text at the declared native offset.
Partial numbers, command bytes, stale native sources, altered references,
incorrect amounts, omitted words, changed controls, and altered final parts fail.
The approval is not permission to change prices in gameplay or save data. For
`107E`, native encoded offset 131 contains `49800`, and decoded reference offset
755 contains `148,000`.

## Native enlargement agreement and refusal

The original drafts in `translations/n64-renovations.json` cover:

- `107F`: full repayment, desire for a still larger room, warning about expense,
  and agreement choices `00DF/000D`. Preserve `5E`, branches `1080/1081`, and `01`.
- `1081`: Nook dismisses refusal, promises no complaint over unpaid bills,
  proceeds with remodelling, and requests a roof colour. Preserve `09:09:0001`,
  choices `00A1/00A2/00A3/00E0`, branches `1085/1085/1085/1086`, and `01`.

Every native command and argument remains in its original order. The GameCube
room-or-basement offer and basement explanation are different actions and are
not imported. Existing native `1082` already explains the final 498,000-Bell
enlargement and its maximum-size limit; this work leaves that draft unchanged.
The two new drafts have expanded bounds of 421 and 322 bytes, with no layout
warnings under the approved font metrics.

## Validation scope

Eight focused host checks pass for complete reconstruction, native numeric
identity, slice coverage, capacity, original commands, layout, and source guards.
All 96 reference checks, eleven placeholder checks, and seven coverage checks
also pass. Runtime/C tests retain their separate 675-test full-suite checkpoint.

The silent four-MiB native scenario passes four complete cartridge loads, both
invoice records' continuation/termination, both agreement outcomes, and all four
roof-selection branch outcomes. All 33 calls, 51 memory assertions, and 142
recorded steps pass, with restored checkpoint, intact guards, graceful shutdown,
and blank isolated cartridge/Pak saves. The branch fixture dispatches native
handlers directly; it does not simulate choosing colours in ordinary gameplay.
Independent artifact checks verify all 12,518 installed ordinary edits and the
UPS reconstruction. Only main text, its table, and their DMA-directory container
differ from the mood-phrase pilot; unrelated container bytes remain unchanged.
Normal repayment progression, roof selection, rendering, later saving, final
wording review, and original-hardware behaviour remain separate acceptance work.
Generated outputs stay in ignored `build/nook-renovation-*` directories.
