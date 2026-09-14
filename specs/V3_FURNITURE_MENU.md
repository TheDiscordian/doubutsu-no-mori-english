# V3 furniture menu dispatch

## Implemented paths

`tools/v3_furniture_menu.py` adapts three furniture-type checks in the current
translated tag overlay. The checks classify selected imports as furniture without
altering the item ID carried by the surrounding code.

| Native window | Purpose |
| --- | --- |
| `80872BB0` | Route the room-placement action to the furniture drop function |
| `8087480C` | Restrict held furniture to the ordinary inventory/letter destinations |
| `80875688` | Choose furniture action menus for the current field/room context |

The current tag file is VROM `03950000`, 44,384 bytes, linked at `8086F310`.
Its flattened relocation file at `03960000` contains 886 entries. The installer
binds both complete files, their parent submenu owner, the native parent
allocation descriptor, and the tag constructor record. It rejects changed
instructions, displaced relocations, and incoming branches/pointers into a
replaced window's interior. Only six original instruction words change.

Each detour reproduces the original `ANDI` temporary, calls the existing
full-width query wrapper in classification mode, and writes only the intended
type result. Selected imports produce type 1; original inputs retain their
native type. An unavailable profile does not receive the furniture classification.
Invalid saved imports still require the pending save/profile guard; this is not
a substitute for that guard.

Wrapped-present and quest conditions remain in their original earlier branches.
Other tag type checks compare against ordinary item type 2, so original furniture
type 1 and imported type 3 already take the same path there. Those instructions
remain untouched, including checks whose masking operation is a branch delay
instruction. Do not overwrite a delay instruction as though it were an ordinary
two-instruction entry.

## Loaded owner and register preservation

The submenu parent allocation is read from `8010DCEC`. Its tag descriptor at
offset `2CB0` stores the constructor pointer at `2CC0`. The actual native parent
loader updates that pointer after tag initialization. These runtime action and
hand/menu functions do not run during the tag constructor.

The detour derives the live continuation from that updated constructor pointer,
whose original link address is `808787A0`. It preserves full-width RA while
calculating the address and restores RA in the final jump delay slot. The shared
query wrapper preserves all other live GPRs, HI/LO, and the caller stack; the
new code has no floating-point operations. The tag overlay and parent retain
their allocation sizes, loader, constructors, destruction, and relocation files.

V3 ABI 9 keeps the 48-KiB resident reservation and model layout. The three
80-byte detours occupy `8046A800`–`8046A8EF`. The existing room and shared-field
code remains unchanged. Guards, tables, saved identities, and heap bounds retain
their positions. Both web patchers remain V2.

## Verification and remaining work

Three focused tests check the exact complete overlay changes, retained parent
and relocations, full-width save instructions, query binding, guards/CRC, UPS
reconstruction, deterministic composition, and import-free V2 output.

The [native checkpoint](../docs/checkpoints/V3_FURNITURE_MENU.md) checks all three
windows with full-width registers and selected/disabled inputs. It also executes
the complete held-item destination function and action-menu selector. The two
imports match original furniture in all four field contexts, and wrapped/quest
conditions remain intact. The fixture constructs the documented post-initializer
parent state; it does not execute the complete parent initialization or ordinary
menu flow. Normal placement/acquisition, saving/loading imports, and hardware
compatibility remain unverified.

The inventory icon has a separate native furniture check in `mSM_draw_item` in
the submenu parent. The type shift/constant pair at `8085C880`–`8085C884` is a
candidate entry; its mask at `8085C864` is a branch delay instruction and must
remain in place. The normal furniture path selects the leaf texture descriptor
at linked `8085DCF8`, then reaches `8085C980` before drawing. This icon reader
is not patched by the three tag detours and remains required work.

Catalogue flags, shop generation/order lists, outside-field item consumers,
scoring, acquisition, and complete save/profile support also remain required.
