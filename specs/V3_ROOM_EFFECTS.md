# V3 shared room effects

## Scope and state

Room effects are part of complete item behaviour. The judge's bell requires its
endpoint-triggered animation, positional bell sound, and, with ringside seating,
a singleton camera sound and the complete camera-flash controller. None of these
dependencies may be dropped to make the item selectable.

`tools/v3_room_effects.py` supplies source-bound effect preparation and installation,
complete sprite packing, native profile packets, and additive controller-table
expansion. `overlays/v3/room_effects.c` implements both flash lifecycles. These
components are installed in ABI 213 at `build/v3-room-effects-runtime-02/`.
The native loader/profile integration has focused passing evidence. Complete
native particle lifetime and furniture binding remain incomplete; the bell is
not selectable. Host checks cover the complete particle/controller lifecycles.
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
checked table references/bound and profile-loader call. Original BSS becomes
explicit zero-filled initial data at the same offsets. A 384-byte relocated
loader and the expanded tables follow that state. The installed owner is 25,440
bytes, with 3,664 additional scene bytes and no additional fixed resident
reservation. The actor descriptor at `801010B0` points to the complete owner
at VROM `03FA0000` and its actual RAM size; the relocation resource is
`03FB0000`. Their DMA entries retain native directory adjacency. Original
relocations remain, with six added relocations for the new loader and its hook.

The current owner contains four absolute campsite-lamp profile hooks and four
removed relocations. The extension accepts and preserves that checked variant
as well as the original native owner. Replacing it with the unmodified retail
controller would remove completed lamp behaviour. The existing lamp wrapper
calls original controller functions by unchanged offsets.

The effect profiles contain four absolute callbacks in the shared room packet,
death policy `-2`, no-child value `255`, and the source no-distance-death value.
Each native profile packet is 32 data bytes plus a 32-byte empty relocation
trailer. The first 24 bytes are the native profile; the remaining data words
hold its CRC32 and `AFEP` marker. Linked profile addresses do not reserve
additional fixed RAM; the native effect code pool owns actual loaded storage.
Callbacks live in the existing `804C8000..804CBFFF` code reservation, loaded
before the first request, and retained for the lifetime of the effects.

The native `ovlmgr_Load` ignores the supplied VROM end and derives resource and
relocation ranges from neighbouring DMA-directory entries. It cannot load
these tiny subresources within the import file. The controller's loader hook
therefore preserves ordinary `ovlmgr_Load` for every original effect, while
imported profiles use bounded native DMA, CRC/marker verification, callback
range checks, and the existing room-packet loader. Invalid profiles fault before
the native caller can publish them. No additional DMA-directory entry is used.

The equipment word at `804B1E08` points to the current room bootstrap loader;
it is regenerated with every shared compilation. The same publication step
rewrites and checks all effect-profile callbacks and checksums, so subsequent
item categories cannot retain stale function addresses. Bootstrap code uses
1,509 of 1,536 bytes; shared room code uses 5,956 of 16,384 bytes.

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

## Remaining integration

1. Bind the endpoint-hit policy to both complete source sound programs, including
   the system singleton trigger, and the actual full-index wall getter. Enable
   the bell only when all behaviour and ordinary import requirements are met.
2. Include the remaining particle lifetime in the next meaningful combined
   native integration check. The existing fixture now recognises nonzero active
   priorities, rather than requiring a boolean `1`; that corrected continuation
   is not yet executed. Preserve passing controller/profile loading, relocation,
   native program caching, complete original-program loading, and shared-packet
   evidence. Do not repeat unchanged hit/rolling/material tests.

Host sanitizer checks and the partial native run do not establish complete
native particle lifetime, sound synthesis, GPU appearance, ordinary room
interaction, save/restart, or original-hardware behaviour.
