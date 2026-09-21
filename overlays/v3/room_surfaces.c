/* Shared room/shop double-buffer surface reads. No saved fields or allocation. */
#include <stddef.h>
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct {
    u8 preceding[0x180];
    void *floor[2];
    void *wall[2];
} SurfaceRoom;
#ifdef __mips__
_Static_assert(offsetof(SurfaceRoom, floor)==0x180, "Native floor buffers moved");
_Static_assert(offsetof(SurfaceRoom, wall)==0x188, "Native wall buffers moved");
#endif
extern int af_surface_dma(void *,u32,u32);

static __attribute__((always_inline)) inline void copy_surface(
        void **buffers,short index,short bank,u32 native,u32 added,u32 stride) {
    u32 address;
    if ((unsigned short)index<68u) address=native+(u32)index*stride;
    else if ((unsigned short)(index-73)<5u) address=added+(u32)(index-73)*stride;
    else return; /* Never address another DMA owner for a missing surface. */
    if ((unsigned short)bank>2u) return;
    unsigned first=bank==2 ? 0u : (unsigned short)bank;
    unsigned end=bank==2 ? 2u : first+1u;
    for (unsigned i=first;i<end;i++)
        if (buffers[i]) af_surface_dma(buffers[i],address,stride);
}

void af_v3_surface_floor(SurfaceRoom *room,int index,int bank) {
    /* Retail entry points narrow both argument registers themselves. */
    if (room) copy_surface(room->floor,(short)index,(short)bank,0x017A1000u,AF_SURFACE_FLOOR_VROM,0x2020u);
}
void af_v3_surface_wall(SurfaceRoom *room,int index,int bank) {
    if (room) copy_surface(room->wall,(short)index,(short)bank,0x0182A000u,AF_SURFACE_WALL_VROM,0x1020u);
}
