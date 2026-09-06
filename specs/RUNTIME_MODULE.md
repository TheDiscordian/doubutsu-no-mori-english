# Resident translation module

## Purpose and status

The resident module provides a fixed, bounded location for English runtime code
and data. Boot, four-MiB heap bounds, and the train-to-town sequence pass in the
isolated emulator. The module remains experimental pending broader gameplay,
save, and hardware checks. Existing choice and font patches remain independently
selectable while module features are developed. The module includes bounded
[English message date/time formatters](ENGLISH_DATES.md).

## Memory contract

The retail `mainproc` calls `SystemHeap_Init(801948E0, 0026B720)` at RAM
`800D6720`. The heap begins immediately after the static buffers segment and
ends at `80400000`. The DMA manager is already running; no system-heap allocation
has occurred. The module reserves the first `4000` hexadecimal bytes (sixteen
KiB), then initialises the original heap at `801988E0`, size `00267720`.

`osMemSize` stays four MiB. The game heap, framebuffers, and dynamic overlays
continue to use the original allocators. Their allocations may move, so overlay
relocation and heap-budget regressions are required. The emergency fault
framebuffer at the top of RAM does not overlap this bottom-of-heap reservation.

| Region | Purpose |
| --- | --- |
| `801948E0..801949DF` | Versioned module header and startup observations |
| `801949E0..80194BCF` | Relocated original watchdog, 496 bytes |
| `80194BE0` onward | Original translation runtime code and data |
| `801988D0..801988DF` | Four-word end guard, outside linked code/data/BSS |
| `801988E0..803FFFFF` | Original system heap, reduced by sixteen KiB |

The linker rejects code, constants, or BSS reaching the guard. The DMA file is
zero-padded to the entire reservation, so BSS starts cleared. Runtime startup
records the old/new heap bounds and guard values for debugger assertions.

## Bootstrap and watchdog preservation

The original watchdog occupies `800D64E0..800D66CF`. Its entry becomes a jump to
the preserved copy at `801949E0`; the bootstrap occupies the rest of its old
space. The original watchdog uses PC-relative internal branches and direct calls
to existing external functions. Copying it preserves branch distances. The
builder checks for internal absolute jumps and external references to its
interior; unsupported relocation forms fail the build.

The heap-initialisation call targets the bootstrap at `800D64F0`. It preserves
the o32 ABI, saves the original heap arguments, verifies the expected heap bounds,
requests the new DMA file, checks its magic/version/reservation, writes back data
cache, invalidates instruction cache,
calls the module's startup function, updates `gSystemHeapSize`, and invokes the
original `SystemHeap_Init` with the reduced region. A startup error stops before
executing an incomplete module or creating an overlapping heap.

The watchdog's normal caller runs only after module startup. Neither the
watchdog nor the fault handler is removed.

## ROM contract

The new uncompressed file uses VROM `02800000..02803FFF`. The retail DMA table
contains 3,374 entries and sixteen zero rows within its loaded allocation.
Adding one entry and preserving the following zero terminator does not enlarge
the table. DMA initialisation counts entries until the terminator.

The builder verifies available zero rows, non-overlapping VROM ranges, file
bounds, source/patch hashes, re-extracted contents, CIC checksums, and UPS
application. Source ROM files are never modified. Module artifacts remain in
ignored build output; the runtime source, linker script, and build tool are
versioned.

## Validation

Required checks include deterministic Docker builds, guarded bootstrap patches,
preserved watchdog control flow, module magic and ready flag, exact heap bounds,
end guards through gameplay, four-MiB operation, normal allocation and overlay
relocation, game saves, and original-hardware execution. Emulator checkpoints
may resume only an identical ROM; cartridge-save compatibility is tested
separately across builds.
