# V3 animated speed bag

## Converted asset and remaining runtime work

`tools/v3_speed_bag_art.py` converts the complete GAFE01-r0 speed-bag asset:
both model parts, all textures/palettes/vertices, all animation tracks, the
two-joint hierarchy, and the native keyframe headers. The output is a local
3,728-byte segment-six object, within the existing 5,120-byte room model bank.

The native constructor, hit/retrigger callback, and draw callback are implemented
in `overlays/v3/speed_bag.c`; their actual N64 execution passes in private test
storage. The complete donor hit sound is extracted and assembled into bounded
native-compatible resources by `tools/v3_speed_bag_audio.py`.

This is not a playable import. Sound registration/allocation, callback/profile
installation, item registration/readers, and Punchy's house placement remain
uninstalled. Do not enable Punchy or substitute a static decoration for this
item. Both served patchers remain V2 until the user tests and approves V3.

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

## Native behaviour

The callbacks preserve the donor's constructor/move/draw sequence:

- Construct the two-joint skeleton, initialise stop-mode playback, evaluate
  the first pose, set speed zero, and clear the changed-switch flag.
- Preserve the move callback's evaluation order. A running update evaluates
  twice and sets speed 0.5. A new hit resets frame 1, evaluates again, and sets
  speed 0.5. Do not infer animation duration simply from the speed field or
  replace the damped keyframes with a generic wobble.
- Dispatch eligible hits through the explicit `af_v3_speed_bag_sound` dependency.
  A private observer verifies dispatch position and ordering without playing
  sound. Do not install a callback linked to that observer in a cartridge.
- Draw through the native skeleton routine using the actor's alternating
  matrix buffers and current model transform. Verify native field offsets,
  allocation, callback signatures, segment lifetime, and cleanup.

The actor stride is `740`, not the incorrect `A10` comment in the partial native
header. Position is at `008`, state at `03C`, changed-switch at `12D`, keyframe
at `134`, joint/morph arrays at `1A4/1DA`, and matrices at `210`. Each matrix bank
has ten 64-byte matrices, a stride of `280`. The two-joint object consumes three
joint vectors and two matrices; unused entries remain intact in the native test.
The Game graphics pointer is at zero, frame counter at `A0`, and opaque command
head at graphics-context `298`. The native skeleton routine also emits segment
13 into both opaque and translucent command lists.

The N64's appearing/disappearing states are **5, 6, 13, 15**, not the donor's
12–15. The checked native room transition exclusions at `8093DC5C` establish
that set; native moves 12 and 14 must remain sound-eligible. The room owner's
`80945060` loop clears changed-switch flags and advances actors by `740` after
the callbacks. The imported callback must not clear the flag itself.

`tools/v3_speed_bag.py` checks the complete native room owner and compiles 472
bytes of callback text. The linker rejects extra code/data sections; relocation
validation permits only explicit JALs to the six native engine entries and the
required sound dependency. There are no local absolute references, constant
pools, or writable globals. The validated text can move within KSEG0; that
property does not reserve production RAM or install a vtable. Entry offsets are
`000`, `094`, and `148`. Constructor/draw stack use is 48 bytes; move uses 32.

Native keyframe entries are `80052228` (construct), `80052298` (initialise stop),
`800528D4` (evaluate), and `800530D8` (draw). These addresses come from the pinned
N64 source/symbols. The [callback checkpoint](../docs/checkpoints/V3_SPEED_BAG_CALLBACKS.md)
records actual evaluation and draw-command execution separately from still
unverified sound synthesis, ordinary gameplay, and GPU appearance.

## Actual hit sound

The donor's `0176` dispatches through main sequence 242, group one, index 118,
to offset `062B`. Its program selects bank selector 1, instrument 103, starts
the note layer at `0632`, and gives that layer its custom envelope at `063A`.
Bank selector 1 resolves to donor bank 154, using wave bank 5. The note is 32,
duration 110, velocity 120, and envelope decay 240. Preserve the original
instrument tuning, loop state, predictor coefficients, and both envelopes.

The N64 main sequence is 199. Its group-one table has 97 entries; reusing `0176`
reads another table and resolves to unrelated program `1AF9`. Its selector-one
bank is 140 and has only 71 instruments. The complete donor sample is absent
from native wave bank 5. Neither the donor sound ID nor instrument number can
be copied directly into the native callback.

The local audio output consists of:

- A 208-byte, single-instrument font with all internal pointers rewritten to
  bounded bank-relative offsets; no drums or independent sound-effect rows.
- The complete 11,062-byte ADPCM sample, without a destructive waveform edit.
- A 27-byte channel/layer/envelope fragment whose sequence offsets, bank selector,
  and instrument slot are explicitly rebound by `bind_program`.

The zero-based fragment and standalone font are conversion artifacts, not a
registered sound. The installer must integrate the sequence dispatch, font and
wave data, IDs, DMA metadata, and actual audio-memory capacity before binding
the callback. Appending bytes to ROM does not enlarge a native audio allocation.
An existing-font append can reuse these extracted resources; introducing a new
font also requires reviewing the native font tables and readers. Native synthesis
and sound lifetime remain unverified. No physical audio is emitted by tests.
