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
all four assets. `tools/v3_campsite_exterior.py` adds the complete exterior
callbacks and native structure-loader binding. ABI 73 adds the native calendar
and expanded event index. ABI 74 supplies an independently owned visitor Animal,
registration/defaults, and native NPC-info attachment. ABI 75 supplies native
tent foreground placement/removal classification and event cleanup. Event-manager activation,
remaining masked readers/conversations/rewards, and special scene lighting remain unfinished. Neither
served patcher changes.

`overlays/v3/campsite_event.c` supplies the calendar, selection, and start/stop
module. `campsite_calendar.c` binds its calendar to the native directory and
date operations. Selection and lifecycle entries still require the event-manager
and greeting/placement adapters. The [native calendar checkpoint](../docs/checkpoints/V3_CAMPSITE_CALENDAR.md)
records fifteen focused/composition checks and passing native calendar/save-area
execution; these do not establish an active tent visitor or ordinary acquisition.

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
  handling. The native calendar uses an independently allocated type index,
  retaining the original sixteen daily-event slots. Manager callbacks and full
  visitor binding still require integration.
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

The checked resident package is `30000` bytes. Its original guards at
`804A0000` and `804A2000` remain, the scene and calendar packets have their own
guards, and the final package guard is `804A2FF0`. Package end `804A3000` stays
below the furniture pool at `80500000`; its VROM end `02430000` meets the next
existing resource. Further growth needs separately checked storage, not an
in-place increase. Startup verifies the complete CRC and invalidates the new
code reservation. Saved format 2 and selected identities remain unchanged.
The offline composer retains shared scene data in nonempty profiles and exact
V2 when empty. The calendar requires selected camping content; event-manager
activation must preserve that condition when installed.

## Installed exterior actor

The native structure loader gives foreground `5849` a separate resident actor
`CA`; `C9` remains the original no-demo sentinel. All 201 original descriptors,
the igloo actor, and its artwork remain unchanged. The native active-actor limit
remains 201. Only the descriptor lookup in `Actor_info_make_actor` is extended;
each live actor retains its exact descriptor pointer for later destruction.

The controller's setup callback intercepts `5849` and forwards all other building
IDs to the existing relocated controller. Its original two HI/LO relocations
`45001528` and `46001530` are removed; the other 120 remain. The controller and
relocation resources keep their VROMs and existing DMA directory slots. Tent setup
requires at least one of the ten actual camping-item enable rows; no-selection
profiles cannot create this actor.

The native birth controller routes every `5xxx` foreground through the structure
callback (`80936010..80936160`); it does not index a bounded building table first.
It skips `Fxxx` temporary markers. Thus `5849` reaches the new selector and `F127`
does not request another actor. This is verified against the original native
instructions, not inferred from GameCube constants.

`overlays/v3/campsite_exterior.c` uses 3,168 bytes at `804A0360`, leaving 64 bytes
before the scene packet. Its separate `AFTE` actor packet occupies 496 bytes at
`804A1800`, within the scene packet's unused gap. Startup CRC and instruction-cache
coverage include both. There is no additional permanent RAM, model bank, or
ordinary heap-limit increase. The actor remains exactly `2D8` bytes, the native
structure pool's fixed stride; never enlarge it in place.

Each live tent owns a checked 7,776-byte heap allocation containing the complete
6,960-byte exterior, 800-byte shadow, and 16-byte guard. A failed allocation or
DMA deletes the actor without changing foreground/collision. Destruction clears
the entrance reservation and frees the assets. The native actor lifecycle restores
foreground `5849` in place of temporary marker `F127` and returns the pool slot.
This lifecycle is implemented; complete native execution remains unverified.

The callbacks preserve buried-item recovery, all nine donor collision records,
door request angle/distance, outside return coordinates, scene-35 entry, and
window fading at 05:00/18:00. The door uses native wipe/BGM command `028A`, not the
unrelated donor numeric encoding. GC's `0800` texture-adjust flag is not an N64
actor flag. Window display-list and complete projected-shadow vertices use
separate segment-8 bindings in checked frame-owned storage. Exhausted or
misaligned opaque/shadow arenas cause no partial draw.

