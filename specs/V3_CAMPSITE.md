# V3 summer campsite

## Purpose and boundary

The ten camping furniture rewards belong to the donor's summer-camper
conversations in an enterable tent. Install that acquisition route, not ordinary
shop stock or an unrelated gift source. The decorative tent model `336C` and
collectible lantern `339C` do not supply the enterable building or scene light.

`tools/v3_campsite_art.py` converts the complete exterior, projected shadow,
interior, and scene lantern from the pinned GAFE01-r0 donor. The converter
verifies the actual decoded REL and symbols, full arrays, model relocations,
materials, and dynamic references. It does not install the scene, event,
conversations, or rewards in a cartridge. Neither served patcher changes.

## Complete native scenery

| Part | Vertices | Triangles | Native bytes | Model offset |
| --- | ---: | ---: | ---: | --- |
| Exterior | 105 | 61 | 6,960 | `17D0` |
| Projected shadow | 28 | 16 | 800 | `0260` |
| Interior | 349 | 267 | 19,872 | `43F0` |
| Scene lantern | 45 | 25 | 3,248 | `0B10` |

All 527 source vertices, 369 triangles, 36,416 texture texels, and 128 palette
entries remain. RGB5A3 palettes become native RGBA16; tiled CI4/I4 texels become
linear texels. Position, UV, and colour/normal bytes remain intact. Only
GX-specific vertex flags are normalised. Each object binds its static resources
through segment 6; a runtime owner must establish that segment before drawing.

The interior is larger than the existing 9,216-byte furniture bank. It needs
scene storage and a checked loader; do not squeeze it into a furniture bank or
remove geometry/textures to fit. No new cartridge or RAM allocation is made by
the asset converter.

### Materials and frame-owned data

- The exterior has a window-colour display-list call through `08000000`. Retain
  that call, the unlit window material, and the surrounding lit tent materials.
  The exterior draw callback supplies a frame-owned two-command list containing primitive
  colour `(fade*255, fade*255, fade*150, 255)` and termination.
- The projected shadow loads 28 runtime-projected vertices from `08000000`, not
  the original unprojected array. Its complete source vertices, 28 fixed-vertex
  flags, 60-unit shadow height, and donor descriptor pointers are verified.
  The native shadow owner must supply frame-owned projected vertices and its
  normal primitive colour before drawing. The exterior's segment-8 display
  list and shadow's segment-8 vertices are different bindings for separate draws.
- The interior switches from CI4 materials to three I4 contact-shadow textures.
  Native texture-LUT mode switches from RGBA16 to NONE at that material boundary.
  Preserve the purple shadow tint, primitive LOD, decal render mode, and complete
  model order. Its separate translucent list is genuinely empty and remains a
  one-command terminator at native offset `4D98`.
- The lantern retains two 32×64 CI4 images simultaneously. Native tiles 0 and 1
  occupy TMEM words 0 and 128, below the TLUT; their palettes retain banks 15 and
  14. Preserve the two-texture primitive-LOD blend, mirrored S, clamped T, and
  unlit geometry. Loading both images into tile 0 would lose the light blend.
- The interior's 8×8 texture uses tile DMA so its four-byte source rows occupy
  correctly padded native TMEM rows. All other textures use the appropriate
  complete block or two-tile loads. Unknown commands and references fail.

## Donor scene and acquisition bindings

The pinned donor source, not a similarly named native enum value, defines the
required behaviour:

- `src/data/scene/tent.c` and `src/game/m_play.c` define `SCENE_TENT` (51), its
  scene entry, default player `(120,0,100)`, eleven controller actors, miscellaneous
  indoor field construction, and one outside exit. `src/data/field/mvactor/tent.c`
  places the special camper identity `D08F` at unit `(3,3)`. The native scene enum
  ends at 35 and contains no tent; appending GC scene numbers to a native table
  without extending its readers is unsafe.
- `src/actor/ac_tent.c` supplies the enterable exterior. Its door enters the tent
  at `(120,0,220)`; exit coordinates are reconstructed from the exterior actor.
  Preserve the nine-cell collision grid, foreground reservation/cleanup,
  buried-item handling, door requests, wipe/sound, shadow, and daylight window
  fade. The native igloo actor is a useful binding reference, not a slot to
  replace permanently.
- `src/actor/ac_event_manager.c` reserves the summer-camper event's save area,
  selects/registers the masked camper, and places/removes the tent on a vacant
  housing lot. Its entry/exit handlers also participate in the event lifecycle.
  `src/game/m_event.c` supplies the calendar adjustments and inside-scene event
  handling. Preserve the actual schedule and lifecycle; the complete native
  event layout and capacity still need binding.
- `src/game/m_npc.c` selects a non-appeared personality/candidate and records
  appearance history. Mask registration uses the actual animal's defaults,
  clothing, and the current player's remembered greeting state. Camper selection
  also excludes that animal from simultaneous ordinary move-in. Adapt to the
  installed optional-villager predicate rather than admitting disabled imports.
- `src/actor/ac_quest_manager.c` distinguishes the camper's first greeting from
  later conversations. `ac_quest_talk_greeting.c` supplies summer-specific
  greeting selection; `ac_quest_talk_normal_init.c` supplies the conversation
  setup and the 20% Tent furniture selection. Import the actual English dialogue
  and its state transitions, not a renamed igloo conversation.
- `src/effect/ef_effect_control.c` creates the tent lantern on scene entry.
  `ef_tent_lamp.c` supplies its timed light, primitive-LOD fade, and complete
  model draw. `m_kankyo.c` and `m_room_type.c` also treat the tent specially;
  room light, surfaces, and the hidden manual light switch require native
  integration. A converted lamp model alone does not install scene lighting.

The collectible lantern and sleeping bag remain non-interactive as their actual
furniture profiles specify. Their null callbacks and zero contact/interaction
flags are correct; do not add scene-lantern or bed behaviour to those items.

## Integration and verification still required

Bind native scene/room construction, exterior actor/collision, event schedule
and saved camper identity, NPC/conversation readers, scene lighting, and enabled
reward filtering. Assign stable additive identities without replacing existing
scenes, events, or furniture. Only selected rewards may be awarded; the optional
composer must retain required shared campsite data when any camping reward is
enabled and preserve exact V2 output for an empty import selection.

After installation, use one bounded combined native/gameplay batch for entry,
camper conversation and reward handover, exit, and persistence. Do not rerun old
fire or static-furniture component tests unless those implementations change.
Asset checks are not evidence of GPU rendering, ordinary acquisition, save
compatibility, or original-hardware acceptance. The full V3 objective remains
open, including other donor content and browser composition.

Executed conversion checks and artifact hashes are recorded in the
[campsite checkpoint](../docs/checkpoints/V3_CAMPSITE_ART.md).
