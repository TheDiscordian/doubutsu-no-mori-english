# Exact isolated-emulator observations

## Debugger memory access

The installed ares 148 debugger aligns two- and four-byte memory reads down to
the corresponding halfword/word boundary. Raw `m<address>,4` requests therefore
do not reliably describe an unaligned four-byte guard. Longer reads preserve the
requested address. `tests/debugger-memory-alignment-scenario.json` records the
raw behaviour using an original ASCII fixture, then verifies the exact-access API.

`RSP.read_memory` requests a covering, word-aligned range and slices the requested
bytes. Every scenario assertion and state snapshot uses this API. Raw `command`
actions intentionally remain raw for protocol diagnostics. Writes use single-byte
edges and aligned bulk transfers; they do not read and overwrite adjacent live
state. Portable tests exercise every alignment and lengths one through thirty-three,
including adjacent guards and invalid/truncated reads.

Test calls require a matching emulator checkpoint and complete restoration. On
an unexpected stop, diagnostics retain the before/after register packets and
scratch stack. An unexplained call failure stays in the validation record even
when its rerun passes. A generated scenario is not evidence of a passed test.
Run manifests record the ROM, runner source, and scenario hashes.

## Read-only player position

`snapshot_player` reads `gamePT` at `8010EF90`, then the pointer at game offset
`1C90`, matching the native accessor at `800B1C84`. The actor must have part two
(`ACTOR_PART_PLAYER`). Position is the three floats at actor offset `28`, and
the signed block fields are bytes `8` and `9`, as defined in the pinned header.
Player block fields can be minus one; use the actual world coordinates for
navigation. Reject invalid/unaligned/out-of-range pointers, wrong actor types,
nonfinite coordinates, and truncated reads.

This observation does not teleport the player, unlock progression, or establish
save compatibility. Normal gameplay tests use controller input. Captures belong
only to the isolated silent emulator display, never the user's working desktop.
