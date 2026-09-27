# Shared console persistence checkpoint

## Completed batch

The ordinary console converter prepares one common executor for all nineteen
supplied games. It executes every one of the sixty extracted save operations,
including first-play state, score restoration only after game initialization,
score changes, reset-preserve flags, battery ranges, disk ranges, and Zelda's
three-slot marker/checksum repair. The actual donor's four-player allocation is
retained: four 1,632-byte records, 6,528 bytes in total. The donor memory-card
container adds another 64 bytes; this is not an N64 FlashRAM allocation.

The API verifies the full packet and all image/operation bounds, rejects saved
range overlaps and game-bit aliases, and requires disjoint context, packet,
four-player save, work RAM, battery RAM, and full writable image buffers.
Validation failure changes no output. Close captures complete battery/disk
ranges and invalidates the session. Eleven complete donor functions are pinned
to the actual checked executable, including initialization/allocation/cleanup.

Reproduction:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation console \
  --assets-only --output build/v3-console-games-prepared-03
```

Use a fresh output path for another build; existing evidence is immutable.
The shared command succeeds, retaining nineteen games, twenty furniture launch
bindings, and the complete 1,472,384-byte packet. The packet matches preparation
02, so existing extraction evidence remains valid without replaying its tests.
The direct core preparation at `build/v3-console-persistence-01/` contains the
same common code, without the launch-receipt collection of the ordinary command.

MIPS core: 3,476 bytes, SHA-256
`cb5b50768cb1d3f7bb04632bf74e44371e75a07e94901f09527481ad84a7c698`.
It is linked at zero for preparation only, has no mutable globals or unresolved
symbols, and is not installed into the cartridge. Entry offsets are validate
`0000`, open `066C`, frame `0AF4`, and close `0C7C`. The largest stack chain is
368 bytes (104-byte open frame plus 264-byte validation frame).

## Focused evidence

Two tests in `tests/test_v3_console_save.py` pass across targeted invocations:

- The actual donor functions are compiled into an isolated host comparison,
  using source tags and the complete prepared images. 26,695 assertions cover
  all nineteen games, all four players, first/repeat launch, ordinary/default/
  changed score frames, all four score states, reset flags, battery/disk writes,
  Zelda repair, inactive-session errors, malformed ranges, buffer aliasing, and
  failure without mutation. Address and undefined-behaviour sanitizers pass.
  Only the donor's direct big-endian game-bit word is converted for the host;
  its actual tag and persistence routines are not replaced with a Python model.
- The shared-command output's MIPS code, source receipts, explicit uninstalled
  flags, and complete prepared packet match. No old cartridge test is replayed.

The first comparison-harness compile rejects an unused diagnostic variable in
the donor's source because diagnostic output is silenced. The one justified
retry disables that warning for the donor host fixture; it passes. The N64
implementation still compiles with warnings treated as errors.

## Required continuation

The current cartridge is ABI 277 at
`build/v3-console-images-native-01/build-lock.json`. Its
[streaming reader](V3_CONSOLE_IMAGES.md) installs the complete compressed game
pool and compact metadata, with actual native iNES/QD decode evidence. It links
the shared version-two open API without duplicating per-game save logic. Reuse
these installed resources for launch/frame/exit integration; do not rebuild the
earlier full-packet-only executor or rerun its unchanged checks.

Native format-five storage is installed and verified in ABI 276 at
`build/v3-console-storage-native-04/build-lock.json`. See the
[storage checkpoint](V3_CONSOLE_STORAGE.md) for complete hashes, compatibility,
native writing/fresh-process loading, and remaining test limits. The common
recipe executor is linked there but is not connected to NES gameplay yet.

1. Connect checked game lookup, full allocation, room launch/return, and the
   common open/frame/reset/close calls. Preserve original native game IDs and
   their saved state; do not discard native scores during migration.
2. Complete the QD/disk engine dependency and verify representative native
   execution. Static mapper callbacks do not establish correct gameplay.
3. Reuse all fourteen prepared console models and complete game resources;
   enable only records with complete gameplay/persistence dependencies.

Useful original-emulator anchors from the checked `007492E0` overlay:
`8082DF6C` initializes the game state; allocation calls at `8082E0C4` and
`8082E0D8` request `16F90` state and `25008` graphics bytes through `8082A814`.
Their pointers go to linked globals `80854A08` and `80854A10`. Lookup at
`8082A91C` returns start/end source addresses for seven games. `8082E194` onwards
derives image length from iNES PRG/CHR counts. These are static disassembly
observations, not approved replacement hooks or complete allocation evidence.

No native emulator execution, full save/restart, console GPU/audio output, or
original-hardware verification is claimed by this batch. Warn explicitly about
any eventual saved-format change before the private playtest handoff. Stable
V2 corrections remain publishable; V3 stays off both patcher deployments until
the user tests and approves it.
