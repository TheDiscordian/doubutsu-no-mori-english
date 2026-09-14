# V3 furniture room range and index integration

## Scope

`tools/v3_furniture_room.py` adapts the reviewed `My_Room` furniture checks and
index conversions for selected imports. It installs 21 upper-range detours,
two item-to-runtime-index conversions, and four local field-type conversions.
All native room code outside those exact instruction windows remains unchanged.
The [checkpoint](../docs/checkpoints/V3_FURNITURE_ROOM.md) records verification.

The imported IDs remain `3224`–`3227` and `32B8`–`32BB`, with runtime indices
1,161 and 1,198. Only their enabled, correctly bound resident profiles qualify.
Other `3xxx` values remain rejected by the room range checks. These helpers
do not replace the saved item number with a native alias.

This component does not establish ordinary acquisition, inventory dispatch,
placed rendering/collision, pickup, catalogue/scoring, or save/profile safety.
Those consumers still need integration and an ordinary gameplay check before
either import can be advertised as playable. Both web patchers remain V2.

## Checked source and control flow

The input is the exact loader-adapted V2 room owner, SHA-256
`06a23fdecd70488a102e4c9a6f0734687174748c223e7cdd84b469a68c60f5e1`,
with its retained 1,401-relocation file, SHA-256
`a130c711f128e0ba32d5fdba9e06b7480d848d4badc01fe411731dac6983c762`.
The installer rejects changed source, changed range inventory, changed registers
or instructions, overlapping windows, displaced relocations, and branches or
relocated pointers entering a replaced window's interior.

Seventeen range checks pair `SLTI item,1000` with `SLTI item,1ECD` in the lower
branch's delay slot. Their complete four-instruction window moves to a generated
resident detour. Four upper checks have an earlier separate lower test; those
detours replace only the upper comparison and following branch.

Every original upper-branch delay instruction stays at its native address.
Ordinary branch fall-through returns there; a branch-likely fall-through skips
it. A taken upper branch executes that instruction in the detour before returning
to the original target. Taken lower branches retain their original target and
the upper comparison's delay-slot result. This preserves live AT values, stack
loads, native furniture-marker assignments, and branch-likely annulment.

| Original linked entry/window | Adaptation |
| --- | --- |
| `80938A34`, `MakeOneFurniture` range | Accept selected imported furniture before creation |
| `809386B0`, actual furniture constructor | Produce runtime-index/rotation arithmetic offset |
| `80938AA0`, creation index reader | Produce the selected runtime index |
| `8093AB2C`, `8093AB68`, `8093ABA4`, `8093ABE4` | Treat selected imports as furniture in local field-clearing scans |
| Other reviewed room range sites | Consistent selection checks across room movement, interaction, and removal paths |

The complete address list and instruction values live in the checked installer
and generated build report. Room-owner `6xxx` checks and unrelated `2xxx` checks
remain unchanged. Interaction bitfields shifted by two are not item indices and
are not rewritten.

## Register and memory preservation

Generated detours use the actual loaded room address from `80100E00`, never the
overlay's unavailable link address. Dynamic returns temporarily save RA, compute
the live continuation, and restore RA in the jump delay slot. Original callers'
registers and stack arguments survive, including delay instructions that load RA.

The query wrapper explicitly uses `.set gp=64`. It saves complete 64-bit GPRs,
HI, and LO before calling the o32 helper, including the callee-saved registers
whose upper halves o32 C prologues do not preserve. The helper uses no floating
point instructions. Its 40-byte compiled stack plus the 32-byte caller and
256-byte register-save frames consume at most 328 bytes on this path.

## Layout

The room variant uses V3 ABI 7 and a 48-KiB startup reservation at `80460000`.
All preceding resident offsets remain fixed, including the interior `80467FF0`
guard. Room code starts at `80468000`; the end guard is `8046BFF0`. The builder
stages the existing 32-KiB prefix, adds the room code, and checks the complete
48-KiB CRC. Ordinary heap bounds do not change.

The compiled query, wrapper, and 27 detours occupy 4,436 bytes. The models move
within the same ROM-only file tail to `03F0C000` and `03F0E000`; item identities
and runtime indices do not move. The file is 60,560 bytes, below the first
villager texture at `03F10000`. Both model extents and profile addresses are
checked. The DMA directory gains no entries.

## Evidence limits

Focused checks cover selected rotations, rejected/disabled imports, original
arithmetic, exact installed windows, complete 64-bit load/store opcodes, both
guards, CRC/configuration, model-tail bounds, UPS reconstruction, and the exact
import-free V2 output.

The native fixture loads and relocates the actual current room owner. It executes
125 cases across all 27 installed windows, checking continuation PCs, full-width
registers, HI/LO, floating-point registers, caller stack, and guards. It resumes
the checkpoint afterward. It does not call a complete placed-actor constructor,
insert items into a town, write a game save, or establish hardware compatibility.
