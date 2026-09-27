# Console allocator bounds and checked runtime refresh

## Current cartridge

ABI 281 is `build/v3-console-emulator-capacity-01/build-lock.json`.

- ROM SHA-256: `763bbcbeca77390e797039c79ee8ae83a2a7b7497b5768db81534ed0ce14a62d`.
- UPS SHA-256: `e2fff8b99b32431c7189e6fb3849e19bfd805050d2513e6be48465ef71d1a0bc`.
- Linked console reader/lifecycle/save code: 7,500 bytes, SHA-256
  `49b945a56872e16aba9a4a74381631d8d93b70c98647e66c7c34766753defba7`.
- Existing room code/table/vtable, complete images/metadata, all models and
  selections, format-five storage, and both V2-13 deployments remain intact.

The ordinary shared runtime command supports checked updates of installed code:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime --console-emulator \
  --base-lock build/v3-console-room-imports-01/cartridge/build-lock.json \
  --output build/v3-console-emulator-capacity-next
```

Use a fresh output directory. Before recompiling, the installer recreates the
previous native hooks from the verified original ROM and compares both full
code and relocation resources with the current cartridge. It does not guess
original instructions from patched data. It also verifies the installed packet,
room bindings, and complete native arena function. Updated code stays below
`804FB000`; every byte from the room callback through metadata and the packet
guard is retained. The six lifecycle call targets are rebound, with only their
six original relocation entries removed.

## Allocation correction

The native allocator's call at `8082A88C` now reaches
`af_v3_console_arena_allocate`. That covers every console game-arena allocation,
including native audio/state/header allocations before the import session is
initialized. The original `THA_alloc16` subtracts from the tail without checking
the head; its complete 32-byte implementation is pinned with SHA-256
`f3e069b2d467873eb48833d658698f16a0a0942f8688dadf0df6ff1701ac3116`.

The new entry validates the heap-header address, size, ordered start/head/tail,
four-MiB native-memory bounds, and full sixteen-byte-aligned allocation extent.
It rejects zero/overflowing requests and insufficient space before invoking the
original subtraction. Rejection leaves the arena unchanged. The original
primary-pool → game-arena → fallback-pool order remains available; the native
allocator can try its real fallback pool after a rejected arena request.
Imported direct requests also reject oversized inputs before native alignment.
No global, actor, model-bank, or saved field grows. The new guard needs no stack.

## Focused evidence

Four tests pass across targeted runs in `tests.test_v3_console_emulator`:

- Sanitized host execution uses actual complete donor images and the common
  save executor: 110,902 assertions covering eleven iNES games, four players,
  first/repeat entry, reset/close, original game paths, allocation boundaries,
  exact fits, misalignment, wraparound, full arenas, and real fallback ordering.
  Native CPU/PPU/audio are stubs in this test.
- Cartridge checks verify all seven calls, the six removed relocations,
  unchanged room code/data, full pool/metadata and save resources, retained
  profiles, source receipts, and original-ROM UPS reconstruction.
- Modified installed-code or relocation receipts reject before compilation or
  packet changes.
- Four private browser/offline compositions match, including empty selection.
  The pinned empty-selection baseline still needs its V2-13 alignment.

## Native evidence and unresolved startup

`tests/scenarios/v3_console_game.json` uses the actual native game-state manager
from a disposable title checkpoint, with Wario's Woods as the largest image.
It does not simulate a room conversation or claim ordinary acquisition/entry.
Audio is disabled and existing saves are not used or modified.

Two attempts are retained:

1. `build/v3-console-game-native-01/results.json` verifies startup and requests
   the native state transition. Waiting for another normal frame times out.
2. `build/v3-console-game-native-02/results.json` corrects observation to inspect
   the stopped machine without requiring it to reach another frame. The snapshot
   records game 15, player zero, a 524,304-byte image allocation at `80275050`,
   and the battery backup at `80273050`. The native game arena is 1,539,296 bytes,
   starting at `80234130`, with head `80234130`, tail `80253E30`, and 130,304 free
   bytes. The session has no error and the CPU fault-thread pointer is zero.
   The emulator-state pointer and save-session active flag remain zero, so
   initialization is incomplete. Observation is in native thread 10 at
   `800F48BC`; this alone does not establish the cause of the stall.

Neither scenario passes. There is no complete image comparison, running-game,
reset/return, or checkpoint-restoration claim from these attempts. Both attempts
are spent: do not repeat this setup unchanged or dismiss the stall as harmless.
The next relevant native run should capture the graph thread's saved context
and the startup boundary before audio/CPU initialization to identify the wait.
A credible unresolved startup defect remains a playable-handoff blocker.

## Next implementation and compatibility

Continue the QD disk engine and the unresolved native startup/normal room return.
The local donor reference contains QD fast loading/saving, disk registers,
interrupt timing, and sound in `src/static/Famicom/ks_nes_core.cpp` and
`src/static/jaudio_NES/game/emusound.c`; these need native bindings, not a renamed
cartridge header. Do not replace the complete Clu Clu Land D image with another
release. Acquisition remains after primary importing work.

The save layout remains format five. V2 and older-format V3 cannot load these
saves. Removing a selected imported profile is not safe compatibility merely
because the layout is unchanged. Preserve original saves and provide the explicit
warning before a private handoff. Hardware and ordinary console save/reload
remain unverified. V3 is not deployed to either patcher.
