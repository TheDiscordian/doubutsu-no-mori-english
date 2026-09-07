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
has occurred. The module reserves the first `8000` hexadecimal bytes (32 KiB),
then initialises the original heap at `8019C8E0`, size `00263720`. The linker
allows at most `6000` bytes for code/data/BSS, leaving a separate 8 KiB native-test
area. `tools/runtime_layout.py` shares these bounds among host-side consumers.

`osMemSize` stays four MiB. The game heap, framebuffers, and dynamic overlays
continue to use the original allocators. Their allocations may move, so overlay
relocation and heap-budget regressions are required. The emergency fault
framebuffer at the top of RAM does not overlap this bottom-of-heap reservation.

| Region | Purpose |
| --- | --- |
| `801948E0..801949DF` | Versioned module header and startup observations |
| `801949E0..80194BCF` | Relocated original watchdog, 496 bytes |
| `80194BE0..8019A8DF` | Original translation runtime code and data, ending at its linked bound |
| `8019A8E0..8019C8CF` | Zero-initialized isolated native-test area, outside linked code/data/BSS |
| `8019C8D0..8019C8DF` | Four-word `AF32C0DE` end guard |
| `8019C8E0..803FFFFF` | Original system heap, reduced by 32 KiB |

The linker rejects code, constants, or BSS entering the test area. The DMA file is
zero-padded to the entire reservation, so BSS starts cleared. Runtime startup
records the old/new heap bounds and guard values for debugger assertions.
Its header also describes the linked twenty-byte choice capacity and thirty-two
byte row stride. Choice storage is part of the linked BSS, not a second heap
reservation. See [choice storage](ENGLISH_RUNTIME.md) for the complete contract.

Optional resource configuration words at header byte offsets `38`, `3C`, and
`40` hexadecimal enable the sixteen-byte item names, eight-byte display names,
and ten-byte default catchphrases respectively. Each accepts only its designated
VROM and a separately verified DMA resource. Resources are installed in that
order; test-module verification normalizes only these known configuration words.

## Bootstrap and watchdog preservation

The original watchdog occupies `800D64E0..800D66CF`. Its entry becomes a jump to
the preserved copy at `801949E0`; the bootstrap occupies the rest of its old
space. The original watchdog uses PC-relative internal branches and direct calls
to existing external functions. Copying it preserves branch distances. The
builder checks for internal absolute jumps and external references to its
interior; unsupported relocation forms fail the build.

Reference checks scan aligned literal function pointers in every DMA file.
Instruction decoding uses only executable subsegments from the pinned Splat
definitions, not entire containers labelled `type: code`. Embedded graphics,
rodata, library data sections, and relocation files are not CPU instructions.
Unknown definition forms/types fail closed. Synthetic mutation tests ensure real
calls and literal data pointers into replaced functions still fail the audit.

The heap-initialisation call targets the bootstrap at `800D64F0`. It preserves
the o32 ABI, saves the original heap arguments, verifies the expected heap bounds,
requests the new DMA file, checks its magic/version/reservation, writes back data
cache, invalidates instruction cache,
calls the module's startup function, updates `gSystemHeapSize`, and invokes the
original `SystemHeap_Init` with the reduced region. A startup error stops before
executing an incomplete module or creating an overlapping heap.

The 32 KiB size is loaded with `ori`, not a signed `addiu` immediate. Heap
adjustments use explicit unsigned-sized register addition/subtraction. The
assembled instruction tests cover both DMA/cache lengths and heap arithmetic;
runtime assertions check the recorded bounds, `gSystemHeapSize`, and the actual
malloc arena's start pointer independently.

The watchdog's normal caller runs only after module startup. Neither the
watchdog nor the fault handler is removed.

## ROM contract

The new uncompressed file uses VROM `02800000..02807FFF`. The retail DMA table
contains 3,374 entries and sixteen zero rows within its loaded allocation.
Adding one entry and preserving the following zero terminator does not enlarge
the table. DMA initialisation counts entries until the terminator.

The builder verifies available zero rows, non-overlapping VROM ranges, file
bounds, source/patch hashes, re-extracted contents, CIC checksums, and UPS
application. Source ROM files are never modified. Module artifacts remain in
ignored build output; the runtime source, linker script, and build tool are
versioned.

The source inventory and compiler input list include nested C files and headers,
including `runtime/mail/`. Source changes during compilation reject the build.
The linked mail codec and full-letter assembler are callable APIs only: linking
them does not install native mail creation/viewer/save hooks or enable wider
mail-bank candidates.

## Validation

Required checks include deterministic Docker builds, guarded bootstrap patches,
preserved watchdog control flow, module magic and ready flag, exact heap bounds,
end guards through gameplay, four-MiB operation, normal allocation and overlay
relocation, game saves, and original-hardware execution. Emulator checkpoints
may resume only an identical ROM; cartridge-save compatibility is tested
separately across builds.
