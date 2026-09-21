/* Native catalogue surface setup, preserving its geometry, scale, and pricing. */
#include <stddef.h>
#include "surface_transfer.h"
typedef unsigned short u16;
typedef struct {
    u16 index;
    unsigned char preceding[0x742];
    void *texture;
    u32 profile,offset;
    u16 type,timer;
    u32 price,scale,y;
} SurfacePreview;
#ifdef __mips__
_Static_assert(offsetof(SurfacePreview,texture)==0x744, "Native preview texture moved");
_Static_assert(offsetof(SurfacePreview,price)==0x754, "Native preview price moved");
_Static_assert(offsetof(SurfacePreview,y)==0x75C, "Native preview position moved");
#endif
extern int af_surface_stock(u16,int,int,void *);
extern u32 af_surface_price(u16);

static __attribute__((always_inline)) inline void initialise(SurfacePreview *preview,
        u16 item,u16 base,int kind,u32 native,u32 added,u32 stride) {
    u16 index=(u16)(item-base);
    preview->type=(u16)(6-kind);preview->profile=0;preview->index=index;
    preview->y=0xC2B40000u;preview->scale=0x3F000000u;
    u32 offset=(u32)index*stride,address=native+offset;
    preview->offset=offset;
    if (index>=68u) {
        if ((u32)index-73u>=5u) goto price;
        address=added+offset-73u*stride;
    }
    if (preview->texture) af_surface_dma(preview->texture,address,stride);
price:
    u32 price=0;
    for (int stock=0;stock<3;stock++)
        if (af_surface_stock(item,kind,stock,NULL)) {price=af_surface_price(item);break;}
    preview->price=price;
}
void af_v3_preview_wall(SurfacePreview *preview,int item) {
    initialise(preview,(u16)item,0x2700,4,0x0182A000u,AF_SURFACE_WALL_VROM,0x1020u);
}
void af_v3_preview_floor(SurfacePreview *preview,int item) {
    initialise(preview,(u16)item,0x2600,3,0x017A1000u,AF_SURFACE_FLOOR_VROM,0x2020u);
}
