# V3 animated speed bag

## Converted asset and remaining runtime work

`tools/v3_speed_bag_art.py` converts the complete GAFE01-r0 speed-bag asset:
both model parts, all textures/palettes/vertices, all animation tracks, the
two-joint hierarchy, and the native keyframe headers. The output is a local
3,728-byte segment-six object, within the existing 5,120-byte room model bank.

This is an animated asset conversion, not a playable import. The N64 interaction
callbacks, sound binding, item registration/readers, and Punchy's house placement
remain uninstalled. Do not enable Punchy or substitute a static decoration for
this item. Both served patchers remain V2 until the user tests and approves V3.

## Verified source identity

The converter verifies the supplied GAFE01 disc/revision, complete decoded REL,
and pinned symbols through the existing donor reader. Source identity is
`GAFE01-r0/item/3350`; `3352` in Punchy's house is its placed rotation, not a
different import. Both donor furniture-quality tables resolve index 1,236 to
`iam_ike_prores_punch01`, and the corresponding English name is “speed bag”.
No destination ID is assigned by this asset-only converter.

The 52-byte donor profile is at `.data:000928F4`; its sole pointer targets the
20-byte `fIPPnch_func` table at `.data:000928E0`. The callback table resolves
exactly to constructor `fIPPnch_ct`, move `fIPPnch_mv`, and draw `fIPPnch_dw` in
the same REL's text section; the final two callbacks are null. Resource pointers
continue to reject text targets unless text callbacks are explicitly requested.
Wrong sections, external modules, duplicate/missing pointers, nonzero relocated
words, and out-of-range targets fail conversion.

The actual scalar fields specify height 40, scale 0.01, shape 4, collision kind
0, no extra rotation flag, lighting map 1, contact 0, and interaction bits 0.
The scalar bytes alone do not implement the custom behaviour.

## Graphics conversion

The base has 24 triangles and the ball has 20, using all 62 supplied vertices.
Both sixteen-colour source palettes are retained as separate resources even
though their contents match. All eight CI4 textures are untiled into native
row order; the vertex conversion preserves position, UVs, normals, and alpha,
clearing only the recognised GameCube matrix flag.

The static furniture parser retains its strict default settings. An explicit
speed-bag mode additionally recognises only:

- Texture scale `4000,4000`, encoded as `D7000002 0FA00FA0`.
- The ball's 16×16 repeating tile with shifts `2,2`, encoded as
  `D2F0F522 00000000`; native output uses wrap, masks `4,4`, and shifts `2,2`.
- Geometry mode `00270405`, including generated texture coordinates for the
  reflective ball. Existing compatible lighting, fog, culling, and colour state
  remain intact; zero-scale base materials retain the existing native `FFFF` fix.

Palette and texture loads become native TLUT/texture-block commands; packed
GameCube triangles become native triangle commands. The converter does not pass
unknown Dolphin commands through to the N64. Visual appearance, including the
reflective material, remains unverified in an ordinary rendered scene.

## Native object layout

| Offset | Bytes | Contents |
| --- | ---: | --- |
| `0000` | 64 | Two RGBA16 palettes |
| `0040` | 1,408 | Eight CI4 textures |
| `05C0` | 992 | All 62 native vertices |
| `09A0` | 168 | Animation flags/counts/constants/keys, including alignment |
| `0A48` | 768 | Base display list |
| `0D48` | 272 | Ball display list |
| `0E58` | 20 | Native animation header |
| `0E6C` | 24 | Two native joint records |
| `0E84` | 8 | Native skeleton header |
| `0E8C` | 4 | Final alignment |

The animation has 69 frames, three animated rotation channels with `2,11,11`
keys, six constant components, and two joints. Every track begins at frame 1,
ends at frame 69, and has strictly increasing frame numbers. The base joint
has one child; the ball is its leaf. Both draw in the opaque list. Preserve all
source frame/value/velocity triples and the `-1` animation-header field.

The N64 `BaseAnimationR`, `JointElemR`, and `BaseSkeletonR` layouts match the
supplied structures. The converter rewrites all seven header/joint pointers to
bounded segment-six offsets. The native constructor resolves skeleton/animation
pointers, while evaluation and drawing resolve their nested segmented pointers.
Runtime integration must establish segment six for the selected model bank
before constructing or evaluating the animation.

## Behaviour implementation requirements

Port the actual constructor/move/draw sequence onto verified N64 actor fields:

- Construct the two-joint skeleton, initialise stop-mode playback, evaluate
  the first pose, set speed zero, and clear the changed-switch flag.
- Preserve the move callback's evaluation order. A running update evaluates
  twice and sets speed 0.5. A new hit resets frame 1, evaluates again, and sets
  speed 0.5. Do not infer animation duration simply from the speed field or
  replace the damped keyframes with a generic wobble.
- Bind donor sound `0176` to a verified native equivalent or port its actual
  sound data. Preserve the donor's sound-eligibility condition. The number is
  not assumed to be the same native sound ID, and no physical audio is tested.
- Draw through the native skeleton routine using the actor's alternating
  matrix buffers and current model transform. Verify native field offsets,
  allocation, callback signatures, segment lifetime, and cleanup first.

Native keyframe entries are `80052228` (construct), `80052298` (initialise stop),
`800528D4` (evaluate), and `800530D8` (draw). These addresses come from the pinned
N64 source/symbols; they do not establish that the complete furniture behaviour
has been executed. The [checkpoint](../docs/checkpoints/V3_SPEED_BAG_ART.md)
separates passing asset checks from the unexecuted native fixture.
