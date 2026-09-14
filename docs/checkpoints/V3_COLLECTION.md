# V3 collection checkpoint

The [collection adapter](../../specs/V3_COLLECTION.md) connects native item
collection and resident clearing to the imported catalogues. The cartridge is
`build/v3-collection-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `d39bd3930ebf1b01cdef5328d9371d5a0d7c0d040642a7a6970d5271c6f36ff6`.
- UPS SHA-256: `79546a42445d54e0dd269aaed50b738c80a2e338f6293fbf53e11aa158e6b586`.
- Collection code: 504 bytes, SHA-256 `b5d1fceb5b6bf426c21b18bf5d6248f8318d217480ad2652aa4e3dc46bdab042`.
- Resident prefix: 48 KiB, ABI 15; no additional RAM or save-format change.

```sh
python3 tools/v3_asset_loader.py --collection --output build/v3-collection-01
python3 -m unittest discover -s tests -p test_v3_collection.py -v
```

The build and all four focused tests pass. The sanitized host test checks all
four players/rotations, shared ownership bits, independent clearing, untouched
native records, original fallbacks, disabled/unknown IDs, invalid pointers,
foreign-player rejection, state failure before clearing, and profile rejection.
Cartridge tests check complete native owners, original-function bridges,
unchanged acquisition functions, dependency layout, unchanged FlashRAM helper,
model retention, full UPS reconstruction, and exact import-free V2 composition.

## Native acquisition and saving

The first attempt, `build/v3-collection-save-native-01`, reaches the collection
fixture but stops before its acquisition calls. The shared test-call wrapper
did not provide the existing boot-code proof for cache function `8002FE00`.
The debugger rejects that unverified address; there is no game-fault evidence
or completed acquisition result from that attempt. The fixture is corrected to
reuse `boot_proofs`, with no cartridge change. One justified retry follows:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-collection-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-collection-save-native-02 \
  --scenario tests/scenarios/v3_collection_save.json --expansion-pak \
  --no-initial-screenshot --allow-test-flash-write --seconds 180 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The retry passes 177 steps and 69 native calls, including 31 save dispatches and
30 actual frame advances. Imported pocket contents and catalogue bits come from
native acquisition/collection calls, not injected ownership bytes:

- Player zero acquires a rotated haz-mat barrel through the native free-pocket
  setter. Querying another rotation returns owned. Original furniture still
  updates its original 120-byte catalogue without changing imported ownership.
- Player one receives a wrapped oil drum; it is not collected until the native
  setter changes the item to normal condition.
- Player two's quest-condition barrel remains uncollected.
- Player three acquires an oil drum. Clearing a temporary private record leaves
  every resident catalogue unchanged. Clearing player three removes only that
  player's imported ownership and clears the original pockets. Acquiring a
  barrel afterwards populates that now-fresh catalogue.

The original active-private pointer is restored. All complete-state and private
allocation checks pass. The normal asynchronous writer then prepares and writes
both complete banks, checked against the independent Python encoder and actual
chip readback. Original fixture RAM/state is restored, followed by checkpoint
restoration, fault/guard checks, and graceful shutdown.

The export correctly records `native_collection_populated_catalogue: true` and
`synchronous_single_bank_passed: false`. This batch does not repeat the already
verified, unchanged synchronous writer.

## Fresh-process load

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-collection-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-collection-read-native-01 \
  --scenario tests/scenarios/v3_save_runtime_read.json --expansion-pak \
  --no-initial-screenshot --seconds 120 \
  --seed-save build/v3-collection-save-native-02/native-flash-export \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first reader attempt passes 54 steps and 17 native calls. Only the exported
FlashRAM seeds the new process. Both native load entries restore the complete
original payload and separately saved imported catalogue/profile. Town/ready
fields, original live-RAM tail, guards, fault status, and unchanged chip contents
pass. The fixture checkpoint restores and the emulator exits gracefully.

The exported, writer-flushed, and reader-flushed chip files all have SHA-256
`ae90e77afde3c8c1f2c8bb05c34dd89ee3b5526e42b3109db22e22b9a638d522`.
Each bank has SHA-256
`4e4fd80ab866f98bfa1930f3b361dbb6df07d0999a184df3ee0343458fe321cb`.

Harness construction and verification take less than the 30-minute allowance.
All execution is silent under private Xvfb. No user save, old candidate, live
web patcher, deployment, or released trailer is modified.

## Remaining work

Catalogue screen list/preview/completion/ordering, ordinary shop/reward routes,
item scoring, placement, villager houses/move-in, and Controller Pak transport
remain required. The focused acquisition function calls are not an ordinary
gameplay or original-hardware playthrough. A visiting player cannot safely
collect these imports until the separate Pak/profile support is implemented;
the development safety stop is not a finished substitute for that support.

The specification records the next catalogue table, capacity, bit reader,
arithmetic, and independent preview-loader sites. Continue there instead of
repeating this completed storage fixture. Development source may be pushed;
V3 remains off both web patchers until the user's testing and explicit approval.
