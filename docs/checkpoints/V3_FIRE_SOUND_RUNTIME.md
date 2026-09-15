# Native fire sound installation

## Result

`tools/v3_fire_sound_runtime.py` installs the complete campfire/bonfire sound
programs and their two missing instruments through the ordinary N64 audio
loader. Native level IDs `5C/5D` select the reviewed two-layer programs; every
original level target and the speed-bag trigger remain intact. Unassigned level
IDs terminate safely. Fire furniture callbacks and profiles are still required.

The current offline composer has 57 experimental selections. All/empty outputs
retain the exact current full/V2 cartridges, with deterministic individual
selection and unchanged dependencies. Both served patchers remain V2, and no
new fire item is presented as selectable or complete gameplay.

## Artifacts

Full cartridge: `build/v3-fire-sound-runtime-01/animal-forest-v3-asset-loader.z64`.

- ROM SHA-256: `f3d055a74c2172029755b6be39e84b29658a17e83ef599a4f2fe6453570cb48f`.
- UPS SHA-256: `27d682f35199ec78f5e37e26d55a96db2fa7295d59aaae221584144ffde21556`.
- Report SHA-256: `75894b4b5a77b31ffcc34e32766d38abc6a65c899326b0aaa8e66413a246e7ce`.
- Native evidence: `build/v3-fire-sound-native-01/results.json`, SHA-256
  `ec988ef4aaaba47e994b8fb6c07a46b2c8cef7b873e0bf6acf08077657e246e3`.
- Tent-only subset retaining the sound runtime: `build/v3-optional-fire-audio-01/`,
  ROM SHA-256 `756fc2e27b73e0394984cd67a7d006a283b6bc475d2e36a17aee5418bea74b16`.

The installer consumes the pinned current tent-loader cartridge and
[complete fire sound conversion](V3_FIRE_AUDIO.md). Complete resource hashes,
source/operand checks, allocation bounds, unchanged resources, directory capacity,
N64 checksums, and full UPS reconstruction pass. No existing cartridge or save
is overwritten, and no game-derived file is committed.

## Memory and physical storage

Both the actual `malloc` size and the size passed to audio initialization become
`47E00` (294,400 bytes). The fixed/permanent sizes become `1DC00/1AC00`.
All three grow by 1,024 bytes: session/cache capacity and the fixed pool's
non-permanent allowance remain identical. Conservative use by all seven
permanent resources is 109,312 of 109,568 bytes, leaving 256 spare.
Actual native initialization confirms all three pool boundaries and usage.
This changes the ordinary audio allocation by 1 KiB, not the entire game heap
boundary or the existing Expansion Pak model/package reservations.

The complete 5,504,048-byte native wave file moves to physical `03800000`.
Its original contents remain intact, followed by only the new 21,360 aligned
sample bytes. The old physical allocation is retained but no longer selected
by the wave initializer. The same VROM directory entry grows within its
reservation; the directory still has 3,389 entries and its sole terminator.
The ROM remains 64 MiB, and future import-resource growth has space below the
relocated wave file.

Wave 2 retains its separate physical location `01F51D60` inside the import
resource, including all imported villager samples. Its new unsigned relative
offset `FE751D60`, plus group base `03800000`, yields that same address through
the verified native `ADDU` at `800EA948`. All six actual initialized wave
headers pass native comparison, including this external resource. No wave data
is assumed to live at its VROM address.

The 20,176-byte sequence and 11,280-byte font append inside the existing import
resource, whose remaining VROM capacity is 1,609,056 bytes. These are streamed
audio data, not additional resident package copies. The checked startup prefix,
save code, item/assets/catalogue, package, and ABI 69 stay unchanged.
The `fire_sound` report owns the current audio address map; older sound sections
retain provenance and point to the replacement map.

## Verification

Five focused cartridge checks pass. Four pass on their first run; the retention
check initially expects the native file-table resource to be entirely unchanged.
That resource contains the two deliberately changed directory rows. Correcting
that expectation, while checking all other bytes, passes its focused rerun.
The same run passes all twelve current composition checks: **13 tests in
10.370 seconds**. No old cartridge is executed or historical suite replayed.

The initial silent native run passes **74 records, four calls, and 29 assertions**.
It cold-boots the current cartridge and verifies all three audio pools, all six
wave headers, actual sequence/font headers, relocated level table, and complete
74-instrument font. Every original and imported instrument, envelope, sample,
loop, and predictor binding matches the expected native relocation.

Both free system-level slots receive the new sound IDs through ordinary native
start calls. Actual completed ROM sample transfers appear at frame 2 for the
sustained wave and frame 33 for the crackling wave, after its real 100-tick
initial rest. Native stop calls release both slots. Programs/envelopes, save
state, the full resident prefix, translation guard, and no-fault checks pass.
The emulator checkpoint restores and shutdown is clean. No native setup retry
is needed, and new harness work stays within the 30-minute batch budget.

This is combined native level-dispatch/sample evidence, not separate listening
certification for both mixes. No speaker/headphone playback occurs. It does not
establish positional furniture interaction, final graphics, acquisition,
ordinary save/restart, or original-hardware acceptance. The system-level route
is used only by the isolated test; furniture must use its per-actor positional
refresh/stop route.

## Continuation and saves

Continue the complete fire rig, billboard, and texture scrolling, connecting
the installed loop sounds to actual positional callbacks. Install the bonfire's
four-cell readers, item profiles, catalogue/scoring, and optional dependencies;
then complete summer-camper acquisition and other donor work.

Saved format and selected profile are unchanged by this sound installation.
Existing imported saves still require a matching/superset V3 profile and must
not be loaded by V2. Ordinary cross-build reload is not newly verified. Keep
the complete V3 goal active and both served patchers on V2 until user testing
and explicit approval.
