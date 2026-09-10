# Persistent font Expansion Pak owner

## V1-20 and allocation contract

The RC3 font-edge correction grows the persistent font blob by 15,824 bytes.
The system arena retains that allocation, reducing the later gameplay arena.
The supplied existing town exhausts that arena when the native overlay manager
requests 528 bytes for a relocation table. This is an allocation failure, not
save-format rejection. Keep the bordered glyphs and move the font out of the
ordinary arenas.

Reserve `80450000..80457FFF` exclusively for the persistent font. The first
and last sixteen bytes hold four `AF46C0DE` guard words. The unchanged font
blob loads at `80450010`, with at most `7FE0` bytes before the final guard.
The title reservation ends before `80450000`; the emergency fault framebuffer
starts at `807DA800` on eight-MiB systems. Ordinary arenas and framebuffers
remain below `80400000`. Native diagnostic regions at `80500000` and above
remain separate; diagnostics must explicitly allow this new production owner.

Replace only the resident font-initialiser function at
`8019614C..801963B7`. Bind its complete RC3 module, exact original function,
and exact font blob before installing newly compiled code. Retain its existing
busy flag at `80199F00`, installed pointer at `80199F04`, configuration at
`80194948`, and CRC function at `80195938`. No other resident symbol may move.
The linker rejects code growth beyond the old function and any new data/BSS.

Retain configuration bounds, CRC verification before relocation/execution,
native relocator, D-cache writeback, I-cache invalidation, and re-entry guards.
Do not allocate or free from either ordinary arena. Detect exactly eight MiB
before touching the reservation. On unsupported memory configurations, leave
the font uninstalled and allow the existing title adapter to show its English
Expansion Pak warning and stop the graph thread. No upper-memory access is
allowed on that path.

The same candidate includes the independent name-window ordinary-space marker
correction. All other ROM resources, font pixels/code, gameplay, saved formats,
and transition correction stay intact. Backward save compatibility is preferred,
not mandatory; necessary incompatibilities require an explicit handoff warning.
An unintended allocation crash remains a stability defect.

## Focused verification

Check configuration rejection, absent-memory no-write behaviour, CRC/DMA/entry
failures, call order, repeated initialisation, and guard preservation with host
sanitisers. Bind all unchanged resources and reconstruct the full UPS. Independently
relocate the complete retained font at its exact upper-memory address.

Cold-boot the supplied save on the corrected candidate and inspect the faulted
thread, loaded player, heap links/free space, complete loaded font/guards, and
module guard. A running emulator process is not proof that the game avoided a
fault. Record normal save/restart separately from initial loading. Reuse existing
font pixel/drawing evidence without claiming an unchanged execution address was
freshly tested. Hardware acceptance remains the human playtest.
