# V3 speed-bag asset checkpoint

## Completed conversion

`tools/v3_speed_bag_art.py --output build/v3-speed-bag-art-01` succeeds on its
first build with the existing pinned Docker compiler and supplied English disc.
The [specification](../../specs/V3_SPEED_BAG.md) records the verified identity,
profile/callback bindings, graphics settings, rig, layout, and remaining behaviour.

- Object: `build/v3-speed-bag-art-01/speed-bag.n64obj.bin`, 3,728 bytes.
- Object SHA-256: `3b10054b80021c00a5a12d98aeb4afcd76b7201ad68f55c1ac77c1b3a7844893`.
- Base commands: 768 bytes, SHA-256 `da944836268e4ecc14d835a2bb9e957562a085eb3defe3595d014e7154952fde`.
- Ball commands: 272 bytes, SHA-256 `1c9aa226b6500e5ff5d3cefbf3979e8b6224c68ef6e444139f48d07622c9fee8`.
- Generated compiler input SHA-256: `9ffded461039b3ca88c64985c2853f7827a424ae104d2ddf5f841f77fbda3629`.
- Existing room-bank capacity: 5,120 bytes; 1,392 remain unused by the asset.

The actual object contains all eight textures, both palettes, 62 vertices,
44 triangles, 24 animation keys, six constants, both joints, and all native
headers. All seven rig/model pointers are rebound within its segment-six range.
No ROM, existing save, item ID, live service, or patcher changes.

## Focused verification

`build/v3-speed-bag-art-tests-01.log` passes all 11 tests initially, in 1.301
seconds: six speed-bag checks and the five original static-converter host checks.

- Explicit environment-map scale/wrap/shift support, with the default static
  parser still rejecting those settings and unknown variants failing closed.
- Animation dimensions, channel/key counts, ordered duration, and malformed
  input rejection.
- Synthetic same-module callback relocation, including wrong-section,
  out-of-range, and external-module rejection.
- Actual supplied donor profile, name, both quality tables, and all three
  callback bindings through the complete checked REL.
- Independent pixel-by-pixel GX block addressing for every converted texel,
  both palette conversions, and all vertex fields.
- Independent decoding of complete compiled native display lists: every face,
  material/palette load, texture dimension, scale, wrap/shift, render state,
  vertex-cache bound, and list ending.
- Exact retained animation arrays, all seven native pointers, every non-pointer
  header/joint field, and complete-object bank bounds.

The two actual-donor static-retention checks also pass in
`build/v3-speed-bag-static-retention-01.log`: the changed shared helpers retain
both complete barrel assets and every compiled face/material/load. These are
host-side resource comparisons, not replays of historical cartridges.

`python3 -m py_compile` passes for all changed/new Python modules after the native
fixture syntax correction. Generated game assets stay ignored; only original
conversion/test code, scenarios, and documentation enter Git.

## Native fixture limit

The bounded native fixture is intended to evaluate frames 1, 57, and 69 using
the unchanged N64 keyframe engine, with the converted object in a private
allocation. It saves/restores segment bases, checks complete object/state and
memory guards, frees its allocation, and requires full checkpoint restoration.
It is not an installed-item, GPU rendering, interaction, or audio test.

`build/v3-speed-bag-art-native-01` reaches the initial emulator checkpoint and
native graph-thread pause but stops while importing the new helper because of
a missing closing parenthesis. No fixture allocation or keyframe call executes.
The syntax is corrected and compilation checked.

The single resume attempt, `build/v3-speed-bag-art-native-02`, is rejected before
an emulator starts: the aborted blank-cartridge run has no `test.flash` file,
which the existing checkpoint-resume contract requires. This is not a tested
save failure or animation defect. Stop setup retries for this batch. No native
keyframe result, restored-state result, or graceful native-test completion is
claimed. During the next callback-implementation batch, run the combined check
from a fresh blank cartridge; do not assume this checkpoint can be resumed.

## Next implementation

Implement the constructor, hit/retrigger update, and skeleton drawing against
verified N64 furniture fields and a verified sound mapping. Then install a
stable optional identity, native readers, and the real house dependency. Keep
ordinary acquisition, behaviour, persistence, and hardware acceptance open;
neither this conversion nor an English name constitutes a playable import.
