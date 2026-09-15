# Saved camper and resident exclusion

## Implemented

ABI 77 prevents a saved summer visitor from simultaneously becoming a town
resident. The actual donor `mNpc_GetRemoveAnimal` checks the summer event's saved
identity before accepting a transferred villager. The installed transfer wrapper
adds that rule before the native acceptance/copy path. Its ordinary free-state
result remains unchanged. No outgoing-transfer branch is changed.

The normal-growth candidate check also excludes the saved visitor, independently
of appearance history. This closes the case where an all-appeared reset clears
the camper's seen bit. Other residents, personalities, selected imports/outfits,
candidate ordering, and the native random draw retain their existing rules.
Releasing the camper event record restores normal eligibility.

The 252-byte helper at `80463EE0` ends at `80463FDC`, after the complete existing
clothing-menu/wearing code and before the shared villager reader. Two existing
call instructions change: `804636B8` in the growth candidate check and
`800AC650` in native incoming transfer. Both delay slots remain. The wrappers
call the actual native Animal-search, free-state, and saved-event readers.
Neither RAM reservation, heap limit, resource size, DMA entry, nor saved format
changes. The candidate wrapper is used only for an occupied/not-occupied check;
its conflict result is never used to index a resident.

## Artifacts and verification

- Full: `build/v3-camper-movein-runtime-02/animal-forest-v3-asset-loader.z64`.
- Full SHA-256: `31771d9e0fe23dba25fe1a8643f0124705ea40948b4c060853036fb4e150214f`.
- UPS SHA-256: `af70ca8f866a815d70a78b0fb75643585e1618725e79d523555667067630bdb9`.
- Build report SHA-256: `d9e18c193d9a3955bc4069fea18913f7ccc083b07211d658918bb8d3de2464b1`.
- Helper SHA-256: `14e5ffb1c9f404c3dc527ed0a4ef8c44fcc059651220d917d5e0e85708eadcf5`.
- Ten-item subset: `build/v3-optional-camper-movein-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `126f694d6bc708ef66a38d7a181de6be9fec932f825bd49cad63a2f5b1a8d874`.

`python3 -m unittest tests.test_v3_camper_movein tests.test_v3_optional_composition -v`
passes fifteen checks. The actual adapters run with address/undefined-behaviour
sanitisers. Native and imported identities, absent/nonmatching/invalid event
records, existing residents, and ordinary free-state results are covered.
Complete cartridge retention checks allow only the two calls, helper, ABI/CRC,
and startup updates. The complete existing English manager and all other game
resources remain identical. All/empty offline composition still reproduces
the full/V2 cartridges exactly; all 59 experimental choices remain available.

The first silent native run, `build/v3-camper-movein-native-01/results.json`,
passes **48 records, 22 calls, and 25 assertions**, with zero failures. SHA-256:
`13af288dd0f9652371d2f8ade8494b771e37d7a0fe1d5eac4ff24b4bdb899a28`.
It executes the installed native growth entry before/after an actual event-save
reservation, actual all-appeared reset, the complete native/imported candidate
set, and the complete native incoming-transfer function. The rejected camper
changes neither the town Animals nor the incoming Animal nor its saved visitor
payload. Native/imported identity checks and re-eligibility after area release
pass. The test restores saved RAM, transient state, and the checkpoint, resumes
without a fault, and shuts down gracefully. No FlashRAM write/reload is requested.

The initial compile-only output directory contains no cartridge: the installer
rejected an occupied candidate reservation before any output ROM was written.
The accepted helper uses the checked gap after the complete clothing owner.
A focused-test comparison was corrected to account for JSON's tuple-to-array
conversion; actual code and cartridge did not change for that fixture correction.

## Remaining work and publication boundary

Continue masked NPC construction/quest routing, actual English summer greetings
and conversations, first-greeting completion state, selected rewards, and scene
lighting/floor sounds. Ordinary arrivals, house construction, campsite entry/exit,
GPU appearance, acquisition, and persistence remain unverified. The complete
V3 scope also retains other donor content and browser composition; this is not
a complete-import playtest handoff.

Saved format 2 and selected identities are unchanged. Imported saves require
matching/superset profiles and must not be loaded in V2. Codec checks are not
ordinary cross-profile save/reload proof. Both served patchers remain V2;
development source may be pushed on `v3/optional-imports`, but switching either
patcher requires user testing followed by explicit approval.
