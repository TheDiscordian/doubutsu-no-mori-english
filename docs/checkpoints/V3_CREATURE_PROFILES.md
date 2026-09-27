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

ABI 287 remains the current cartridge at
`build/v3-builtin-model-profiles-01/profile-runtime/build-lock.json`, with 167
selectable choices and 100 complete inactive furniture profiles. These creature
resources are not installed or selectable. Neither the main lock nor either
stable V2-13 deployment changes.

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
