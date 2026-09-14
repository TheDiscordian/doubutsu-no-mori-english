# V3 FlashRAM checkpoint

The [native integration](../../specs/V3_FLASH_RUNTIME.md) connects the codec to
actual town reads/writes and the incompatibility warning. The current cartridge
is `build/v3-save-runtime-02/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `c76818eb6296a69a08f59cf570e306883816b5dfd3d80bd71719bb849ae749a2`.
- UPS SHA-256: `ffeae8d617f031b8763704f79a0d141ec5803cf9411cdd8e56b87c63461c0de3`.
- Runtime helper: 1,867 bytes, SHA-256 `21bb3b82007790f77e9b9e6d4445974474726658bea3e3158778f56f477368ab`.
- ROM size: 32 MiB; resident prefix: 48 KiB, ABI 14; added owned state: 704 bytes.

```sh
python3 tools/v3_asset_loader.py --save-runtime --output build/v3-save-runtime-02
python3 -m unittest discover -s tests -p test_v3_save_runtime.py -v
```

All six focused tests pass without skips. The initial build caught an incorrect
profile index calculation for `3xxx` items; the corrected builder uses the
verified extended-table base of 1,024. The passing cartridge installs all guarded
windows, preserves payload-copy widths and model objects, and reconstructs fully
from its UPS. An empty composition retains exact V2-11.

## Native writing and fresh-process loading

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-save-runtime-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-save-runtime-write-native-01 \
  --scenario tests/scenarios/v3_save_runtime_write.json --expansion-pak \
  --no-initial-screenshot --allow-test-flash-write --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes synchronous `8008F7C8` writing, complete chip readback,
independent bank encoding, imported catalogue/profile retention, unchanged bank
one, and the updated complete live payload. It then stops at the fixture's
asynchronous framebuffer bound. That fixture incorrectly required a framebuffer
to lie above the translation module, excluding native framebuffer zero. This is
not recorded as a complete first-attempt pass.

The corrected check matches native framebuffer ownership, retired pointer, table,
alignment, and full capacity. One justified retry runs only the asynchronous
portion, retaining the completed synchronous evidence instead of repeating it:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-save-runtime-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-save-runtime-write-native-02 \
  --scenario tests/scenarios/v3_save_runtime_write_async.json --expansion-pak \
  --no-initial-screenshot --allow-test-flash-write --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
python3 tools/emulator_smoke.py \
  --rom build/v3-save-runtime-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-save-runtime-read-native-01 \
  --scenario tests/scenarios/v3_save_runtime_read.json --expansion-pak \
  --no-initial-screenshot --seconds 120 \
  --seed-save build/v3-save-runtime-write-native-02/native-flash-export \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The writer passes 141 steps and 50 native calls, including 31 save dispatches,
30 actual frame advances, both complete bank writes/readbacks, native verification,
guard checks, restored fixture RAM/checkpoint, and graceful shutdown. Its prepared
framebuffer is `801C3140`, matching owner state 4 and the native framebuffer table.
Both banks match the complete native prepared buffer, including the extension.

The fresh reader passes 54 steps and 17 native calls. Only the exported cartridge
save seeds the new process; no checkpoint or RAM image crosses between processes.
Both complete native bank reads, native checksums/header checks, allocated load
`8008F968`, redirected direct load `8008F938`, full original payload, catalogue/
profile state, town/ready fields, unchanged native RAM tail, guards, and unchanged
chip readback pass. The imported IDs `3225` and `32BB` remain in the two fixture
players' pockets. Checkpoint restoration and graceful shutdown pass.

Exported and both flushed chip files have SHA-256
`853fadff83a7e13de65495dd215aea49bca11b14ef09200779a9e9c908a41bbc`.
Each complete bank has SHA-256
`d11da423a9ed952c627aa54d38f8cde07beb07838ef02f029b5f96d722a17009`.
The retry export honestly records `synchronous_single_bank_passed: false` for
that invocation; the first attempt's result owns the synchronous evidence.

## Cold-boot incompatibility warning

```sh
python3 tools/v3_save_warning_smoke.py \
  --source build/v3-save-runtime-write-native-02/native-flash-export \
  --output build/v3-save-warning-seed-01
python3 tools/emulator_smoke.py \
  --rom build/v3-save-runtime-02/animal-forest-v3-asset-loader.z64 \
  --output build/v3-save-warning-native-01 \
  --scenario tests/scenarios/v3_save_warning.json --expansion-pak \
  --no-initial-screenshot --seconds 60 --seed-save build/v3-save-warning-seed-01 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes five recorded steps. A valid first-bank extension
requires unselected actor index 218; the second bank is the compatible original
export. Normal cold-boot execution reaches the missing-import warning, renders
the complete English message (108 glyphs/6,912 checked pixels), and stops graph
thread 4 with no CPU fault. No native test calls or fixture RAM/register edits
trigger the warning. The flushed complete chip retains seed SHA-256
`d6b6a2434af4c74ee5a400eeb88d5c79e28ed3925d4e35faf677d899e1132621`.
The runner also enforces this post-shutdown equality for future warning checks;
the recorded run's actual file equality is independently checked.

All harness construction and these bounded checks fit the 30-minute allowance.
Tests use private Xvfb and no physical audio. Existing user saves, stable V2,
both web patchers, the trailer, and previous cartridges remain unchanged.

## Compatibility and remaining work

These saves require the new V3 save format and the saved required imports.
Do not load them in V2 or older experimental V3 builds. Keep backups. Adding
imports is supported by the codec; removing required imports stops loading with
the checked warning. Actual V2-save migration, ordinary gameplay/save-menu use,
Controller Pak transport, and hardware acceptance are not established here.

Next: native catalogue marking/query/order consumers, ordinary furniture
acquisition/placement, remaining item scoring, villager houses/move-in, and
complete playable pilots. Development source may be pushed. V3 stays off both
web patchers until the user tests and explicitly approves it.
