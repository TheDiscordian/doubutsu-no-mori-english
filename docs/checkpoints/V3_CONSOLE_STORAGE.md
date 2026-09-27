# Console storage checkpoint

## Installed native storage

The shared runtime builder installs format-five storage in ABI 276 at
`build/v3-console-storage-native-04/build-lock.json`. The complete canonical
format-four bank remains inside the lossless envelope alongside all four console
records. Stable save entries dispatch to the new adapter; the canonical codec,
existing native I/O, and player-clear chain remain. Startup loads five verified
packets before save-state reset. No console launch or new selectable item is
claimed, and neither V2 patcher is changed.

- ROM SHA-256: `f876fc31541db21297e6c5b27f62af790e32ea33850d700f15f3cdd1291f070f`.
- UPS SHA-256: `0b25b49e99743aa93f37c7e731a510b36526cf4574acc217a6de48abe8b2db67`.
- Code: 11,308 linked bytes inside the 19,968-byte guarded packet at `804DE200`.
- Console state: 6,560 bytes at `804DC800`, including header and guard.
- Scratch: 72,064 bytes at `804E3000`, plus a 16-byte guard.
- Hash workspace: 16,384 bytes at `804F5000`, plus a 16-byte guard.
- Existing working save state: 1,232 bytes, unchanged.
- Existing development choices: 162, unchanged.

Reproduction uses a fresh output directory:

```sh
python3 tools/v3_furniture_install.py --refresh-runtime --console-storage \
  --base-lock build/v3-player-exercise-imports-01/player-exercise-native/build-lock.json \
  --output build/v3-console-storage-native-next
```

Four focused checks in `tests/test_v3_console_storage.py` pass across targeted
runs. The host adapter passes 85,426 assertions under address/undefined-behaviour
sanitizers: independent records, probe-versus-commit separation, old-save migration,
native score preservation, player/new-town clearing, and capacity/profile rejection
before I/O. Existing compression/recipe core evidence is retained, not replayed.
All ten DMA/checksum failure paths and successful five-packet startup pass.
Installed dispatches, memory bounds, retained game resources, UPS reconstruction,
and four private browser/offline compositions pass. The translation-only profile
still uses its pinned V2-12 baseline; alignment with V2-13 remains a handoff task.

The initial resource assertion incorrectly treated relocated DMA entries and the
refreshed startup module as unrelated data. Its targeted correction checks the
directory fields, retained resource contents, compiled startup digest, ABI, and
configuration checksum separately. No game safeguard is removed.

### Native writing and fresh-process loading

The existing isolated FlashRAM scenario is adapted to read the installed state
dimensions and independently decode format five. It compares the complete
canonical extension, all town bytes, and all 6,528 console bytes, not only headers.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-console-storage-native-04/animal-forest-v3-asset-loader.z64 \
  --output build/v3-console-storage-write-next \
  --scenario tests/scenarios/v3_save_runtime_write.json --expansion-pak \
  --no-initial-screenshot --allow-test-flash-write --seconds 300 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
python3 tools/emulator_smoke.py \
  --rom build/v3-console-storage-native-04/animal-forest-v3-asset-loader.z64 \
  --output build/v3-console-storage-read-next \
  --scenario tests/scenarios/v3_save_runtime_read.json --expansion-pak \
  --no-initial-screenshot --seconds 180 \
  --seed-save build/v3-console-storage-write-next/native-flash-export \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

Passing evidence is `build/v3-console-storage-write-02/` (164 steps, 62 native
calls, 30 explicit memory assertions) and `build/v3-console-storage-read-02/`
(67 steps, 19 native calls, 40 explicit memory assertions). Writing includes
synchronous single-bank semantics and the ordinary asynchronous two-bank
dispatch/verification sequence. The fresh process checks both encoded bank
probes without committing console data, then both complete native load routes,
restored town/catalogue/console state, native checksum validation, unchanged RAM
tails, workspace guards, and unchanged cartridge storage. Both runs restore the
isolated checkpoint and exit cleanly with audio disabled.

Flash export SHA-256:
`0138d719929dd321e4cf13afef9901d554cc84a9266b46e54307ef2806d33113`.
Each bank SHA-256:
`623c212ad76dbe6c0706fb053de003b27243fca3eab4b8dbf04ecd4b9b10e20e`.

