# Main-program diagnostic text

Translate the eleven native `mRF_DebugMsg` town-generation stages, the
`mRmTp_DrawFamicomInfo` index label, and the retained `(予約)` reserve literal.
These are outside the dialogue banks and scene-selector owner. The first twelve
strings have graphics-print readers; the reserve literal is a discarded C
expression, not a newly discovered player message. Do not enable debug controls
or execute generation/item-spawning actions to inspect wording.

The main owner is VROM `00675720`, linked RAM `80051A80`. The generation pointer
table at `8010C6CC` contains eleven pointers to the aligned string slots beginning
at `801175B0` through `8011767C`. Famicom text occupies sixteen bytes at
`801176C0`; the reserve literal occupies eight at `80117CD4`. Combined storage is
252 bytes. Source strings use EUC-JP; replacements are printable ASCII.

Every complete translation, terminator, and padding fits its existing slot.
Change no pointer, instruction, allocation, relocation, saved field, reader,
generation step, or debug-menu access condition. Preserve the native eight-game
Famicom selector rather than importing GC's larger catalogue. Preserve the
single `%d` argument and both existing English generation prefixes.

Bind `mRF_PrintDebug` (`800BCC40..800BCCFC`) and `mRmTp_DrawFamicomInfo`
(`800BF27C..800BF338`) to their unchanged native instructions. The generation
drawer starts at column three, row 22, after `RandomStep `; every translated
stage fits before column forty. Famicom retains column three, row 26. No line
break, reveal timing, font, or dialogue formatting changes.

`tools/main_diagnostic_text.py` accepts the exact RC8 baseline and verified
original ROM. Reject changed native literals/padding, pointer tables, readers,
source definitions, oversized English, control characters, or altered format
arguments. Reconstruct the complete cartridge while retaining all other DMA
resources, then require original-ROM UPS reconstruction. Use committed sources
and a fresh output directory; no old artifact or save is overwritten.

`make complete` adds this single final construction step after the existing
nineteen-stage correction runner. Final outputs are in the isolated checkout's
`build/v1-final/`. The unchanged base/artwork/correction recipes keep their
recorded evidence; do not replay them to verify this new data-only suffix.

Focused checks cover complete text, slot boundaries, actual pointer reads,
unchanged reader code, format rejection, and new command ordering. Execute the
new construction once from the current RC8, with complete patch reconstruction.
This is not native drawing, ordinary debug-menu access, or hardware acceptance.
