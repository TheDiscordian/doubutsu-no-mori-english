#ifndef AF_V3_SURFACE_TRANSFER_H
#define AF_V3_SURFACE_TRANSFER_H
typedef unsigned int u32;
extern int af_surface_dma(void *,u32,u32);
static __attribute__((always_inline)) inline void copy_surface(
        void *target,int index,u32 native,u32 added,u32 stride) {
    if (!target) return;
    u32 slot=(u32)index,base=native;
    if (slot>=68u) {
        slot-=73u;
        if (slot>=5u) return;
        base=added;
    }
    af_surface_dma(target,base+slot*stride,stride);
}
#endif
