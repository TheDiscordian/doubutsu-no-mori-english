# V3 shared room effects

## Scope and state

Room effects are part of complete item behaviour. The judge's bell requires its
endpoint-triggered animation, positional bell sound, and, with ringside seating,
a singleton camera sound and the complete camera-flash controller. None of these
dependencies may be dropped to make the item selectable.

`tools/v3_room_effects.py` supplies source-bound effect preparation, complete
sprite packing, native profile packets, and additive controller-table expansion.
`overlays/v3/room_effects.c` implements both flash lifecycles. These components
are prepared and host-checked, not installed in the current ABI-212 cartridge.
The public source branch contains development work; neither web-patcher
deployment changes until user testing and approval.

## Native controller integration

The native controller uses VROM `008E0A30`, relocation resource `008E4170`, and
linked address `80A17190`. Sections are 10,752 bytes of code, 3,312 bytes of data,
80 bytes of read-only data, and 7,632 bytes of zero-initialised state. The native
pool supports 80 active effects, twelve 3,072-byte code slots, and six 3,584-byte
graphics slots. Those capacities remain unchanged.

| Table | Original offset | Row size | Original count |
| --- | ---: | ---: | ---: |
| Overlay descriptors | `2A00` | 20 | 111 |
| Graphics ranges | `32AC` | 8 | 111 |
| Duplicate-suppression flags | `3624` | 1 | 111 |

The shared extension appends identities 111 (flash) and 112 (flash controller).
It preserves all existing rows, active-state addresses, instructions outside the
checked table references/bound, and relocation records. Original BSS becomes
explicit zero-filled initial data at the same offsets. Expanded tables follow
that state. The resulting owner is 25,056 bytes, with 3,280 additional scene
bytes and no additional fixed resident reservation. Installation must update
the actual actor loader's ROM range and allocated size; producing this owner
alone does not install it.

The current owner contains four absolute campsite-lamp profile hooks and four
removed relocations. The extension accepts and preserves that checked variant
as well as the original native owner. Replacing it with the unmodified retail
controller would remove completed lamp behaviour. The existing lamp wrapper
calls original controller functions by unchanged offsets.

The effect profiles contain four absolute callbacks in the shared room packet,
death policy `-2`, no-child value `255`, and the source no-distance-death value.
Each native loader packet is 32 data bytes plus a 32-byte empty relocation
trailer. Linked profile addresses do not reserve additional fixed RAM; the
native effect code pool owns their actual loaded storage. Callbacks must be
linked into the existing `804C8000..804CBFFF` code reservation, loaded before
the first request, and retained for the lifetime of the effects.

## Camera flashes

All eight donor callbacks and both profiles are bound to the supplied GAFE01-r0
REL. Native effect records retain their 88-byte layout. Requests preserve
priority, owning item, position, arguments, native pool allocation, cleanup,
and source duplicate policy. No parallel particle pool or saved field is added.

The controller retains a 240-donor-tick lifetime and an eight-tick spawn period:
30 flashes over 120 native updates. Native rooms map by identity: scene 20 has
width four, scenes 6 and 21 have width six, and scene 22 has width eight. Position
and alternating light flags use the donor formulas and continuous RNG. GameCube
second-floor, basement, and island-cottage scenes have no corresponding native
room and are not fabricated.

Particles retain the five-tick source timer and sample the source scale curve at
two ticks per native update. The callback supplies one decrement; the existing
native controller supplies the other. Alternating flashes register the actual
`27,27,27,255` light and shadow flag with the native lighting owner. Integer light
endpoints round upward to native frames, differing by less than one native frame.
Draw callbacks retain billboard transforms, source scale, white alpha 200, and
the complete donor model. Matrix/command writes are bounded by the translucent
arena and cache-written before GPU consumption.

## Artwork and wall identity

The donor star uses legacy native `FD/F5/F3/F2` commands, not Dolphin `FD/D2`
commands. Its 16×16 IA8 texture is already linear with native channel ordering;
applying the ordinary GX untile conversion would corrupt it. The complete
256-byte texture and 64-byte vertex array match the native resources. The full
donor drawing program is retained separately because it differs in render-state
commands, including source culling and the lack of a primitive-colour override.

The packed sprite is 464 bytes. Appending it with the native eight-byte object
header grows the existing graphics bank by 472 bytes, preserving its complete
original prefix. The appended range is `06016C90..06016E68`; its full model is
`06016DD8`. Both resource pointers are rebased to the shared segment-6 convention.
There is no unused segment-8 dependency in the donor drawing program.

Ringside seating is donor wall 65 (`2741`) and additive native wall 76 (`274C`).
Preparation compares all 8,192 converted pixels with the installed resource,
and checks the persistent registry. Comparing against native wall 65 is wrong.
The conditional effect remains conditional on the wall; it does not require
forcing that optional wall into every bell selection.

## Remaining installation

1. Link the effect callbacks into the shared room packet and regenerate native
   profile packets using their final addresses. Reuse the prepared sprite.
2. Install expanded controller/relocation and graphics resources through the
   existing shared installer, preserving the timed-lamp wrapper and native
   actor-loader binding. Account for 3,280 additional scene bytes and full ROM
   growth; do not overwrite neighbouring virtual resources.
3. Bind the endpoint-hit policy to both complete source sound programs, including
   the system singleton trigger, and the actual full-index wall getter. Enable
   the bell only when all behaviour and ordinary import requirements are met.
4. Run a focused combined native check of the changed integration. Retain passing
   unchanged hit/rolling/material evidence. Host relocation and sanitizer checks
   do not establish native loading, sound synthesis, GPU appearance, ordinary
   room interaction, save/restart, or original-hardware behaviour.
