# V3 room furniture identity

## Purpose

Room actors store a runtime furniture index, not a saved item ID. For selected
imports, the inverse conversion must recover `3224` or `32B8` from indices 1,161
and 1,198. Native `1000 + index*4` arithmetic instead produces `2224` and `22B8`.
The named inverse function and three inlined conversions require separate hooks.

`tools/v3_furniture_identity.py` installs the three inlined conversions after the
[room range/index adapter](V3_FURNITURE_ROOM.md). The
[menu index adapter](V3_FURNITURE_MENU.md) supplies the correct expanded index
when dropping an item. Both are included when building with `--furniture-menu`
or a later dependent component. This does not enable imports in either patcher.

## Native instruction windows

| Linked window | Input and result |
| --- | --- |
| `80943CA0` | Collision: A1 contains index × 4; return the full 16-bit item in A1 |
| `80945FC8` | Tile lookup/pickup: A1 contains the index; return the full item in A1, retaining the following native branch and masking delay instruction |
| `8093BBF0` | Model re-DMA: S0 contains the index; retain A0's index and V0's bank address, and supply the full item in S2/A1 |

Each detour replaces exactly two instructions. The installer checks the complete
input owner and relocation hashes, displaced words, absence of displaced
relocations, and absence of branches or relocated pointers into a replaced
interior. Existing surrounding branches and delay instructions stay unchanged.
Texture command constants resembling item arithmetic are not modified.

The accepted input owner at VROM `0082D7F0` has SHA-256
`cfd1b88e8a763013e666a58487304bdcc618819a9f794490948ee804862c7da1`.
Its relocation at `00844400` has SHA-256
`a130c711f128e0ba32d5fdba9e06b7480d848d4badc01fe411731dac6983c762`.
Owner length, relocation data, and allocation are unchanged.

## Conversion and register contract

The integer-only helper checks the existing selected-profile predicate at
`80465000` and obtains the imported ID from the inverse helper at `804652E4`.
Both exported addresses are checked against the actual compiled dependencies.
For every unselected index, retain the inlined native unchecked calculation;
do not substitute the named inverse function's `1088` fallback.

The full-register assembly wrapper is generated from `room_entry.S` with only
the function names changed. It preserves 64-bit GPRs and HI/LO across the o32
call. Floating-point registers are untouched. Each continuation uses the actual
loaded room pointer at `80100E00`, not the room's link address. Only each
window's documented result registers change.

## Reservation and compatibility

The helper, wrapper, and three detours occupy 596 bytes at
`80469D00`–`80469F53`, inside the reserved gap before the field bridge at
`8046A200`. The builder rejects a nonempty or insufficient reservation.
The 48-KiB resident extent and model file tails remain unchanged. The assembled
startup uses ABI 22 and checks the full updated prefix CRC.

No item identities, saved layouts, saved profile formats, or catalogue bits
change. Experimental V3 saves still require a compatible V3 import profile;
this does not make them safe to load in V2. The import-free composition remains
the exact stable V2 cartridge.

Verification and ordinary interaction findings belong in the
[item lifecycle checkpoint](../docs/checkpoints/V3_ITEM_LIFECYCLE.md).