The first writer attempt holds a diagnostic allocation that leaves only 61,200
free native-heap bytes, less than the writer's 65,536-byte bank request. Releasing
that diagnostic buffer before saving produces a successful native write without
changing the game. The first reader has the same fixture-lifetime error, retaining
a complete-bank probe while calling a loader that allocates its own bank. Its
single corrected retry releases the probe before the ordinary loaders. Failed
attempts remain recorded; they are not labelled passes. No historical ROM is run.

The tests use synthetic console progress and direct native function calls, not
ordinary NES play or the save menu. Host checks establish pre-I/O capacity
rejection; that failure is not separately induced on native hardware. Ordinary
console gameplay, save-menu operation with consoles, and original hardware remain
unverified. Native game launch, graphics allocation, frame/reset/exit binding,
QD emulation, and actual acquisition are still required.

Format-five saves cannot load in V2 or format-one/two/three/four V3. Valid older
saves migrate with empty console records and retained original native scores.
Every handoff must warn and preserve backups. The main lock is unchanged.

## Prepared common codec evidence

The ordinary converter prepares the lossless format-five envelope at
`build/v3-console-games-prepared-04/`. It retains the complete 1,472,384-byte game/
tag packet, twenty launch bindings, eleven pinned donor persistence functions,
and unchanged 3,476-byte recipe executor. No ROM, saved format, native hook,
selector, deployment, or existing save changes.

Command used:

```sh
python3 tools/v3_furniture_pipeline.py convert --representation console \
  --assets-only --output build/v3-console-games-prepared-04
```

Use a fresh directory for another build. The 3,368-byte MIPS envelope has SHA-256
`b6d98f6f6748ae7867482fcbad86c04fe33ed898239ee0e0b16aaed5dd5d3ede`.
It links at zero, has no mutable globals/unresolved symbols, and uses at most
152 stack bytes along its longest call chain. Pack offset is zero; expand is
`8FC`. Caller workspace is 72,064 decode bytes and 16,384 hash bytes; decode
storage can also hold the canonical pack buffer between operations.

## Focused evidence

Two new targeted tests and the refreshed common-core receipt check pass:

- `test_lossless_capacity_malformed_streams_and_atomic_pack`: 446 assertions
  under address/undefined-behaviour sanitizers. Deterministic encoding, complete
  decode, guards, read-only inputs, malformed headers/streams, ordinary and
  compensated checksum damage, alias/size rejection, and unchanged output on
  invalid/oversized input pass. The independent established Python Yaz0 decoder
  also reconstructs each complete successful input.
- `test_mips_preparation_receipt`: compiled/source digests, fixed bank size,
  and explicit uninstalled status.
- Existing `test_prepared_mips_core_matches_current_sources_without_install_claim`:
  current common-executor receipt and complete packet. Unchanged donor recipe
  comparisons from the preceding batch are retained, not replayed.

All successful cases include 6,528 independently randomized console bytes:

| Input | Encoded stream | Spare capacity |
| --- | ---: | ---: |
| Empty payload with valid metadata | 8,141 | 55,709 |
| Existing hardware-test town data | 14,909 | 48,941 |
| Dense synthetic letters/map | 58,699 | 5,151 |

The hardware-test save is read only as compression data, not booted in an old
ROM or retested for gameplay. The stress case fills all 192 letter records with
random printable bytes and every foreground word with a random fourteen-bit
value. It is dense storage, **not a semantically valid town or exhaustive
capacity proof**. An entirely randomized payload rejects before output changes.

The first fixture accidentally repairs the same checksum byte it corrupts,
restoring the valid input. Its one justified retry leaves checksum-only damage
unrepaired while retaining compensated damage elsewhere; it passes. No emulator
harness expansion or historical ROM replay is used.

## Required continuation

Continue native console launch/return, full graphics allocation, frame/reset/exit
integration, and QD emulation from the ABI-276 lock above. Reuse the complete
prepared games/models and installed common storage. Raw resource storage must
account for the complete 1,472,384-byte game packet: the current import blob has
less than that much remaining virtual space, so do not append without extending
or separately allocating a checked resource. Do not enable incomplete consoles.
Ordinary gameplay/save-menu and hardware evidence remain pending.
