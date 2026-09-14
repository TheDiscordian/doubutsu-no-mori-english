# V3 animated furniture installation

## Installed work

ABI 46 installs the speed bag's full model and rig, production constructor/
move/draw text, positional hit-sound adapter, callback table, native profile,
fixed item/index reservation, and English name/price/footprint metadata.
The general furniture loader accepts this specific reviewed animated profile;
other unknown non-null vtables remain rejected.

The row starts disabled and is not in the saved import profile. It is not a
playtest-ready or selectable item yet. Its donor HRA series 58 exceeds the
native 55-entry completion storage; scoring needs an explicit adaptation before
the item is enabled. Acquisition/catalogue, ordinary interaction/persistence,
and Punchy's house also remain required. No static model, alternate hit sound,
or replacement scoring series stands in for the donor behaviour.

## Current private artifact

`build/v3-speed-bag-runtime-03/animal-forest-v3-asset-loader.z64`

- ROM SHA-256: `e5e293093197fe24ae02b213c56643365b8f59667cf986cfce9cc2e0fc178a81`.
- UPS SHA-256: `f4c6e0df7b6fff42ed5f9eaf944ff80648de6432d40914f854e83ce562cf220e`.
- Resident prefix SHA-256: `4eaad54d3b46ec822c97f144d731e2d3c9c7879664cbdc9c7ad88f0ab187ed8e`.
- ROM: 32 MiB; required RAM: 8 MiB; resident prefix: 49,152 bytes.
- V3 file: 69,264 bytes in reserved VROM `02200000..02400000`.

The saved format and complete selected profile remain unchanged from ABI 45.
Neither the relocated asset-file address nor the disabled furniture row adds a
saved dependency. This is not an ordinary cross-version reload test. Existing
V3 save/profile restrictions still apply; V3 saves must not be loaded in V2 or
incompatible older builds. User saves and preceding artifacts are preserved.

## Storage and bindings

The 64-KiB V3 file interval lacks space for this model. The new two-MiB virtual
reservation is checked against every existing file, without increasing the
resident RAM allocation. All three resource types—furniture, clothing, and
secondary code—pack together in address order. The 3,728-byte speed-bag object
occupies file offset `10000`; its model bank remains the native 5,120 bytes.

The composer retains every existing DMA directory index. `replace_dma` accepts
an explicitly checked addition order; callers without that argument retain the
existing default. Virtual-address sorting alone would renumber existing V2
added files when introducing this lower-address V3 file, so the composer keeps
those existing rows first. The full directory identity and patch reconstruction
checks pass.

The [specification](../../specs/V3_SPEED_BAG.md) records the exact reclaimed seed
bytes and resident layout. Production callbacks begin at `80466F20`; the sound
adapter at `80467100` calls the actual positional entry `800D1D58` with `0169`.
The table is at `80467110`, and the native profile at `80467138`. The expanded
loader uses 1,308 of its 2,048-byte reservation. Item metadata is at `804672E0`.
All established public item-reader addresses are retained despite the compiler
changing its private two-record unroll into a bounded three-record loop.

Two initial build attempts fail safely before saving a ROM: the first detects
the shifted public item-type entry; explicit linker positions retain the ABI.
The second detects changed existing DMA indices; explicit addition ordering
retains them. The third build completes all internal bounds, source guards,
composition, and UPS reconstruction checks. Failed build directories are
preserved, not handed off or treated as working cartridges.

## Focused checks

`build/v3-speed-bag-runtime-tests-01.log`: all four checks pass on the initial
run. The actual C loader runs with address/undefined-behaviour sanitizers and
checks disabled selection, identity/vtable/bank validation, all rotations,
complete-object DMA, rejected malformed profiles, failed DMA, and retained
indices. Python checks cover ordered packing, overlap rejection, complete
installed model/callback/table/profile/metadata, preserved old bridges and
metadata, startup configuration, secondary code CRC, original directory indices,
unchanged save profile, and complete UPS reconstruction.
`build/v3-speed-bag-runtime-tests-02.log` also passes all four checks after
adding explicit empty/oversized/misaligned prefix and resource rejection.

`build/v3-speed-bag-runtime-native-02/`: all **204 records / 75 assertions** pass,
including complete current prefix/extra-code startup, real sound loading and
waveform transfers, both existing imported models, the new animated model,
all rotation identities/categories/prices, the English name, installed
constructor, and actual first-hit positional sound at priority 70. Native
clothing-model loading/drawing commands, original furniture fallback, model
reuse/release, profile cleanup, saved state, memory guards, restored checkpoint,
and graceful shutdown also pass. The full 49,152-byte prefix is checked, not
just the earlier 32,768-byte furniture prefix.

The initial `native-01` attempt
already establishes full sound loading/transfers, model loading, English name,
all four rotation identities/categories/prices, actual installed constructor,
and first-hit animation. It then stops at the positional-sound expectation:
the title checkpoint's native scene zero suppresses positional sound. One
fixture correction enters the normal native audio mode through `Na_SceneMode`
and obtains the real listener coordinates through `Camera2_getMicPos_p`.
No cartridge sound code is changed for that correction.

No physical audio is emitted. Ordinary placement, final GPU appearance, completed
PCM/listening comparison, ordinary acquisition/persistence, and original-hardware
testing are not established by these component checks.

## Next actions and publication

Implement the actual scoring group, catalogue/acquisition rules, selected save
dependency, and Punchy house installation; batch ordinary interaction and
persistence with the remaining villager checks. Keep the disabled row unavailable
until those dependencies work.

V3 development source remains on `v3/optional-imports`. Stable V2, both served
patchers, deployment configuration, services, repository visibility, user saves,
and the released trailer remain unchanged. The user tests V3 and explicitly
approves any switch of the local or public patcher.
