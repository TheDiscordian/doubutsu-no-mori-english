# V3 NPC clothing checkpoint

## Implementation

The [clothing specification](../../specs/V3_CLOTHING.md) covers both NPC owners'
foreground and queued loaders, checked full shirt IDs, and unchanged native
slots, buffers, and relocation tables. Twelve guarded edits install the helpers.
The actual cherry shirt remains distinct from native `24BF`. Player wearing,
item readers/acquisition, and the clothing save registry remain pending.
Punchy's defaults, natural move-in flags, and web selections remain disabled.

## Artifacts

`build/v3-npc-clothing-01/animal-forest-v3-asset-loader.z64`, ABI 29.

- ROM SHA-256: `2406a6dee1bc07bf3edeceb8125bbded2e12c30fc508e0018aaac81fa1042372`.
- UPS SHA-256: `789c3d22741799898b4b55537e10929608b4a1ac23e012a50f51e8444b6196f8`.
- Resident prefix SHA-256: `1d8caa4cf5c74b9186e804ef8203ee3a29dd53fc55822d54eda8a7bba3a53676`.
- Asset helper SHA-256: `1f2ff4953119a7a083184d7ea4dee1eebe2a75337e5973f63364c92a812768f6`.

Combined asset code occupies 2,892 bytes, adding 512 bytes inside the existing
reservation. The resident prefix remains `C000`, its complete DMA file `F220`,
and clothing metadata/artwork and saved profile are unchanged. Shared indexed
reader instructions remain unchanged. Neither web patcher is updated.

## Bounded verification

Four focused tests pass in 1.165 seconds: original/imported/invalid indices,
missing resource fallback, exact transfer bounds, single asynchronous submission,
queue parameters and completion results, null/disabled rejection, all twelve
installed edits, source/control-flow/relocation guards, unchanged other cartridge
resources and saved profile, and UPS reconstruction.

The initial native attempt, `build/v3-npc-clothing-native-01`, stops before any
clothing call: its `26000`-byte temporary test allocation returns null. The
corrected retry, `build/v3-npc-clothing-native-02`, uses `23800` bytes, based on
the measured maximum `22640`-byte overlay/BSS/relocation plus test slots/outputs.
It allocates normally and verifies the complete relocated first owner and BSS.
Its complete foreground loop transfers native `24BF`, imported `34BF`, and
invalid furniture `3224` falling back to `2400`. All six complete texture/palette
outputs, completed slot flags, retained other flags, and seven unused slots pass.

The following queued check submits its requests and confirms all three pending
flags, but its immediate completion poll leaves the first flag pending. The test
does not advance a game frame between those calls; host debugger reads do not
advance emulated time. Queued completion is therefore unresolved, not passed or
established as a game defect. The second owner and final guards are not reached.
The fixture now uses the existing guarded native-frame advancement before that
poll; this correction has not been rerun. The initial attempt plus corrected
retry budget is consumed, and no further replay is queued in this batch.
No ordinary gameplay or persistence claim follows from these component checks.

Next useful native evidence is completion after a real frame and the second
owner's execution, preferably alongside ordinary clothing gameplay. Continue
player/item/save implementation without re-testing the completed foreground
prefix. Original hardware remains untested, and all existing saves are retained.