The [exterior checkpoint](../docs/checkpoints/V3_CAMPSITE_EXTERIOR.md) records
sixteen focused/composition checks and partial native evidence. Actual controller
relocation, setup registration, descriptor selection, and pool initialization
pass. The combined native probe stops at a field-background allocation bound
before actor construction; the cause is unresolved. Do not claim native tent
construction, drawing, cleanup, natural entry, or persistence from that run.

## Installed native calendar

The event module preserves the supplied donor's twelve-byte calendar row,
seasonal month substitution, Sunday adjustment, and separately ordered exit-frame
and inside-tent rows. It retains the inclusive ending hour 14. Date subtraction
handles day zero like the donor; the native helper does not. The native calendar
adapter also translates the weekly encoding: GameCube uses week 7/current and
6/last, whereas N64 uses 9/current and 15/last. It retains GameCube's month-end
clamp and uses native first/last Saturday decoding where required. The original
date functions and schedules for other events remain unchanged.
Visitor selection uses six personalities and the donor's 236 shuffle operations,
with full fixed IDs and an explicit installed-selection predicate.

Event type 70 uses the independently allocated 128-byte index at `804A2B00`.
All eighteen native index readers/writers move, including the direct event-16
consumer. Native initialization still owns its original BSS, then initializes
the new index. Both cleanup loops cover types 0–70. End pointers for the
unchanged daily-event array retain their original addresses, even where those
addresses equal the old index start. Forty checked instruction writes install
these changes and the initialization/pre-cleanup calls. The calendar runs inside
the original job gate and preserves the native first-entry result.

The 1,600-byte event module at `804A2100`, 588-byte native adapter at `804A2740`,
index, and checked packet at `804A2C00` add 4,080 resident bytes. Normal heaps,
model banks, and the sixteen daily-event slots remain unchanged. Native shared
readers, actual calendar insertion, saved-event allocation/readback/release,
neighbouring BSS, and guards have passing current evidence. These are emulated
RAM checks, not save/restart persistence or completed tent gameplay.

## Integration and verification still required

The five native event-save areas offer forty payload bytes each, with two
needed for the camper. The independent visitor owner below supplies the full
Animal without using a town slot. Connect the event-manager and remaining masked
readers before tent activation. Preserve allocation-failure handling and do not
register an unsupported masked identity against bounded original actor tables.

Finish event-manager activation and saved camper
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

## Independent camper ownership

`camper.c` and `camper_reader.c` install the native counterpart of GC's
`mNpc_RegistMaskNpc_summercamp` and masked `mNpc_SetNpcinfo` branch. All five
original twelve-byte aliases and fifteen town Animal/NpcList slots remain.
An existing matching alias retains its Animal and memories; a conflicting alias,
full table, disabled import, test ID, or incomplete outfit fails registration.
Registration never clears an Animal referenced by an existing alias.

| Owner | Address | Bytes |
| --- | --- | ---: |
| Checked visitor header/state/Animal/guard | `804A1A00` | 1,376 |
| Complete native Animal inside owner | `804A1A20` | 1,320 |
| Preserved native NPC-info prologue/trampoline | `804A1F60` | 16 |
| Native NPC-info attachment adapter | `804A29A0` | 200 |
| Complete registration/default/memory adapter | `804A2D00` | 448 |

These reservations are verified unused before writing. The scene packet's
existing exterior descriptor, scene guard, event index/calendar packet, and
final package guard remain. Package size stays `30000` and neither the normal
heap nor furniture pool grows. Startup verifies the whole package and invalidates
`804A0100..804A2FFF`, covering both adapters and the original-function trampoline.
Its native NPC-info detour preserves the full original path for unrelated actors.

Registration uses the installed optional-town predicate and full indexed-default
initializer. Both ordinary imports and selected islanders receive their actual
personality, outfit, catchphrase reference, and town identity. Zero outfit means
the animal's default; valid native/additive or reserved `FE20` overrides remain,
and invalid explicit overrides use `2400`. The registered texture and identity
are both the full actual `E0xx`, not a table index or replacement resident.

