/* Original translation runtime. Retail code and assets are supplied at build time. */
typedef unsigned int u32;

#define MODULE_RAM 0x801948E0u
#define RESERVATION 0x4000u
#define GUARD_VALUE 0xAF16C0DEu

struct ModuleHeader {
    u32 magic, abi, reserved_bytes, linked_bytes;
    u32 ready, original_heap, original_size, heap, heap_size, initializations;
};

__attribute__((section(".text.af_runtime_init")))
void af_runtime_init(u32 original_heap, u32 original_size) {
    volatile struct ModuleHeader *header = (void *)MODULE_RAM;
    volatile u32 *guard = (void *)(MODULE_RAM + RESERVATION - 16);
    unsigned int i;

    header->original_heap = original_heap;
    header->original_size = original_size;
    header->heap = original_heap + RESERVATION;
    header->heap_size = original_size - RESERVATION;
    for (i = 0; i < 4; ++i) {
        guard[i] = GUARD_VALUE;
    }
    header->initializations += 1;
    header->ready = 1;
}
