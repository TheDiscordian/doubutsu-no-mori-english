# Complete Katrina fortune fragments

## Source and destination contract

The native fortune preparer `809DC590..809DC608` selects one of 32 strings
from each of four bases, in item-field order: `01A4`, `01C4`, `0184`, `0164`.
All 128 complete supplied English references agree with the complete legacy
values at the same native indices. Every phrase fits sixteen plain text bytes.
The phrase order is adjective, noun, activity, then place. Native selection
consumes one existing RNG call per field; the fortune effect and price are
separate operations and remain unchanged.

The native 48-byte frame stores its ten-byte local at `sp+24` hexadecimal and
the input field number in the caller argument slot at `sp+30`. The scoped patch
grows the frame to 56 bytes, retains the local at `sp+24`, moves all three
argument-slot references to `sp+38`, and passes sixteen to both the string
loader and item setter. The return address stays at `sp+14`. File, BSS, and
relocation sizes remain unchanged; none of the seven changed words is relocated.

The resident main-window item setter and insertion path already preserve
sixteen-byte values. Installation requires that verified resident module.
No new resident code, allocation, font metric, actor identity, or save format
is needed. Existing native item fields retain their ten-byte compatibility copy.

## String storage and permissions

An enabled build relocates the complete general-string data bank from `00D16000`
to `02600000`, retaining its cumulative table at `00D18000`. Only the existing
data-address instruction pair at `800C3F1C` changes. The native 1,562-entry
count, sixty-four-byte getter limit, DMA staging, and caller copy limits remain.

Capacity permission belongs only to the complete 128-record group, independently
bound to the original bank and a length-prefixed digest of all complete English
values. Each permitted record additionally binds original and output hashes.
Missing, duplicated, changed, shortened, reordered, non-text, and overlong
records fail. Other string IDs retain their original entry budgets. Candidate
metadata cannot grant capacity. The generator and builder both require the
explicit English-fortunes option and a resident module; partial installation
must not leave long fragments feeding the old ten-byte caller.

## Verified scope

All seven focused tests and the complete 810-test host regression pass.
Construction reconstructs all 12,711 candidate edits and every general-string
entry, including unchanged non-fortune entries, and verifies the original-ROM
UPS round trip. Disabled generation reproduces the 12,603-edit candidate file
exactly. The complete relocated data file is 8,032 bytes; the ROM remains 32 MiB.
The source address inventory finds only the original DMA entry and the guarded
main-code address pair for the exact string-data base.

`build/smoke-fortune-01/` passes 2,112 recorded steps, 459 native calls, and
888 complete memory assertions. All 128 phrase loads, 128 actual preparations,
32 independent original RNG calls, 32 complete reading loads, 128 full message
insertions, and eight native table boundaries pass. The actual overlay comes
from the cartridge and relocates into a bounded native heap allocation; no
replacement actor code is uploaded by the debugger. Stack locals, neighbouring
native fields, complete saved memory, heap/stack/module guards, restoration,
blank isolated FlashRAM/Pak, and graceful shutdown pass with audio disabled and
four-MiB configuration. Independent regeneration and expected-output hashing
check complete loads, expanded locals, random state, and every insertion.
Normal paid readings, resulting luck effects, appearance, and hardware remain
separate gameplay/playthrough requirements.

## Verification requirements

- Check full source banks, complete legacy/reference agreement, all 128 English
  values, native base order, all frame changes, and unchanged relocations.
- Exercise generation and independent construction, including disabled/partial
  groups, altered source/output, oversized unrelated strings, and patch overlap.
- Load the actual cartridge overlay at a valid relocated address. Exercise the
  original preparer over every selected phrase, comparing original RNG state
  and full sixteen-byte fields and message insertion. Reconstruct every installed
  string-table entry on the host; exercise native table boundaries and every
  fortune fragment after relocation in a bounded silent batch.
- Preserve isolated saves and restore the checkpoint. Ordinary paid readings,
  resulting luck effects, visual presentation, and hardware remain gameplay
  and playthrough checks, not claims from isolated function tests.
