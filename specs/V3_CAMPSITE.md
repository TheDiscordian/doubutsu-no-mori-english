# V3 summer campsite

## Purpose and boundary

The ten camping furniture rewards belong to the donor's summer-camper
conversations in an enterable tent. Install that acquisition route, not ordinary
shop stock or an unrelated gift source. The decorative tent model `336C` and
collectible lantern `339C` do not supply the enterable building or scene light.

`tools/v3_campsite_art.py` converts the complete exterior, projected shadow,
interior, and scene lantern from the pinned GAFE01-r0 donor. The converter
verifies the actual decoded REL and symbols, full arrays, model relocations,
materials, and dynamic references. `tools/v3_campsite_scene.py` converts the
scene/field packet, and `tools/v3_campsite_runtime.py` installs its loader and
all four assets in ABI 71. Event, exterior actor, conversations, rewards, and
special scene lighting remain unfinished. Neither served patcher changes.

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
remove geometry/textures to fit. The installed field uses the engine's existing
40,960-byte background allocation. No model-bank or normal heap limit grows.

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
  places the special camper identity `D08F` at unit `(3,3)`. Original native
  scenes occupy indices 0–34. The adapter assigns new index 35, not donor index
  51; the scene-status and field-table readers both support the added record.
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

## Installed native scene and field

`overlays/v3/campsite_scene.c` supplies 580 bytes of resident code at `804A0100`
and a checked 4,096-byte packet at `804A1000`. Its `AFCP` header binds version 1,
packet size, native scene 35, and donor scene 51. No writable globals or BSS
are added. The native scene caller clears descriptor byte 19, so the new
descriptor lives in the loaded writable packet.

| Resource | VROM | Bytes |
| --- | --- | ---: |
| Native campsite scene | `02480000` | 128 |
| Camper load list | `02480100` | 48 |
| Complete extended field directory | `02480200` | 4,896 |
| Interior object | `02484000` | 19,872 |
| Lantern object | `02489000` | 3,248 |
| Exterior object | `0248A000` | 6,960 |
| Projected-shadow object | `0248C000` | 800 |

All 35 original 136-byte field records remain intact. The added record uses
field `3012`, one block, and donor combination `05BC` (background `F3`, foreground
`199`, type `FF`). Native scene-control actors and door commands match the donor
and retain native segment-2 addresses; the donor's player position is converted.
The complete 24-byte-per-actor camper list retains masked identity `D08F` and its
sentinel. Registration of that camper identity is still required before entry.

The packet retains all 256 collision records and all 256 foreground cells,
including exit markers `4080` at cells 98 and 99. Donor/native collision corner
labels differ, but all five height fields agree within each donor cell, so this
room does not require guessing a corner permutation. Native background and
foreground setters still decode collision, cache heights, and initialise fields.
Other field IDs call the original native block initializer. No original field,
background, scene, or item slot is replaced.

The gameplay overlay's status-table calculation calls the resident selector,
preserving its game pointer and signed scene argument. Its room-sound switch
retains every original result and adds tent result 2. It must not call a linked
`808...` overlay address as though it were permanently resident. The old local
sound-selector relocation `44001818` is removed; all other 127 records remain.
The edited overlay and relocation resource use new physical storage but retain
their original VROMs and DMA directory slots. The directory still has 3,389 files
and its original terminator.

The checked resident package expands from `2D010` to `2F010` bytes, adding 8 KiB.
Its original guard at `804A0000` remains, the packet has its own tail guard,
and the final package guard moves to `804A2000`. Package end `804A2010` stays
below the furniture pool at `80500000`. Startup verifies the larger CRC and
invalidates the new code reservation. Saved format 2 and selected identities
remain unchanged. The offline composer uses this current cartridge, retains
shared scene data in nonempty profiles, and reproduces exact V2 when empty.
Event activation must be conditional on selected camping content when installed.

## Integration and verification still required

Finish enterable exterior actor/collision, event schedule and saved camper
identity, NPC/conversation readers, scene lighting/floor sounds, and enabled
reward filtering. Assign stable additive identities without replacing existing
scenes, events, or furniture. Only selected rewards may be awarded.

After installation, use one bounded combined native/gameplay batch for entry,
camper conversation and reward handover, exit, and persistence. Do not rerun old
fire or static-furniture component tests unless those implementations change.
Asset checks are not evidence of GPU rendering, ordinary acquisition, save
compatibility, or original-hardware acceptance. The full V3 objective remains
open, including other donor content and browser composition.

Executed conversion checks and artifact hashes are recorded in the
[art checkpoint](../docs/checkpoints/V3_CAMPSITE_ART.md). Current installed-scene
checks are recorded in the [runtime checkpoint](../docs/checkpoints/V3_CAMPSITE_SCENE.md).
