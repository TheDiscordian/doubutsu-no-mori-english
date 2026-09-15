# Tent-model runtime integration

## Result

ABI 69 installs the complete `336C` tent model: four-part converted artwork,
create/move/draw/destroy callbacks, English name, 2,550-Bell price, 1×1 footprint,
catalogue entry, HRA/feng shui, and optional selected-import dependency.
It is additive and retains its donor summer-camper identity. Catalogue ordering
is explicitly forbidden for all rotations; ordinary shop stock is unchanged.

The offline composer contains 57 experimental options: 20 villagers, 34 furniture
items, and three shirts. Full selection reproduces the integration cartridge;
empty selection reproduces the exact stable V2 cartridge. Tent can be selected
individually without unrelated furniture or villagers.

Both local and public patchers remain V2. This is not a complete-import handoff.
Ordinary placement, GPU appearance, light interaction, acquisition, and
persistence remain unverified. The two fires and summer-camper reward route are
unfinished; this batch does not stand in for those parts of the full V3 goal.

## Artifacts

Full output: `build/v3-tent-model-runtime-01/`.

- ROM SHA-256: `29f5d1e6760dbfb4acc015f2a3482470fdbd43f1ce6ef03d156ecb1902ddab6a`.
- UPS SHA-256: `8e6b9455f696ae4277e1e7118cde058eddd8aa6c816203576def489ba22daea2`.
- Build-report SHA-256: `7d177af03b8ad4a19796c7034fc3a097a705b8d3654ba050ec8f697c7915b693`.
- Resident package SHA-256: `9b42348503aaa6cfb292489ee522d5af0f75a88d7325f2a25ff05acf14b66889`.
- Native evidence: `build/v3-tent-model-native-01/results.json`, SHA-256
  `c5febaae3ea5f07bc4a325e7df04505d1d485bdaf540df81655322bf5adbad43`.
- Tent-only experimental subset: `build/v3-optional-tent-model-01/`.
  ROM SHA-256: `3e4a8d23f783dbc50de9e05c986301db05a4526db2b3bb7e5d6bb12c77bb90e8`.

The installer consumes the pinned ABI 68 cartridge/report and complete
`build/v3-tent-model-callbacks-02/` callback output. It verifies the original
native callback/instance contract, complete converted asset, source hashes,
empty destination slots, selected profile, package checksum, and reservations.
It compiles only the changed catalogue and startup, not historical build chains.
The UPS reconstructs the complete new cartridge from the verified original ROM.

## Runtime and memory

The 580 callback bytes and 20-byte vtable occupy `80483400` and `80483700` in
the existing resident item-code reservation. Native startup loads that package
and invalidates the reservation before execution. The full 4,288-byte object
occupies VROM `0244E000`, with an 8,192-byte reserved slot. The canonical sparse
profile points to the actual callbacks; it is not a static substitute.

No resident package, normal heap, model-bank, or menu allocation grows. The
resource directory retains all 3,389 entries and its sole terminator. The
changed catalogue and relocations append inside the existing import resource,
using their existing directory entries. HRA/feng owners keep their allocations.
The import resource occupies 2,488,256 bytes, with 1,640,512 bytes remaining before
the relocated English choices. Catalogue code is 3,408 bytes with 256 spare;
the conservative menu requirement is 280,256 of 280,704 reserved bytes.

Each actor owns its fade. Its generic rig/texture pointers remain null, so the
private fade does not conflict with generic animation. Draw uses a frame-owned
matrix and palette, with checked arena bounds and native cache writeback. Moves,
destruction, and reuse cannot mutate previously submitted palette data.

## Verification

`python3 -m unittest tests.test_v3_tent_model_runtime tests.test_v3_optional_composition -v`
passes all **17 tests** in 13.223 seconds. Checks cover complete installed code,
vtable/profile/object/item rows, only intended ROM changes, retained native and
prior-import resources, directory/checksums, exact scoring changes, catalogue
memory limits, sanitized native catalogue rules, tent-only composition,
determinism, all/empty outputs, and existing dependency/save-codec rules.

The initial silent native run passes **69 records, 17 calls, and 48 assertions**.
It cold-boots ABI 69, verifies the loaded upper-memory callbacks and complete
tent profile/item row, and executes the installed name/type/price/size readers.
Two private furniture instances construct on/off, move in opposite directions,
and draw all four models with all sixteen interpolated palette entries. The
submitted palettes survive destruction and reuse. Actor/arena/stack guards,
the complete resident prefix, save-runtime state, and no-fault checks pass.
The native heap allocation is released, the checkpoint restores, and the
emulator shuts down cleanly. No speaker/headphone audio is enabled.

Existing lower-memory verified jump stubs call the installed Expansion Pak
code; callbacks are not copied to a different execution address. This exercises
the native matrix converter and cache function, but does not send the private
draw lists to the GPU. No ordinary gameplay or original-hardware claim follows.
No native setup retry is needed, and new harness work stays within the 30-minute
batch limit.

Subset export initially exposed two old item-report rows lacking an `id` field.
The enabled-state report now uses their canonical `item_id`, matching the actual
selection key. This was an export error, not an emulator failure or game crash.
The corrected export completes; its ROM hash, enabled-state reports, matching
package hash, and disabled web-patcher publication flag pass direct checks.

## Save boundary and next work

The saved format stays at version 2; selecting tent adds its fixed dependency
bit. Existing codec tests establish compatible equal/superset profiles and safe
rejection of missing dependencies. Ordinary cross-build save/restart is not
claimed. Preserve earlier saves and warn before a private gameplay handoff:
a town saved with tent selected requires a build that still includes tent.

Continue the complete campfire/bonfire rig, billboard, scrolling, and mapped
sound callbacks from the current ABI 69 cartridge. Install the existing four-cell
reader with bonfire, rebinding all five public item entries. Connect the actual
summer-camper acquisition route for all ten rewards, then verify ordinary
interaction/persistence alongside the remaining donor families and villager work.
Do not update either served patcher before user testing and explicit approval.
