# Complete console images and native streamed reader

## Current cartridge

The checked proposal is ABI 277 at
`build/v3-console-images-native-01/build-lock.json`.

- ROM SHA-256:
  `f346aa8f41e8b4e1e9dad2159ed625f7c10aad4148bdec870dc34c92a602f1d4`.
- UPS SHA-256:
  `b9504f423d51a4d2d058a9270cdb5d0d3a5cbed5f352493b9578218d69b62a55`.
- Preparation: `build/v3-console-games-prepared-06/`.
- All 162 existing development choices remain; this stage enables no console
  furniture. Room launch, emulator initialization, save hooks, and QD execution
  remain unfinished. The main lock and deployed patchers stay unchanged.

The save format remains five. The complete ABI-276 storage packet, native save
hooks, town bytes, and independent player records are unchanged. Retain its
native write/reload evidence without replaying it. Format-five saves cannot load
in V2 or older V3 formats; preserve backups and include that warning at handoff.
No new ordinary save cycle or hardware test is claimed.

## Installed resources

The ordinary converter emits the unchanged full 1,472,384-byte preparation,
6,336-byte compact AFNE-v2 metadata, and 770,144-byte original-Yaz0 pool. All
nineteen images, sixty persistence operations, original tags, and defaults remain.
Only one complete selected game needs decoding; the decoder uses 1,024 input
bytes and at most 524,304 output bytes. It checks input/output bounds, both CRCs,
image headers, and read results before a caller may use the image.

The shared installer consumes that preparation:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime \
  --console-images build/v3-console-games-prepared-06 \
  --base-lock build/v3-console-storage-native-04/build-lock.json \
  --output build/v3-console-images-native-next
```

Use a fresh output directory. ROM-only storage occupies `03F43FA0..03FFFFFF`,
outside existing DMA-owned resources. The source receipt, hash, and complete
extent live in `physical_resources`; these bytes are not free padding even when
zero. Shared input and output validation checks their integrity and overlap;
tail allocation skips them. The full DMA directory gains no entries. No existing
game/audio resource is sacrificed or recompressed to make room.

The checked startup packet occupies `804F9020..804FE81F`: 5,660 linked code
bytes, metadata at `804FC820`, padding, and an end guard. The 584-byte combined
bootstrap fits its existing 688-byte reservation and checks all six packets.
The new reader calls the verified synchronous physical-ROM routine `80026500`,
using aligned requests of at most 1,024 bytes. Its input workspace is supplied
by the caller; the cartridge does not yet allocate live emulator image memory.

Metadata SHA-256:
`350e74125481bbea0971d0a82ccbf1792d294fc2d3df8a8bc0fbe9652dbd470a`.
Pool SHA-256:
`6ab234be644965d19c3571da50e8ae7d03a1116fcc4d5b656436ae2ac461739f`.
Packet SHA-256:
`9ab2b72705aa5e04ce5109abb566faef462d14f6a5ccc6808196f9dd2fa7c8f3`.

## Focused evidence and limits

The common host comparison passes 90,001 assertions under address and undefined-
behaviour sanitizers. It compares actual donor routines against both full and
streamed representations for nineteen games, four players, first/repeat play,
score states/reset, battery/disk saves, and Zelda checksums. All nineteen streamed
images match their complete donor payloads. First/middle/last read failures,
malformed descriptors, bad Yaz0 runs, corrupt checksums, and alias errors reject
without modifying saved state. The immutable full preparation is retained.

Five focused current-source tests pass: installed code/metadata/pool and retained
resources; physical ownership including zero-filled reservations; six-packet
startup and all twelve DMA/checksum failures; four private browser/offline
compositions; and the current preparation receipt. Patch reconstruction passes.
No historical cartridge suite is rerun.

Native evidence is `build/v3-console-images-read-02/results.json`: startup loads
the exact packet; two real cartridge reads decode the complete 40,976-byte Clu
Clu Land iNES image and complete 65,536-byte Clu Clu Land D QD image. Both native
loader calls return success. Fifteen explicit memory comparisons pass, covering
the images, scratch/stack/end guards, and all 6,560 console-state bytes. Five
native calls return successfully before cleanup. This is decoder/PI evidence,
not playing either game or executing an FDS engine.

The full native scenario is **not passed**. Its first attempt rejects the test's
direct upper-memory function proof because the debugger accepts proofs only
below `80400000`. The corrected retry uses the existing checked low-memory jump
stub and reaches all loader assertions. Its cleanup then calls `8009C020`, inside
`zelda_realloc`, instead of `zelda_free` at `8009C040`, causing the test process to
fault. Source symbols identify this fixture error; it is not a cartridge hook.
The helper is corrected. Both setup attempts are spent; do not rerun the passed
prefix just to obtain a green scenario. Check normal launch/return in the next
changed gameplay batch. Checkpoint restore and graceful scenario completion
remain unverified here. All tests use isolated emulator files and disabled audio.

## Next implementation

Continue from ABI 277, preserving the installed pool, reader, and format-five
storage. Connect the existing emulator and room interaction to full selected-game
allocation and the shared open/frame/reset/close calls. Preserve the original
seven N64 identities and native saved scores. The new packet has room for a
shared bridge before metadata; its current code is not a launch hook.

The checked native overlay is `007492E0`, linked at `8082A070`. It relocates when
loaded: hooks to resident V3 code must remove affected native relocations while
retaining untouched ones. Relevant bindings are:

- `8082A91C`: seven-game lookup; callers at `8082B128` and `8082D34C`.
- `8082A814`: emulator allocator. The game-state initializer starts at
  `8082DF6C`; state and graphics requests are `16F90` and `25008` bytes.
- `8082A6EC`: initializes state/header/graphics/image. Native state fields
  `1A7C`/`1A80` hold PRG/CHR sizes; `1AA0` holds graphics memory.
- Reset at `8082E590` decodes CHR through `808328DC` into graphics + `2008`.
  The swizzle permutes bytes within 1-KiB chunks without expanding their size.
  Wario's Woods therefore needs at least `42008` graphics bytes for its full
  256-KiB CHR, exceeding the original allocation. Review the remaining graphics
  consumers and real game-heap capacity before installing the allocation change.
- Work RAM is state + zero; battery RAM is state + `20A0`. Frame wrapper
  `8082A46C` invokes the emulator at `8082F09C`; cleanup begins at `8082E470`.

Static mapper callbacks for zero/one/four/nine are not execution proof. QD still
requires full disk-engine integration. Do not replace the supplied disk image
with a different cartridge release, drop games to fit, or enable models before
their actual gameplay dependencies work. Reuse the prepared console artwork.
