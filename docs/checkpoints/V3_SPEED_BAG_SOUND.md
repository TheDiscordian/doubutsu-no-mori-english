# V3 actual speed-bag sound installation

## Completed component

ABI 45 installs the complete donor hit sound through the original N64 audio
loader and interpreter. It retains all original audio file contents, original
sound dispatch entries, instruments, and sample offsets. The addition uses
native sound `0169`, bank 140 / instrument 71, and streamed wave bank 5.
The native priority remains 70, matching the donor.

The [sound specification](../../specs/V3_SPEED_BAG.md) records all file intervals,
header changes, physical initializer binding, pointer alignment, and the complete
permanent audio allocation. No audio heap or cache capacity is increased.
Conservative spare permanent capacity decreases from 1,024 to 608 bytes.

This installs sound resources, not the speed-bag item. The production callback,
profile/model loader, item readers, and Punchy's house remain unfinished.

## Current private build

`build/v3-speed-bag-sound-03/animal-forest-v3-asset-loader.z64`

- ROM SHA-256: `07b0da23841e3a030c575599d1e9c8534e9f2c383ea6d55186737c1b2a7469ef`.
- UPS SHA-256: `fc06e1d529940deffd52c3e8b44eaa55acb2122e910f92da2ce82c80331a3bbc`.
- Resident prefix SHA-256: `17d8213e0d328451e22fa24f888ad2803b2e5c49fd97ca09beb4c705d90ff12c`.
- ROM size: 32 MiB; required RAM: 8 MiB; resident prefix: 49,152 bytes.

The build preserves the ABI 44 clothing and save-runtime records. It introduces
no saved identity or format change relative to ABI 44. An ordinary cross-build
reload is not claimed. V3 saves still require the appropriate V3 profile and
must not be loaded in V2 or older incompatible V3 builds; preserve backups.

## Verification and resolved defect

`build/v3-speed-bag-sound-tests-03.log`: all four focused checks pass. These
cover every retained file prefix, all original group-one entries, reserved-ID
terminators, complete instrument resources, pointer/alignment requirements,
full permanent-resource allocation, actual donor priority, bad-input rejection,
three physical ROM argument pairs, original DMA row indices, unchanged other
resources, and complete UPS reconstruction.

`build/v3-speed-bag-sound-native-03/`: all 58 recorded steps complete. Actual
native execution verifies:

- All three relocated native audio headers and the full appended sequence.
- Native instrument count, table pointers, tuning/envelope/sample fields,
  cartridge-medium binding, and complete predictor/loop resources.
- The original permanent heap: five resources loaded at this boot stage,
  73,776 of 108,544 bytes used. The separate host capacity check includes all
  seven permanent resources, including those not yet loaded in this scene.
- Actual public sound trigger allocation with donor priority 70, followed by
  eight ordinary graph frames and one retrigger after four frames.
- Sixteen completed sample-cache observations whose RAM contents match the
  real imported waveform ranges in the cartridge. Descriptors with incomplete
  transfers are not counted and no fixture supplies the waveform to the cache.
- Complete resident/save state, stack guards, translation guard, sound resources,
  no faulted thread, restored emulator checkpoint, and graceful shutdown.

The test is silent. It does not establish a listening comparison, completed PCM
output, complete sound lifetime, GPU appearance, ordinary furniture interaction,
or hardware acceptance. `native_synthesis_tested` remains false in the build
report rather than treating sample DMA alone as PCM verification.

The preceding `sound-01` build used an available sound number with priority 60;
host review rejected that difference before a native run. `sound-02` corrected
the priority but placed the custom envelope at odd offset `4D13`. The first
native attempt lost the graph-frame context; one diagnostic repeat recorded
`S0A` at native audio instruction `800F2624`, a halfword load from `801FF2A3`.
This was an actual alignment defect, not dismissed as a test setup failure.
The fixed build places the reserved-ID terminator before the sound program,
giving the envelope even offset `4D14` without increasing allocation. Its
native run passes on the first attempt. Both failing artifacts remain ignored
and are not playtest candidates. No old candidate builds are replayed.

## Next work and publication boundary

Bind the production positional sound adapter and install the callback/vtable/
profile/model path. Connect a fixed speed-bag item identity, complete readers,
and Punchy's house, then verify ordinary interaction and persistence with the
other remaining villager work. No import is enabled by this component alone.

Stable V2, user saves, both patchers, deployment configuration, services,
repository visibility, and the trailer remain unchanged. V3 source may be
pushed on `v3/optional-imports`; both patchers require the user's V3 testing and
explicit approval before switching.
