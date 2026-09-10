# Animated English title runtime

## Scope and ownership

The separate v1 preview uses all three supplied GameCube English skeletons,
their 121-frame animations, and the complete losslessly converted artwork.
It leaves the handed-off v0 ROM, resident translation module, and save layout
unchanged. The English-first native keyboard remains installed; the GameCube
grid is separate pending work.

The appended title overlay contains 292,320 bytes, including the 280,224-byte
asset package and 1,984 bytes of new executable code. The original 9,952-byte
prefix retains its destructor, update/draw callbacks, start/save/menu logic,
copyright fade, and native Press Start renderer. Guarded call-site replacements
select the new animation, main-logo drawing, and trademark adapters. Five old
Japanese piece calls become NOPs, retaining their harmless argument delay slots.
The constructor wrapper calls the original constructor before preparing the
three English skeletons.

The actor instance grows from `0328` to `07B0` bytes. Its 1,152-byte extension at
offset `0330` owns three native-compatible skeleton controllers, work/morph
arrays, completion state, and an end guard. The original separately allocated
title texture bank supplies the English Press Start tiles.

## Expansion Pak contract

This preview requires eight MiB. It does not enlarge the native game heap:
the existing fixed `80400000` heap ceiling, bootstrap arguments, resident
reservation, framebuffer allocation, and ordinary allocators are unchanged.
Existing wider-name and letter allocation checks retain their four-MiB bounds.

The title alone owns `80400010..804475EF`; sixteen-byte `AF54C0DE` guards precede
and follow it. The reservation must end below `80450000`, away from the emergency
fault framebuffer at the top of detected RAM. No other feature can borrow this
region while the title owns it.

A 108-byte allocation adapter occupies verified zero space at
`800D6600..800D666B`, beyond the existing text-loader bootstrap epilogue. The
native call at `80057A10` selects it. All actor metadata except the exact title
entry at `801021F0` tail-call the unchanged native allocator. The title entry
receives its fixed address only when the detected RAM size is exactly eight
MiB. Its native absolute-allocation flag makes release clear the loaded pointer
without passing Expansion Pak memory to the ordinary scene allocator. A future
title creation reloads and relocates the complete image through the native DMA
and overlay loaders. Transition/re-entry acceptance must verify that lifetime.

The boot store at `80025D08` no longer overwrites IPL3's detected RAM size with
four MiB. Both the fixed physical startup image and the DMA-listed boot image
contain this change, with recomputed N64 checksums. Changing only a replacement
DMA entry cannot change the code initially executed by IPL3.

Without an Expansion Pak, the adapter refuses the title allocation and performs
no upper-memory writes. A clear missing-Pak user interface is still required
before a v1 handoff; an absent title is not an acceptable final warning.

## Animation and graphics

CPU and RSP segment eleven map the title-owned asset package only during the
relevant work, restoring the previous mapping afterwards. Native keyframe
functions consume the verified compatible source layouts. At the native
30-Hz update rate the animations advance one source frame per update; the
background fade advances forty opacity units, capped at 220. START completes
the animation and releases the original six completion flags and copyright fade.

The main logo reserves nineteen frame-owned matrices: one background matrix
and eighteen shown joints. The trademark reserves one more. Allocation aligns
the graphics tail down to sixteen bytes and includes that padding in the bounds
check; a valid eight-byte-aligned native tail must not be rejected. Matrices and
command reservations cannot cross their respective arena heads/tails.

The existing font matrix frames the GameCube translations and scales. Native
joint drawing writes the main logo into the font command stream temporarily,
then restores the opaque-stream pointer. The 107 texture strips keep every
load inside TMEM while preserving source dimensions, colours, cropped UVs,
shared boundaries, and animation geometry. Actual visual approval is separate
from valid commands and successful animation execution.

## Build and verification

`tools/build_title_overlay.py` cross-compiles the original adapter and emits a
complete source-bound overlay and native relocation file. `tools/title_overlay.py`
installs them into a separate ROM/UPS, verifies retention of all v0 resources,
checks the two boot copies, and reconstructs the output from the UPS.
The moved title/relocation DMA rows remain adjacent at `03C00000` and `03C50000`.

The shared relocation model still defaults to four-MiB addresses. Only callers
explicitly declaring `memory_end=80800000` can validate a high-memory overlay;
the title observer additionally requires its exact fixed reservation address.
The silent emulator runner enables eight MiB only with `--expansion-pak` and
records that configuration. The title scenario independently reads detected
RAM, complete relocated code/assets, animation state, native completion flags,
joint work bounds, and memory guards before testing START.

See the [checkpoint](../docs/checkpoints/TITLE_LOGO.md) for actual build hashes,
test outcomes, unresolved checks, and the next action. Neither a host check nor
a silent native execution pass establishes visual or original-hardware approval.
