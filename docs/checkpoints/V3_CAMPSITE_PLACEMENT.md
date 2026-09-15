# Native tent foreground placement and removal

## Installed work

ABI 75 supplies explicit tent handling in both native building-class readers,
preserving all original byte lookups. This fixes a real out-of-bounds route:
`5849` otherwise reads a byte of function-pointer data after the original
68-entry table. GC class 10 maps to native class 8: complete 3×3 foreground
placement, eight reserved neighbours, and housing-lot marker restoration on
removal. The actual donor class/callback/area tables are verified from the disc.

An eighty-byte adapter at `804A2A70` uses an empty gap between camper code and
the event index. The expanded twenty-item cleanup list at `804A2C80` retains
all nineteen native structures and adds the tent. The native event-finish loop
uses that list and the updated count. The complete English event-letter manager,
all other resources, descriptor identities, DMA directory, ordinary heaps,
resident package size, and model banks remain intact.

## Current artifacts

- Full: `build/v3-campsite-placement-runtime-01/animal-forest-v3-asset-loader.z64`.
- Full SHA-256: `f3893696555b91f4852e87b7bce6d09b1213faf4defe75e3f3dc09ece2b02efe`.
- UPS SHA-256: `95c7477fc40d476a1f89ad14422b9ef7404de62876c3728c0d591058695d17ee`.
- Build report SHA-256: `1b8c52f53a4d12effba713b1b8c02f3fc06008f47606c099d0792f50e4913762`.
- Package SHA-256: `917edee66cdc919de9f0f6b72be498980b78df6805bfbf152928a2f2210ba279`.
- Adapter SHA-256: `91b4a69468d6b57cec09f506cdab83d67f250c1ec55f45370d5e2c6003966f2d`.
- Ten-item camping subset: `build/v3-optional-placement-01/animal-forest-v3-asset-loader.z64`.
- Subset SHA-256: `5f68aff93c26329d464632aed5dc8cfd8277a20dd783158c65885983cb9c7af2`.

All/empty composition retains exact full/V2 outputs and all 59 experimental
choices. Both served web patchers remain on V2. ROMs, patches, donor assets,
and test saves remain ignored. This is not a complete-import playtest handoff.

## Bounded verification

`python3 -m unittest tests.test_v3_campsite_placement tests.test_v3_optional_composition -v`
passes sixteen checks. These cover donor semantics, exact hook/packet placement,
complete original-owner retention, rejected changed consumer/cleanup bytes,
package/startup CRC and N64 checksums, actual selected dependencies, and
all/empty/subset composition. No historical builds are re-tested.

The silent current native test uses `tests/scenarios/v3_campsite_placement.json`.
`build/v3-campsite-placement-native-01/results.json` contains **49 records,
eight complete native calls, eight register/delay windows, 39 passing assertions,
and zero failed assertions**. Results SHA-256:
`a306583bf90f907c3992362c8aab7ac111dffdc3ba71282fd9a99d8be50b711b`.
It passes on the initial run, restores the checkpoint, resumes without a faulted
thread, and shuts down cleanly.

The eight instruction windows check both detours with the new tent, the original
igloo, shop, and final native building index, including unchanged caller stack
and full-register/delay results. Complete native area calls retain the donor's
origin-only event-lot query, distinct from its actual nine-cell placement.
The native foreground setter rejects an edge that cannot hold 3×3 cells,
then places all nine cells at a valid location and removes them through the
real native lot-restoration path. The eight neighbours clear and the centre
becomes a valid reserved-house sign. Town lists, import save runtime, owner
guards, and no-fault checks pass.

The 2,048-byte heap fixture supplies indoor-field data for the native saved-town
foreground path; it does not construct a full scene. No test FlashRAM write is
requested. The isolated emulator's blank save files are not persistence proof.
The full event-finish traversal, tent actor constructor/GPU, ordinary entry/exit,
conversation, rewards, and save/restart remain untested by this batch. The
unresolved exterior background-allocation result stays open; this smaller data
fixture neither reproduces nor explains it.

## Remaining work and save compatibility

Extend the **installed English** event-manager owner at VROM `03800000`, retaining
its 38,128 bytes and 433 relocations before appending the new control/callbacks.
The [campsite specification](../../specs/V3_CAMPSITE.md) records verified control,
status, placement, and saved-area bindings. Connect checked start/stop, camper
selection/registration, greeting transitions, remaining masked NPC readers,
the actual English conversations and selected rewards, and scene lighting.

Saved format 2 and selected identities remain unchanged. Equal/superset profiles
are accepted by the codec and missing dependencies rejected; ordinary
cross-profile reload is still unverified. Never load imported saves in V2.
The complete V3 goal, other donor content, and browser composition remain open.
GitHub development source is allowed; switching either patcher requires the
user's testing and explicit approval.
