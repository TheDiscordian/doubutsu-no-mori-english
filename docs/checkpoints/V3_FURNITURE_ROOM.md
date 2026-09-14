# V3 room-integration checkpoint

## Completed implementation

All 21 reviewed `My_Room` furniture upper bounds, both item-index conversions,
and four local field-type scans now recognise selected imported profiles.
Native branch/delay-slot semantics and original-item arithmetic are retained.
The [specification](../../specs/V3_FURNITURE_ROOM.md) documents the complete
scope, preservation rules, memory layout, and remaining consumers.

V3 ABI 7 loads 48 KiB of resident data without changing ordinary heap bounds.
Room code uses 4,436 bytes; model payloads remain ROM-only, with updated profile
VROMs. IDs and prior resident tables retain their positions. The web patchers,
stable V2 cartridge, existing saves, and released trailer are unchanged.

## Current build and focused verification

```sh
python3 tools/v3_asset_loader.py --furniture-room --output build/v3-furniture-room-02
python3 -m unittest tests.test_v3_furniture_room -v
```

All four focused checks pass, without skips. The current cartridge is
`build/v3-furniture-room-02/animal-forest-v3-asset-loader.z64`, SHA-256
`5f269931a911554b2a2106ef21b8896bdf88854f2fec0ee3f0745a0a7623b42e`.
The adjacent UPS has SHA-256
`ca0264edcb4e4006c38cecaeb19cef7aa20f2a1a99a0198ea65d4f806875e787`.
Build reports, compiled assembly, generated hooks, assets, ROMs, and patches
stay in ignored build directories.

Compiled-code review of development build `v3-furniture-room-01` caught o32
assembler expansion of `SD`/`LD` into paired 32-bit operations. Explicit
`.set gp=64` fixes that issue. The wrapper also preserves all callee-saved
registers at full width because the C helper's own o32 prologue saves only
their lower words. Those corrections are in build 02 before its first native
attempt. Build 01 is preserved as an intermediate artifact, not a playable
handoff or a passing result.

## Native verification

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-furniture-room-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-furniture-room-native-01 \
  --scenario tests/scenarios/v3_furniture_room.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first native attempt passes 151 recorded steps, including 125 executed
instruction-window cases. All 27 installed detours run with original furniture,
a selected rotation, an unsupported item, and a disabled profile. Each paired
lower bound also exercises its below-range path. These distinct windows have
different delay instructions and continuations, so checking one helper alone
would not cover the concrete register/control-flow risk.

The fixture verifies the complete 48-KiB startup prefix, actual native relocation
of the room owner and BSS, expected live continuation addresses, full-width GPRs,
HI/LO and floating-point register retention, original caller-stack bytes,
allocation/stack/translation guards, and absence of a faulted thread. Checkpoint
restore and resumed execution pass. Native harness work remains within its
30-minute batch allowance; no setup retry is needed.

The run uses isolated blank storage, private Xvfb, and disabled physical audio.
No game-save or Controller Pak write entry is called. Emulator shutdown writes
only its own newly created isolated storage files. No existing save is read or
modified. Old-build native checks are not replayed.

## Remaining integration

The room detours do not establish an ordinary placed actor. Remaining work
includes inventory/acquisition dispatch, field handling outside this owner,
catalogue/scoring and mail consumers, save/profile compatibility, rendered
placement/collision, pickup, and a normal save/reload cycle with an import.
The villager houses, selection, and other clothing/animated dependencies remain
in the active V3 queue. No import is marked playable, no release is cut, and
neither patcher switches to V3.