The session greeting flag is owner byte `10`. The caller resets it for a newly
selected camper and sets it after the actual first greeting. Re-registration
with the flag set recreates the current player's first memory via the native
memory setter. **Native Animal memories start at `+10`, not `+0C`**; the original
initializer at `800A7A28` accounts for alignment. Personal IDs are sixteen bytes,
the timestamp starts at memory `+10`, and friendship is at memory `+28`.
The registration caller must supply the actual current private-player pointer.
Greeting state transitions are still an event-manager/conversation task.

The NPC-info adapter gives `D08F` the dedicated Animal and a null town NpcList,
as in GC. A cleared or mismatching alias gives null pointers even if the caller
supplies a valid resident index. Existing English actor-name and draw-record
readers then resolve through the actual animal/alias. This does not by itself
establish a complete NPC constructor, conversation, GPU draw, or save/restart.
The [camper checkpoint](../docs/checkpoints/V3_CAMPER.md) records current evidence.

## Native tent placement and cleanup

The original building-class table at `8010699C` has 68 bytes for `5800..5843`.
Its biased lookup at `8010119C + item` would read `5849` from the following
function-pointer table, not a valid class. Both consumers (`8008D4A8` in
`mFI_SetFGStructure_common` and `8008D5BC` in the structure-area reader) use
explicit tent detours. Every other input executes its original byte lookup.
Do not move the table base and thereby change undeclared original inputs.

The eighty-byte adapter at `804A2A70` ends at `804A2AC0`, after the complete
camper reader and before the event index. No new allocation is required. It
preserves the displaced load/LUI and the native continuation; only the already
dead `at` scratch register changes in addition to native outputs.

GC's actual class byte for `5849` is 10. Its callback matches the donor's 3×3
callback, and removal restores the reserved housing-lot sign. Native class 8
provides those semantics through `8008D12C` and `800879B0`. Both games' area-query
rows for this temporary lot type are origin-only, separately from the nine-cell
foreground reservation; retain that distinction rather than assuming a larger
query rectangle. The original igloo uses the same restoration class.

The complete nineteen-entry event-structure cleanup list is retained and extended
with `5849` at `804A2C80` (forty bytes). The native finish loop's base changes and
its existing count word becomes twenty. This lets ordinary cleanup find and
remove the tent without overwriting the padding before the original count word.
The packet CRC, overall package CRC, and startup prefix CRC cover the changes.

The [placement checkpoint](../docs/checkpoints/V3_CAMPSITE_PLACEMENT.md) records
passing native nine-cell placement, invalid-edge rejection, lot restoration,
area calls, and all eight full-register instruction windows. The test uses
native saved-town foreground with a small indoor-field data fixture, not a
constructed scene. It does not execute the full event-finish traversal, create
an exterior actor, establish conversations, or write/reload FlashRAM.

## Event-manager integration contract

Extend the installed English manager at VROM `03800000`, linked RAM `8095B8B0`,
not the absent original VROM `00850680`. The installed file is 38,128 bytes,
ending at `80964DA0`, with 1,760 relocation bytes and 433 retained relocations.
Its descriptor at `80101310`, profile `809622EC`, and 592-byte instance stay.
Preserve the complete English suffix, original zero-initialized BSS addresses,
save/destructor retry wrappers, and native control logic when appending camper
callbacks. This manager extension is not installed yet.

The original 28 controls occupy `80961F48..809622C8`, with a separate count at
`809622C8`. Each control is 32 bytes. A complete relocated copy plus a 29th
summer control fits the existing 32-pointer daily list at `809623D8`; its live
count is `80962458`. The two control-base HI/LO pairs begin at `809612F4` and
`809612F0`, with low instructions at `80961300` and `80961304` respectively.
Retain their relocation handling. Native status dispatchers are `80961004` and
`80961100`; zero callback results retain pending transitions for retry.

Native lot placement is `8095D324(manager, control, foreground, area)`, with
summer area `51`; removal is `8095D1E0(control, area)`. Placement uses saved
location area ID `77`, twenty-byte place records, and the native vacant-lot
picker. The independent two-byte camper identity uses event save area zero.
Do not substitute the GC structure layout or mark start successful when visitor
registration or placement fails. Complete the remaining masked NPC readers and
conversation binding before presenting an active tent as playable.
