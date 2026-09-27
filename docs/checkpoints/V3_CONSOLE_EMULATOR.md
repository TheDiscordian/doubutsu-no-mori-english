# Shared native console lifecycle

## Current cartridge

ABI 278 is `build/v3-console-emulator-native-01/build-lock.json`.

- ROM SHA-256: `5a714a18c3d6037f07bd9664bae456fcf85cd7ba290aebfe35370e42aea41ad1`.
- UPS SHA-256: `29f7129bb4177da6ecc73ae4fb0e299c7f673478ec10f607626a72a4d5316013`.
- Linked reader/lifecycle/save code: 7,276 bytes in the existing 22,528-byte
  packet at `804F9020`; metadata remains at `804FC820`.
- Transient session: `804FE820..804FF01F`, 2,048 bytes, below the model pool.
- All nineteen compressed images, metadata, format-five storage, and existing
  162 choices are retained. No console furniture is selectable yet.

The ordinary installer consumes ABI 277 without reconverting artwork or games:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime --console-emulator \
  --base-lock build/v3-console-images-native-01/build-lock.json \
  --output build/v3-console-emulator-native-next
```

Use a fresh output directory. The main V3 lock stays unchanged. Both patcher
deployments serve latest stable V2-13; only experimental V3 publication is held.

## Native bindings

Six checked calls in the complete native emulator connect graphics allocation,
selected-image loading, initialization, frame, reset, and cleanup. Their native
delay slots are retained. Exactly their six jump relocations are removed; all
other relocated code/data is checked unchanged at two possible load addresses.
The hook derives the actual overlay address from its native caller, not its
original linked address. Session bounds and end guards precede later calls.

Original game IDs zero through seven retain their native loading, scores, and
allocation. Additional iNES games use the complete streamed image. All decode
checks precede binding the image into native emulator globals. Invalid game,
player, save storage, allocation, or image inputs stop setup. Failed save-session
initialization requests the native return path after normal emulator startup.

The existing mapper-zero/one/four/nine callbacks are retained. Wario's Woods
gets `42008` graphics bytes instead of `25008`, accommodating its complete
256-KiB character data after the `2008` graphics prefix. Other games retain the
original allocation unless their complete character data requires more.

Save initialization follows native initialization/reset so that reset cannot
erase restored battery data. The common score update follows each outer native
emulator frame. User reset copies all 8,192 battery bytes aside, updates the
source reset flags, invokes native reset, then restores battery RAM. Cleanup
waits for native RSP completion before capturing final battery progress.
The backup uses the existing game allocator; no saved field is enlarged.

## Verification and limits

Three focused tests pass:

```sh
python3 -m unittest tests.test_v3_console_emulator -v
```

The sanitized host adapter executes the actual decoder and save executor against
all eleven additional iNES images, four players, first/repeat entry, reset,
cleanup ordering, independent progress, allocation guards, and rejection paths.
It retains the original eight loading paths, including Controller Pak ID zero.
Its 110,728 assertions include full-image comparisons and memory guards. Native
CPU/PPU/audio routines are stubbed, so these are **not gameplay results**.

Cartridge checks verify all six hooks, relocation preservation, complete changed
code, unchanged image pool/metadata/save storage and unrelated DMA resources,
and patch reconstruction. Four private browser/offline compositions pass.
There is no new native scenario run for this batch; previous reader and storage
execution evidence remains tied to those earlier builds.

Remaining work: connect source furniture callbacks and normal room return,
measure actual game-state heap capacity with the largest image, verify native
initialization/rendering/reset/return, and implement the full QD disk dependency.
QD currently rejects instead of being treated as a cartridge image. The complete
disk payload remains installed and its gameplay is still required. Neither
static mapper callbacks nor host-adapter success establish gameplay support.

The native room owner is VROM `0082D7F0`, linked at `80936710`. Its console
move callback at `8093BD60` checks the furniture switch-change byte at `12D`,
then dispatches to the existing request function at `8093BC30` for a nonzero
game ID. That function retains message-hide/busy checks, stores the game ID at
room offset `480`, and requests message state 31. The normal room handler calls
`goto_emu_game` at `800C6D5C` from `8093A4F8`, taking the ID from room offset
`482`. Native `goto_emu_game` saves the player's doorway/position; native
`return_emu_game` at `800C6E14` restores that room transition. Connect source
game mappings to this existing lifecycle, not an immediate game-state jump.
Confirm the clip-table binding and current complete-function hashes before
installing callbacks; these located addresses are not installed room support.

Save format remains five. Saves from this build cannot load in V2 or older
format-one/two/three/four V3 builds. Preserve backups and include that warning
before handoff. Ordinary save-menu use with imported games and hardware remain
unverified; no new save-cycle claim follows from unchanged storage code.
