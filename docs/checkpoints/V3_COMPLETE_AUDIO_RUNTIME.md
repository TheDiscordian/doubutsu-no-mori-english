# Complete V3 audio-runtime checkpoint

## Current instrument resolution

The ABI-396 full selection at
`build/v3-travel-console-visitors-profile-01/animal-forest-v3-asset-loader.z64`
has SHA-256
`11f072d0ca3797b3dfed07b7347e6677a6bd3ec4f441f56a5ff63076b5aa0ce8`.
`build/v3-travel-villager-note-trace-03/results.json` passes 96 records and
nine explicit assertions, with actual note selection and matching ROM sample
transfers for all four instruments. Results SHA-256:
`43e031ce9dbd8ed4663472cc98aee41e04aff3e9a2f19fddd129eba61873a6e2`.

The controlled Maelle tune uses `0,14,14,1,14,14,2,14,14,3,14,14,15,15,15,15`:
original held notes (14) and ending (15), not edited melody or engine data.
Instrument 87 first selects with a matching transfer at frame 9; instrument 84
at frame 32, 85 at frame 54, and 86 at frame 76. All relocated instrument
pointers identify bank `801ED280` and the corresponding complete compiled
descriptions. Loaded/resident melody data, the checked 864-byte save/profile
region, fixture/translation
guards, zero fault state, checkpoint restoration, and graceful shutdown pass.
The isolated FlashRAM and Pak hashes remain unchanged. Physical audio is disabled.

The complete original tune-controller commands match between N64 and GameCube
after relocation normalization; the current imported cartridge keeps those same
commands. The focused source/current test passes with:

```sh
V3_COMPLETE_AUDIO_BUILD=build/v3-travel-console-visitors-profile-01 python3 -m unittest tests.test_v3_all_villager_audio.ActualDonorTests.test_original_tune_controller_preserves_hold_and_instrument_tail_timing -v
```

`build/v3-travel-villager-note-trace-01/results.json` records progressing native
note layers, but its unheld tune correctly ends notes before the later instrument
changes. This identifies the earlier absence as the test-tune setup, not a game
defect. `build/v3-travel-villager-note-trace-02/results.json` uses held notes but
ends prematurely: DMA read-ahead includes instrument 86's neighbouring waveform
before its actual selection. It is not accepted as all-four playback evidence.
The third run requires actual selection and matching sample transfer for every
instrument, resolving that diagnostic gap without changing any game code.

This closes the unresolved native instrument result, not ordinary conversation,
listening, or original-hardware acceptance. Existing font/resource checks remain
retained. No ROM rebuild, ABI/save change, or preview recipe refresh is required.
The historical installation and incomplete attempts below remain their original
records, not the current playback status.

## Output

ABI 53 installs all twenty melody sources, the expanded loader, and actual
instrument IDs 84–87, retaining all 83 original instruments. The compact font
reuses a verified identical original envelope; no notes or samples are dropped.
All ordinary move-in flags remain off.

- ROM: `build/v3-all-audio-runtime-01/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `0e8335fa88c5da9800d6c38adf5c1d8fc08ebe86680bcaa88d2fbff5fbc3ff4f`.
- UPS: `build/v3-all-audio-runtime-01/asset-loader.ups`.
- UPS SHA-256: `561875fe6e532d4d68e60724a15fab29dc04359a90f15db11983968b618f154e`.
- Audio bundle: `build/v3-all-villager-audio-02/`.
- Bundle manifest SHA-256: `4899fbd32c0f7b954aa080d634b19f9e13c9f18843959616db52162726719333`.
- Compact font SHA-256: `9b9dfeec62b2aec6c1005db65db7215d69114edce9789bc7c71e8115e8aaa1e4`.

Construction: `python3 tools/v3_all_audio_runtime.py --output build/v3-all-audio-runtime-01`.
The [specification](../../specs/V3_COMPLETE_AUDIO_RUNTIME.md) owns the installed
addresses and memory limits. The ROM remains 32 MiB. Additional resident data
is 12,288 bytes; ordinary audio heaps and saved formats do not grow.

## Focused tests

The combined invocation passes all fourteen tests in 6.245 seconds:

```sh
python3 -m unittest tests.test_v3_all_audio_runtime tests.test_v3_all_villager_audio tests.test_v3_villager_audio.HostTests -v
```

Coverage includes complete source/asset identities, all twenty melodies, all
original and imported instruments, shared-envelope identity, parser failures,
expanded source bounds and protocol under sanitizers, native hook/header edits,
complete resource preservation, all seven permanent allocations, startup CRC,
cartridge bounds/checksum, and UPS reconstruction. No old cartridge is replayed.

## Native run and one focused retry

The first silent isolated run uses `tests/v3-complete-audio-native.json` and
records `build/v3-complete-audio-native-01/results.json`: 113 records, 58 passing
assertions, and no failed assertion. Results SHA-256:
`dafdcc0658fdcd31201ec15a31c80f4a68051370563405d7de262236ddf3cc29`.

Thirty-seven accessory assertions close the previously unexecuted null/guard
tail, including the graphics pointers, matrix stack, complete shared package,
prefix, save/profile state, allocation/stack guards, production guards, and
fault pointer. It does not replay the passing head/torso transform cases.

Audio checks pass actual startup transfers, bank/wave physical-header fixup,
the entire relocated 16,192-byte font, all 87 real instruments and the empty
slot, complete waveform/loop/predictor addresses, and permanent-heap bounds.
Native `Na_Inst` loads Maelle 263, Ankha 277, Cheri 285, and original voice 29;
all complete melody pools and nineteen pointer relocations match. Audio ports
consume the expected tags, and both directions of the 29/285 alias are rejected.

The run ends because twelve-frame windows for each new voice do not observe
a completed sample transfer for instruments 84–87. The single retry uses
`tests/v3-complete-audio-tail.json` on a fresh isolated boot, without requiring
the interrupted run's missing FlashRAM export. It skips the passing font and
accessory checks, invokes the real speech-melody entry on track 6 for Maelle,
and allows sixty frames for the later notes. The copied melody and consumed tag
still match, but no completed new-instrument sample transfer is observed.

Both playback results remain unresolved. Do not classify them as successful
synthesis or as proven fixture-only failures. No third native attempt is made
in this batch. The final post-audio package/save/stack checks are not reached;
the earlier accessory checks do not replace those missing audio-tail results.
No physical audio, ordinary conversation, complete song, or hardware test is
claimed. Inspect note-layer progress and actual sample requests in the next
meaningful combined test; continue unrelated text/default/house work meanwhile.

## Compatibility

Saved fields and the selected profile are unchanged from ABI 52. Ordinary
cross-build loading is not newly verified. Earlier incompatible V3 profiles
and V2 must not consume imported saves. Existing user saves and ROMs remain
intact. Both web patchers stay on V2 pending user testing and explicit approval.
