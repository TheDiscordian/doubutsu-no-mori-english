/* Keep the native command slot while matching the absent GC placard. */
#include <PR/mbi.h>

const Gfx fishing_remove_placard[] __attribute__((section(".remove"), aligned(8))) = {
    gsSPNoOp(),
};
