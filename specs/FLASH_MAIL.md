# Native FlashRAM persistence for English letters

## Scope

`tools/flash_mail.py` guards the original N64 save routines and inventories the
letter arrays within the checksummed save payload. The isolated native harness
tests actual cartridge writes and a separate fresh emulator process reading
only the exported cartridge save. It does not establish ordinary save-menu
operation, post-load gameplay, Controller Pak travel, or original-hardware
compatibility. Snapshot generation remains disabled.

The GameCube source's per-letter `header_back_start` check is part of a separate
debug save-data checker. It is not evidence that the N64 flash module rejects
the experimental snapshot marker. The guarded N64 module checks the signature,
town identity, and checksum. This audit does not exclude additional metadata
readers elsewhere in the N64 executable.

## Native layout and functions

Addresses and offsets in this section are hexadecimal. Live save data begins
at `80126EA0`. Each of two FlashRAM banks has a `10000`-byte stride; the complete
chip is `20000` bytes. The checksummed logical payload is `F980` bytes. Padding
after that payload is not interpreted as saved data and need not be zero.

The header contains `NAFJ` at offset `04`, a two-byte town identity at `08`,
date fields beginning at `0A`, and a two-byte checksum at `12`. The town ID's
high byte must be `30`, and it must equal the saved land ID at `2F68`.
Adding all big-endian sixteen-bit words in the payload modulo 65,536 gives zero
for a valid checksum. A checksum alone does not prove semantic save validity.

| Function | Address | Harness use |
| --- | --- | --- |
| Save dispatch | `80090044` | Run the original asynchronous two-bank save pipeline |
| Native bank reader | `8008F8A0` | Read the 499 payload pages into a private buffer |
| Checksum | `8008EE7C` | Validate each read payload |
| Header identity check | `8008EF0C` | Check signature and town identity |
| Flash initialisation predicate | `800CDBE0` | Require the cartridge interface to be ready |
| Flash read | `800CDE54` | Read all 1,024 chip pages for export/comparison |

The complete module `8008ECA0..80090120` has SHA-256
`6d95d3a3d34236f1447ead3e6a7512ce23917de7114974a602b59e8d8c6c956c`.
The worker range `800CDB10..800CE120` has SHA-256
`e4524a68fb1a56d8ff2f8441079316567c1e901d125c52cceb6b507165263759`.
The seven-entry dispatch table at `80106ACC` must contain `8008FAE0`,
`8008FB64`, `8008FBEC`, `8008FCE8`, `8008FDD4`, `8008FE74`, and `8008FF60`.
Both code ranges and the complete table are checked before execution.

The save state at `8013A398` occupies 32 bytes. The native pipeline requests
a temporarily reserved framebuffer through `800D97A0`, prepares a complete
payload there, writes bank zero in chunks, reads it back, checks it, writes
bank one, verifies it, and releases that buffer. The request state and pointer
are at `80146080` and `80146084`. The graph thread and framebuffer retirement
advance the request from one through two to three; acquisition changes it to
four. This is not a large ordinary-heap allocation. The harness
must not consume the worker's completion queue: the save pipeline owns it.
Between bounded dispatch calls, execution passes the current frame entry at
`800D334C`, stops at its guarded second instruction at `800D3350`, then runs to
the next frame entry. Merely setting the entry breakpoint again while already
stopped there can immediately stop again without advancing the game. No
register or instruction write simulates frame progress. Native return one and
cleared control state are
required for success; timeout and failure returns remain failures.

## Covered storage

The inventory contains 192 distinct slots wholly inside the logical payload:

| Storage | Slots | Record bytes |
| --- | --- | --- |
| Four players' letter pockets | 40 | 164 |
| Four home mailboxes | 40 | 164 |
| Post-office queue | 5 | 164 |
| Leaflet records | 2 | 164 |
| Fifteen NPCs' seven letter memories | 105 | 132 |

The first NPC compact letter is at `80130DF2`: animal base `80130DB8`,
memory offset `10`, and letter offset `2A`. Animal and memory strides are
`528` and `B0`. Native instructions and the caller/conversion tests establish
these offsets; conflicting platform-specific comments are not used.

Both classic and composite snapshots are distributed across every array.
Fixture installation retains identities, gift fields, and compact-record date
and padding bytes. Full-record equality checks include those fields, not only
the 122-byte snapshot envelope. These are synthetic storage fixtures, not a
claim that every slot is occupied by a normally delivered letter.

## Isolation and acceptance

The writer requires a fresh output directory, a matching-ROM test checkpoint,
an idle native save pipeline, an entirely blank isolated FlashRAM chip, and
explicit `--allow-test-flash-write`. Existing user saves are never targets.
The writer uses a 16 KiB streaming read buffer; the fresh-start reader reuses
one 64 KiB bank buffer. Separate decoder storage and guards share each private
native allocation, avoiding a needless complete-chip allocation on the N64.
The native
pipeline's complete prepared payload is captured and compared with both banks
read back through the game's own flash API. The export is created before
restoring the test checkpoint, which may also restore cartridge memory.

The read scenario runs in a separate emulator process with `--seed-save` only;
`--seed-state` is rejected. The complete native chip read must match the export.
Both native bank reads, native checksums, native identity checks, every complete
stored record in both banks, and complete English reconstruction for each
full/compact and classic/composite combination must pass. Heap, stack, and
module guards are checked. Each process restores its own machine checkpoint,
and every private native allocation is freed.

The native writer passes 25 save dispatches and 24 actual frame advances,
including both bank writes and native verification. Its complete 138-step run
contains 44 native calls and 27 assertions. The fresh reader passes 448 steps,
19 native calls, and 406 assertions, including 384 complete-record checks and
eight complete English reconstructions from the actual native-read buffers.
Each process restores its own checkpoint and exits gracefully. The exported
chip, writer's flushed chip, and fresh reader's flushed chip agree completely.
Only the FlashRAM file seeds the fresh process; no emulator checkpoint or RAM
image crosses from the writer into that process.

Portable tests cover slot counts and bounds, both-bank checksum and identity
rejection, uninterpreted padding, malformed sizes, and mutated native code/table
guards. Native execution results and exact artifact hashes belong in the work
log. Passing these tests only proves the specified isolated persistence path;
normal save-menu operation, ordinary gameplay after load, other readers,
lossless editing, semantic template matches, and hardware remain required.
