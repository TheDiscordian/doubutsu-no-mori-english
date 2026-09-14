# V3 furniture menu dispatch

## Implemented paths

`tools/v3_furniture_menu.py` adapts three furniture-type checks and the room-drop
index conversion in the current translated tag overlay. Classification retains
the complete item ID; the separate index conversion passes the correct expanded
runtime index to the native placement callbacks.

| Native window | Purpose |
| --- | --- |
| `80871B6C` | Convert the complete selected item to its runtime placement index |
| `80872BB0` | Route the room-placement action to the furniture drop function |
| `8087480C` | Restrict held furniture to the ordinary inventory/letter destinations |
| `80875688` | Choose furniture action menus for the current field/room context |

The current tag file is VROM `03950000`, 44,384 bytes, linked at `8086F310`.
Its flattened relocation file at `03960000` contains 886 entries. The installer
binds both complete files, their parent submenu owner, the native parent
allocation descriptor, and the tag constructor record. It rejects changed
instructions, displaced relocations, and incoming branches/pointers into a
replaced window's interior. Twelve original instruction words change.

Each detour reproduces the original `ANDI` temporary, calls the existing
full-width query wrapper in classification mode, and writes only the intended
type result. Selected imports produce type 1; original inputs retain their
native type. An unavailable profile does not receive the furniture classification.
The separate save/profile guard handles incompatible saved selections; menu
classification is not a substitute for that guard.

The room-drop function `80871B44` passes a furniture index to both its judge and
reserve callbacks. Its native `(item & 0xFFF) / 4` calculation aliases imported
`3224` to index 137, the original `1224`, instead of index 1161. Replace the whole
six-word mask/signed-division sequence through `80871B80`, returning at
`80871B84`. Enabled imports use the existing expanded-index query, retaining
rotation until the final division. All other sixteen-bit inputs retain the
native low-twelve-bit result, including disabled imports and unused IDs. Only
`at` and `a1` have new outputs; all other registers, HI/LO, and the stack retain
their original values. The callback interfaces and surrounding code are unchanged.

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

V3 ABI 21 keeps the 48-KiB resident reservation and model layout. The three
80-byte classification detours occupy `8046A800`–`8046A8EF`; the 104-byte index
detour extends the helper through `8046A957`, below the next owner at `8046AB00`.
The existing room and shared-field code remains unchanged. Guards, tables, saved
identities, and heap bounds retain their positions. Both web patchers remain V2.

## Verification and remaining work

Three focused placement tests check the exact complete overlay changes, retained parent
and relocations, full-width save instructions, query binding, guards/CRC, UPS
reconstruction, deterministic composition, and import-free V2 output.

The retained [classification checkpoint](../docs/checkpoints/V3_FURNITURE_MENU.md) checks all three
windows with full-width registers and selected/disabled inputs. It also executes
the complete held-item destination function and action-menu selector. The two
imports match original furniture in all four field contexts, and wrapped/quest
conditions remain intact. The fixture constructs the documented post-initializer
parent state; it does not execute the complete parent initialization or ordinary
menu flow. The [lifecycle work record](../docs/checkpoints/V3_ITEM_LIFECYCLE.md)
owns the ordinary placement defect, corrected build, focused index execution,
and normal-play results. Acquisition, ordinary save/reload, and original hardware
remain separate acceptance work.

The [inventory icon adapter](V3_FURNITURE_ICON.md) handles the separate native
furniture check in the submenu parent. It leaves the tag detours unchanged and
retains the parent mask at `8085C864`, which is a branch delay instruction. The
native furniture path selects the leaf descriptor at linked `8085DCF8` and reaches
`8085C980` before drawing. Its focused/native evidence is recorded separately.

Catalogue flags, shop generation/order lists, outside-field item consumers,
scoring, acquisition, and complete save/profile support also remain required.
