# Dresser menu cancellation

The native filled-dresser question `message:0A0B` uses three labels. Its original
order is Remove / Never mind… / Swap (`007E/000D/00E9`), and the room handler
maps indices zero, one, and two to those actions. The room also enables B, whose
native handler selects the last row. B therefore enters Swap.

The correction makes the order Remove / Swap / Never mind… (`007E/00E9/000D`).
Instruction `80939394` changes from `addiu at,zero,1` to `addiu at,zero,2`.
The complete guarded function `80939350..809394F4` retains every other instruction:
zero removes an item, two cancels, and one enters the original swap path.
The ordinary B handler and last-row cancellation sound remain unchanged.

`tools/dresser_menu_fix.py` binds the complete original English message and
native function hashes before changing either resource. Both changes are
required together. It retains bank sizes, offsets, relocation records, allocation,
save formats, all wording, and every unrelated resource. It rejects partially
patched, already patched, or unknown source inputs. Stable packaging requires
the exact V2-13 base and emits a new V2-14 ROM and original-ROM UPS.

The source draft in `translations/n64-storage-raffle.json` retains native controls
for initial translation validation. This guarded post-build adaptation supplies
the final menu. The single provenance catalogue records the final payload and
both edit locations; no new English wording is introduced.

V3 applies the same resource correction through the existing translation-update
stage. Banks resolve by original DMA identity, allowing relocated text resources.
The three current room-owner receipts are updated only after their full input
hashes match. Imported behaviours and format-five saves are retained. The empty
import selection resolves to corrected V2-14; experimental V3 is not deployed.

## Targeted evidence

Three host checks verify the exact two label-byte changes and one instruction-byte
change, rejection guards, checksum, and UPS reconstruction. The silent native
test executes B from every highlighted row and A for each action, then loads and
relocates the complete room owner and executes its actual cancel arm. The dresser
requests close, consumes the selection, and retains saved town/inventory bytes
and memory guards. All 29 assertions pass, followed by checkpoint restoration
and graceful shutdown. The fixture's initial BSS-bound error is corrected once;
the cartridge is unchanged by that test correction.

This verifies native input and the changed cancellation branch, not an ordinary
hardware playthrough or a fresh cross-version save cycle. Existing item-transfer
code, other menus, and save formats are unchanged.
