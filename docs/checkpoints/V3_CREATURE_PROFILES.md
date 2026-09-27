# Complete creature display resources

## Current output

`build/v3-creature-profiles-prepared-01/art.json` records seventeen complete
display objects, 78,544 bytes, and 738 triangles. Sixteen objects have embedded
rotational rigs: 96 joints and 79 shown-joint bindings, with every motion array
retained. The static ant has three drawing layers. The largest object, the frog,
uses 9,824 bytes and fits the current 12-KiB model bank without truncation.

The batch covers source insect displays `1C48..1C64` and fish displays `1C6C`
and `1CE8..1D04`, at four-ID intervals. Source placement and pickup functions
resolve their actual carried parents. This is not a claim of seventeen new
native species: the brook-trout source slot must not replace native herabuna.

ABI 288 is the current cartridge at
`build/v3-creature-rig-resources-01/rig-runtime/build-lock.json`, ROM SHA-256
`0c06c17001c78c63ef39a615be3458cbe95e3eb023518a48f2257ad430702937`.
The shared importer installs all sixteen animated objects, reusing 74,672 bytes
without recompilation, and extends the room-rig packet from 42 to 58 records.
There are still 167 selectable choices and 100 complete inactive furniture
profiles. Creature profiles remain disabled, and the static ant is prepared only.
Neither the main lock nor either stable V2-13 deployment changes.

The common embedded-rig callback preserves initial half-frame advancement, two
half-frame updates per native tick, complete joint arrays, and opaque/translucent
parent matrices. Fixed additive display reservations do not create standalone
furniture options. Four focused source, sanitized callback, cartridge retention,
UPS, and repeat-planning checks pass. No emulator or hardware result is claimed.
The current 12-KiB bank and format-five saved data are unchanged.

Before enabling profiles, connect the native generic motion path during fade
states: ordinary custom callbacks skip states 6 and 13. The source creature sound
helper schedules timed, randomized triggers, not ordinary furniture sound loops.
The native tables lack all three required donor sound entries; complete sound
programs and table integration remain required alongside carried-parent readers.

## Shared conversion

The ordinary profile reader recognizes native-profile-owned rigs without
inventing item-specific converters. Complete direct models, skeletons, animations,
and speeds pass through the existing artwork and keyframe compilers. Converted
profile descriptors point to their complete skeleton and animation in segment
six. The skeleton binding excludes separate tank/cage lists without dropping
those lists from the object.

Mole cricket, mosquito, and frog share a checked complete movement callback,
with source sound IDs 66, 67, and 65 respectively. Their full callback and
positioning-helper receipts remain explicit dependencies; native playback and
transition-state mapping are not yet installed. No callback is replaced with
a static approximation.

The source parent resolver checks both complete forward/inverse functions and
the fish-index helper. It retains canonical carried IDs and official names,
including the donor's separate display/parent spellings. Thirty-four name
credits live in the single `translations/provenance.json` catalogue. Native
identity correspondence remains separate from merely sharing a numerical ID.

## Evidence and next integration

Three focused `ProfileOwnedResourceTests` pass across targeted invocations:
complete artwork/keyframe comparisons and descriptor relocation; actual parent
mappings/names/sound dependencies; and rejection of damaged source code, invalid
speeds, missing pointers, changed interactions, and extra callbacks. The initial
negative-test fixture failed after removing a relocation without refreshing its
sorted index. Its corrected targeted retry passes. No emulator replay is needed
for this converter-only change, and none is claimed.

The first prepared batch compiled thirteen objects. The second reused thirteen
and compiled the three sound-bearing objects. The combined batch reused sixteen
and compiled the static ant in one container. Complete prepared assets remain
reusable by the ordinary importer.

Connect native parent identities and room rig/audio lifecycle, then the carried
item, price, collection, catch/release, and spawn readers. Do not expose creature
displays as standalone furniture. Metadata and profile writers reject the
prepared-only categories until implementation exists. Ordinary rendering,
gameplay, save/reload with these additions, and hardware remain unverified.
No saved format changes are introduced by this resource preparation.
