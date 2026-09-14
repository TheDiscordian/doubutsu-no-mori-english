# V3 complete villager assets: loading checkpoint

## Implementation and artifact

`tools/v3_villager_assets_runtime.py` installs all twenty textures, two separate
models, and sixteen accessories in stable banks 410–447. It expands the bank
table without overwriting the native growth permissions, which move to
`80461E80`. Only four compiled instruction immediates change; helper sizes and
every linked symbol remain identical. No extra startup allocation is needed.

Current experimental cartridge:
`build/v3-complete-villager-assets-01/animal-forest-v3-asset-loader.z64`.

- ABI: 51; cartridge: 32 MiB; Expansion Pak required.
- ROM SHA-256:
  `ac0f03c94b94a7eea434a0a112c745205cc76f4006f3a7383dc13c7669cad57f`.
- UPS SHA-256:
  `c5b727d6db63d9f1ae9a32fe9e7d88a510391a2756294d9ee8a0254b0b73ad6f`.
- Original artwork: 38 objects, 162,016 bytes, pinned complete-bundle manifest
  `3c0e9a645d457feddbc17be2dc12eb66670313300d373b6b5a35c70fbef704a5`.
- Full shared resource file: 415,264 bytes; resident startup prefix: 49,152 bytes.

Construction:

```sh
python3 tools/v3_villager_assets_runtime.py --output build/v3-complete-villager-assets-01
```

The builder appends one expanded file in checked zero padding and updates its
existing directory row. All other physical DMA locations, all original object
banks, and both existing pilot textures stay intact. Direct audio addresses do
not change. The inherited storage-size report field is corrected to the full
expanded size; that report-only correction does not alter the tested cartridge.

## Verification

`python3 -m unittest tests.test_v3_villager_assets_runtime -v` passes seven
focused tests in 7.712 seconds. They check fixed identities, invalid inputs,
sanitized native-object semantics, all 38 installed resources, original bank
retention, exact permitted memory/code changes, moved growth data, disabled
flags, full physical preservation, N64 CRCs, and complete UPS reconstruction.
These tests inspect the current implementation, not an old candidate replay.

Native run `build/v3-complete-villager-assets-native-02/` passes **93 records /
59 assertions**, exits normally, and restores its emulator checkpoint:

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-complete-villager-assets-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-complete-villager-assets-native-02 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb \
  --expansion-pak --no-initial-screenshot \
  --scenario tests/v3-complete-villager-assets-native.json --seconds 210 --port 19386
```

The first attempt cannot launch its display because `Xvfb` is absent from PATH;
no emulator starts. The one corrected retry uses the existing local executable.
No installation or live desktop change is needed.

The real native allocator/DMA loads banks 133, 426, 418, 430, 431, 443, and 447:
an original model, retained pilot texture, Dobie's mouthless texture, Pigleg,
Yodel, the largest lei accessory, and the last accessory. Every loaded byte,
untouched destination tail, status, and arena pointer matches its expected value.
Indices 448 and `FFFF` are rejected; `123401BF` correctly selects bank 447 using
the signed low halfword. All checked memory guards remain intact.

The relocated selection reader passes two complete initial populations, the
native random permutations, all four public selection procedures, temporary
import-flag behaviour, history reset, disabled/resident rejection, and state
restoration. This is a controlled native fixture, not an ordinary move-in.
No physical audio or user-save access occurs. Fresh disposable emulator files
are isolated under the test directory. No game save-write call is tested.

## Remaining work

Accessory joint attachment and lifetime management, eighteen new draw rows,
remaining voices/text/defaults/houses, town behaviour, moves, and persistence
are not completed by this loader batch. All twenty move-in flags remain off.
The current profile and saved formats are unchanged from the preceding ABI-50
implementation; ordinary cross-build loading is not newly verified. V2 and
earlier profiles must not be assumed safe consumers of V3 imported saves.

Both web patchers and the trailer remain unchanged. Source publication is
permitted on `v3/optional-imports`; a web-patcher update requires the user's
testing and subsequent explicit approval.
