# V3 save-codec checkpoint

The [save/profile specification](../../specs/V3_SAVE_PROFILE.md) records the
native storage audit, implemented format, and required integration work.
The combined cartridge contains the encoder/validator/catalogue-bit helper;
it does not enable native save or catalogue hooks.

```sh
python3 tools/v3_asset_loader.py --save-codec --output build/v3-save-codec-01
python3 -m unittest discover -s tests -p test_v3_save_codec.py -v
```

All six focused tests pass without skips. The cartridge is
`build/v3-save-codec-01/animal-forest-v3-asset-loader.z64`, SHA-256
`35c7a499e0b741b8ebc721649f5bf624ba85c0ddc88619edfdad09cf2bfcc66b`.
The UPS SHA-256 is
`2d88a302ee862d9ac316dd143418ebf0f7fb095ebb6f48aa490e5211c926e64c`.
The 1,608-byte helper SHA-256 is
`07579657a5266ed13e61e471ea16a6b68809758438154e1561cdc16e874878fd`.
The cartridge remains 32 MiB, with a 48-KiB ABI-13 resident prefix and no heap
growth. Native flash and worker instructions remain unchanged.

```sh
python3 tools/emulator_smoke.py \
  --rom build/v3-save-codec-01/animal-forest-v3-asset-loader.z64 \
  --output build/v3-save-codec-native-01 \
  --scenario tests/scenarios/v3_save_codec.json --expansion-pak \
  --no-initial-screenshot --seconds 150 \
  --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb
```

The first attempt passes 76 recorded steps, including 33 native calls. The
resident N64 codec produces a complete 64-KiB bank matching the independent
Python/zlib encoder. Native checksum validation passes, and the original
signature predicate accepts the synthetic legacy bank and rejects its `NAF3`
encoding. All four catalogue records decode correctly; rotation-normalised
ownership marking, added selections, removed villager/furniture rejection,
checksum/CRC/binding/catalogue rejection, invalid sizes, and overlapping input
rejection pass. Rejected decodes leave output and input buffers untouched.
Resident code, source profile/state, allocation/stack/translation guards, and
the faulted-thread check pass. Checkpoint restoration resumes execution.

Harness construction and the first native attempt remain within the 30-minute
allowance; no retry is needed. The test uses private Xvfb, disabled physical
audio, and blank isolated storage. It performs no FlashRAM device I/O and does
not touch ordinary game-save data. No actual save/reload, player-facing profile
warning, catalogue-menu behaviour, or hardware acceptance is claimed.

Next: wire prepared banks, complete bank reads, profile acceptance, owned runtime
state, and catalogue consumers; run a bounded fresh-process persistence check.
V2, both web patchers, the trailer, existing saves, and previous builds remain
unchanged. Development source can be pushed; V3 patcher publication still needs
the user's testing and explicit approval.
