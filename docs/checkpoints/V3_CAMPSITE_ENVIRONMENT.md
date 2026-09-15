# V3 campsite floor sound and light parameters

## Deliverable

- Full ROM: `build/v3-campsite-environment-runtime-02/animal-forest-v3-asset-loader.z64`.
  SHA-256 `6d2d533bbf85b961560417293626400222f7c2576c565adfa1b93465f41e21f6`.
- UPS SHA-256 `e6f10594710e1a1bf73865dc7b1380c88e4b8a0a0f084609090d22b373b2b82f`.
- Build report SHA-256
  `1fc74f38d403e4982a486009e66e162700bbc33425149a384a5b9466164bd381`.
- Offline kayak/propane-stove subset: `build/v3-optional-campsite-environment-01/`.
  ROM SHA-256 `5be6b395bf4a838ee75a9a2eab0044bd2dc4b149d184beaaa3f883bf7b29d665`.

ABI 82 retains all installed trade, greeting, text, calendar, and import work.
The composer pins the current full cartridge and report; all 59 experimental
choices remain, with exact full/V2 all/empty output. Neither patcher changes.
No player-facing text is introduced, so no attribution record is added.

## Implemented

The new floor getter returns the native audio-table slot for the donor's actual
tent footstep sound. The donor and native complete sound programs, instruments,
and samples match. The shared transient audio index does not replace floor
artwork, an item, or another scene. Both existing player/NPC sound readers retain
their original code and valid table bounds.

The point-light getter supplies the donor tent's position, colour, power, and
non-flame setting through the original five-argument interface. Original rooms
and non-indoor draw modes retain their complete native paths. The engine still
owns light allocation and cleanup. The timed scene-lamp effect is not installed.

The 156-byte helper occupies checked unused package space at `804A2F54`, ending
at the unchanged final guard `804A2FF0`. SHA-256
`7d8b1c7e595d2d1068f4335a1d40f4a96b8911aeba942943dc06ed8f923e5396`.
Startup remains 912 bytes, below its 992-byte limit. Resident allocations,
ordinary heaps, save code, saved formats, profiles, models, DMA entries, and
audio resource sizes do not change. The [campsite specification](../../specs/V3_CAMPSITE.md)
records exact source bindings and continuation addresses.

## Verification

Six `tests.test_v3_campsite_environment` checks and twelve current
`tests.test_v3_optional_composition` checks pass. They cover complete donor audio
dependencies, exact installed hooks/trampolines, unchanged neighbouring owners,
assets, saves, occupied-space rejection, checksums, selected dependencies, and
exact all/empty composition. The builder reconstructs the full ROM from its UPS.

Initial native run: `build/v3-campsite-environment-native-01/results.json`,
SHA-256 `14dbba9a4394c7961572cbc36af674d283f5a2cd964eeb7928106d0174cf4a90`.
Ten records include four passing assertions and one fixture failure. The new
floor getter correctly returns 68. The fixture incorrectly calls scene 18 a
post office; scene 18 is the buggy and correctly returns 70. The post office
is scene 14. Correct the fixture, not the ROM.

Remaining-only retry: `build/v3-campsite-environment-native-02/results.json`,
SHA-256 `45fbcdb30324cadcf6c2883d5b4402bfeeec4e5b2f453a2882010c4759980fdd`.
All 39 records complete, including nine native calls and 29 passing assertions.
The already-passed standalone tent floor getter is not repeated. Checks cover:

- Complete original post-office, igloo, and unknown-scene floor-getter returns.
- Complete new tent, original house, original igloo, and non-indoor point-light
  calls, all five arguments, stack restoration, and untouched output padding.
- The actual native field caller through its stored floor index.
- Both full native footstep readers reaching `Sou_WalkSe` with sound `0306`
  and retained spatial arguments. Execution stops before audio queuing; this
  establishes routing, not ordinary walking or audible playback.
- Restored saved town, allocation/stack/package/translation guards, no faulted
  thread, fixture release, checkpoint restoration, and clean emulator shutdown.

The run is silent and isolated. It does not write the user's saves, establish
original-hardware acceptance, or replay older candidate builds.

## Continue

Implement the actual timed scene lamp: creation, dawn/dusk room-light transitions,
primitive-LOD model fade, complete drawing, and cleanup. The native engine lacks
the donor's `mEnv_RequestChangeLightON/OFF` API; bind the intended behaviour to
native light ownership rather than copying incompatible function addresses.
Then continue remaining masked readers and combine ordinary tent/NPC
construction, entry/exit, conversations, reward handover, and persistence.
The earlier exterior allocation result remains unresolved until ordinary
integration classifies it. Continue the rest of the full V3 queue as well.

Saved format 2 and selected identities remain unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2. Ordinary cross-profile
reload remains unverified. This is not a complete-import playtest handoff.
Neither web patcher changes until the user tests V3 and explicitly approves it.
