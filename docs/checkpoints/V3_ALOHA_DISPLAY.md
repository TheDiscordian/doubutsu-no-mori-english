# Complete imported-shirt display checkpoint

## Artifact

ABI 58 connects both aloha garments to the complete display and catalogue paths.
See the [specification](../../specs/V3_ALOHA_DISPLAY.md) for identity, memory,
storage, acquisition, and compatibility contracts.

- ROM: `build/v3-aloha-display-03/animal-forest-v3-asset-loader.z64`.
- ROM SHA-256: `0f1c532c281ba3dce1bbc32b1085b0207a6617b95090b98d97de2ff1ad2deb0e`.
- UPS SHA-256: `03d923785c65085c48a80be09ab6f34ed34b24357130a80e28bff0bdd1b140e2`.
- Blob SHA-256: `09c4408f1277ecbb8dabfa1184d6dc122a77a3248fe2684e3266272e2272fff3`.
- Profile SHA-256: `da56b0abe35a8a1e5a6477b0254530f6dc2d2ef0cbfa11aef9a261fce268506d`.

Build: `python3 tools/v3_aloha_display.py --output build/v3-aloha-display-03`.
The first build rejected a missing furniture assembly-entry symbol before writing
a ROM. Including the required existing assembly source corrects the build. The
second build succeeds; the third has the same cartridge and patch with corrected
report fields/source hashes. The third is the authoritative recorded artifact.

## Focused checks

`python3 -m unittest tests.test_v3_aloha_display -v` passes the initial five
tests in 6.545 seconds. The combined real-C fixture uses undefined-behaviour
sanitization and covers all three displays, four rotations, canonical metadata,
names/prices/types, ownership, resource selection, disabled independent
dependencies, malformed rows, original fallbacks, and argument bounds. Cartridge
checks verify complete installed helpers/profiles, donor/native catalogue order,
only the two intended profile-bit changes, untouched resources, declared physical
writes, native CRC, and full UPS reconstruction. An initial host-fixture macro
collision is corrected before these checks; it is not a cartridge defect.

The subsequently added compatibility check passes separately in 0.454 seconds:

```sh
python3 -m unittest tests.test_v3_aloha_display.AlohaDisplayCartridge.test_actual_codec_accepts_older_profiles_and_rejects_missing_displays_without_writes -v
```

The actual format-2 C decoder accepts old-to-current and current-to-current
profiles. Current-to-old returns `-7` with the source and output buffers intact.
This is six passing focused tests across those two invocations, not a claimed
full-suite rerun or an ordinary gameplay reload test.

## Native integration

The first native attempt passes: `build/v3-aloha-display-native-01`, 120 records,
67 passing assertions, no failed assertions. Results SHA-256:
`da02773f25a659173111a01aa239efcd2f0d5186832d28a04a38da2a1171b9e6`.

```sh
python3 tools/emulator_smoke.py --rom build/v3-aloha-display-03/animal-forest-v3-asset-loader.z64 --output build/v3-aloha-display-native-01 --xvfb /home/discordian/Games/OpenRSC/headless/vendor/usr/bin/Xvfb --expansion-pak --no-initial-screenshot --scenario tests/scenarios/v3_clothing_catalogue.json --seconds 240 --port 19392
```

The existing combined fixture exercises both complete native conversion entries,
all three garments in all rotations, and original clothing fallbacks. Real
acquisition-record calls establish ownership for the selected fixture items;
these are not ordinary purchases. Full catalogue initialization verifies all
248 clothing rows and separate furniture, full names, selection, native preview
profiles, prices, animation state, and complete 4,128-byte transfers. Buffer tails
remain intact. Order conversion retains each complete pocket identity.

Disabling red's display and garment dependencies separately removes only red;
cherry, blue, and native entries remain. Native executable prefix, appended
code/tables, module/stack/allocation guards, restored globals/private state,
checkpoint restoration, no-faulted-thread checks, and graceful shutdown pass.
No physical audio is emitted. Native memory/DMA checks do not establish GPU
appearance, ordinary acquisition/payment/delivery, or house placement/persistence.

## Next work and release hold

Trace faithful aloha acquisition without adding exclusive zero-price clothes to
general shop stock. Continue ordinary villager gameplay and persistence. The
[town checkpoint](V3_TOWN_RESIDENTS.md) retains the unexplained post-positioning
debugger response; the next house investigation must retain the raw response and
inspect fault/scene state, not repeat blind navigation. The
[audio checkpoint](V3_COMPLETE_AUDIO_RUNTIME.md) retains incomplete sample-playback
evidence. Neither unresolved result is waived by this catalogue pass.

ABI 58 requires both new display dependencies. Older builds reject its new-profile
saves; keep backups and distinguish codec compatibility from ordinary reload.
This remains an implementation artifact, not a completed V3 handoff. Only source
on `v3/optional-imports` may be pushed. Neither web patcher receives V3 before the
user tests and explicitly approves the switch.
