# Console-game imports

## Shared conversion

`v3_furniture_pipeline.py convert --representation console --assets-only`
prepares the complete English donor's games and persistence recipes in one pass.
`--donor-disc` accepts the supplied GAFE01-r0 disc; its executable and complete
`famicom.arc` hashes must match. Outputs remain in ignored `build/` directories.
Preparation does not enable furniture or claim that the games run on N64.

Archive traversal order supplies nineteen one-based game IDs. Do not sort the
filenames or derive game identity from an English title. All eighteen iNES
images retain their headers, full programme/character data, mirroring, battery,
and trainer flags. The complete 65,536-byte QD image is preserved separately;
it is not replaced with a different release or a fabricated iNES image.

Complete 124-byte indexed and 64-byte fixed furniture callbacks determine the
game and GBA IDs. Both twenty-entry indexed tables, selector range, fallback,
and relocations remain in the source receipt. The existing constant-material
converter attaches this launch dependency without changing artwork or declaring
the move callback implemented. Unknown callbacks remain unresolved.

The donor has twelve additional game payloads after the seven native identities:
eight use mapper zero, Punch-Out uses mapper nine, Wario's Woods uses mapper four,
Zelda uses mapper one, and Clu Clu Land D uses QD disk data. The disk-system
furniture `1FBC` requests game twenty, which does not exist in this donor's game
archive or metadata table. It is an unused source record with a missing payload,
not an additional supplied game awaiting only a launch callback. Super Tortimer
has no game-launch callback in the donor and remains decorative.

## Persistence conversion

The nineteen metadata records come from the checked DOL table at `800AAA30`.
Keep GNO save-bit identity separate from archive identity: Soccer and Excitebike
use save IDs thirteen and twelve respectively. The complete shared recipes
contain sixty ordered operations and address 1,623 bytes after an eight-byte
save header **per player**. The donor allocates four independent `660`-byte
player blocks: 6,528 bytes, plus its separate 64-byte memory-card container
header. The N64 container may differ, but player progress must remain independent.
Eleven complete donor functions, including allocation, loading, saving, and
checksum handling, are pinned in `persistence_contract`. They retain high-score defaults/reset flags, battery RAM regions,
QD write-back regions, and Zelda's special checksum/marker restoration.

High-score bit fifteen preserves the loaded-score state on reset; lower eleven
bits address emulator work RAM. It is not a numeric comparison direction.
The donor waits for the game's default score before restoring saved scores,
then follows subsequent changes. Persistence integration must retain this state
machine, not blindly copy saved scores every frame or only at launch.

One exact checked source defect is corrected: Baseball's GNM record declares
six bytes but contains the eight existing bytes `BASEBALL`. Only its length
byte changes from six to eight. The original record, source hash, corrected
record, and correction receipt are retained. Unknown malformed records reject;
there is no heuristic resynchronisation or invented save metadata.

The binary preparation format is big-endian:

- 32-byte header: `AFNE`, version one, count, 64-byte entry stride, data start,
  save-payload extent, eight-byte save-header size, complete packet length.
- Sixteen words per entry: source game ID, image kind (one iNES, two QD), mapper
  (`FFFFFFFF` for QD), zero flags; image offset/length; original tags
  offset/length; converted tags offset/length; operations offset/count; GNO;
  save-payload extent; two reserved zero words.
- Sixteen-byte operations: kind byte (one HSC, two BBR, three QDS, four SPE),
  parameter byte, length halfword, save-payload offset, source offset, and
  packet-relative high-score defaults pointer. Empty pointers are zero.
- Complete images, original/converted tags, operations, and default bytes use
  sixteen-byte-aligned packet offsets. No game resource is shortened to fit.

## Shared persistence executor

`overlays/v3/console_save.c` executes the complete prepared recipes. The ordinary
console conversion command compiles this dependency as well as preparing games;
there are no per-title installers. The core is zero-linked preparation, with no
assigned native RAM, hooks, device writes, or selectable-game claim.

`af_v3_console_validate` checks the entire packet, image sizes/headers/mappers,
all sixty operations, unique game-save bits, and disjoint saved ranges. Open
validates buffer sizes and separation before changing anything, copies the full
game image, and binds exactly one of four supplied player blocks. The surrounding
save codec owns player header bytes 0–3 and the trailing padding byte; the recipe
executor owns the played-game bits and recipe ranges. Its caller must verify
the immutable packet's digest and retain packet/buffer lifetimes until close.

First play inserts score defaults and clears only declared battery regions;
disk data retains the complete source image. Repeat play loads all battery/disk
ranges and performs Zelda's three-slot marker/checksum repair. The frame entry
retains the donor's four score states, waits for each score's default RAM value,
restores saved scores, then follows changes. Reset honours each HSC preserve bit.
Close captures every battery/disk range and invalidates the transient session.
It does not add an extra score-frame update absent from the donor's cleanup.

The 3,476-byte MIPS core uses no mutable globals and no unresolved libraries.
Its largest stack chain is open plus validate, 368 bytes. Preparation is
`build/v3-console-games-prepared-04/`; all game/tag/default bytes match the
earlier complete preparation. Two focused checks pass across targeted runs:
26,695 assertions using actual donor source routines under address/undefined-
behaviour sanitizers, and current MIPS/source/prepared-packet receipt checks.
Coverage includes all nineteen games, four players, first/repeat launch,
score states, reset, disk/battery/Zelda paths, malformed bounds, alias rejection,
and unchanged output on errors. This is not native emulator or FlashRAM evidence.

## Native integration requirements

The original N64 emulator is VROM `007492E0`, linked at `8082A070`, with SHA-256
`12a57f84c4a600f5cf319f5be82c489ba2c137eada1ed5d4ddb6458ca6c7d1df`.
Its game-range function `8082A91C` handles seven games. Mapper dispatch starts
at `8082E950`, using twenty-byte records at `80836010`. Actual callbacks exist
for mappers zero, one, four, and nine; this is static evidence, not execution
proof for the new games. The existing graphics allocation is `25008` bytes and
cannot simply be assumed sufficient for larger complete character data.

Connect checked game lookup, correct allocation, ordinary room entry/return,
complete persistence, and QD dependencies before enabling each supported import.
Retain original game IDs and native save regions. The current format-four
save capsule has insufficient spare room for the four-player donor save data;
persistence needs an explicit bounded storage design, not an overwrite of its
neighbours or a promise that unchanged formats suffice.
Its 432 spare bytes cannot hold 6,528 player bytes. Do not combine players,
truncate game progress, assume compression always fits, or silently remove the
second town-save bank. Native storage integration remains the next dependency.
The [compressed bank envelope](V3_CONSOLE_STORAGE.md) is prepared by the same
converter. It retains the complete canonical bank and four console records,
with explicit pre-write capacity checks and bounded lossless decoding. Host
checks pass; native hooks, initialization, and commit are not installed.

GameCube GBA download parameters remain in receipts. N64 hardware cannot use a
GameCube link cable; do not silently claim that functionality was imported.
The current preparation changes no cartridge, saved format, selected profile,
or deployed patcher. Any later save-format change needs the normal compatibility
warning before a playtest handoff.
