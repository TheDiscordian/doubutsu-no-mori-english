#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/surface_items.c"
#define AF_SURFACE_ITEMS_VROM 0x02345670u
#define AF_SURFACE_ITEMS_CRC 0x76543210u
#include "../overlays/v3/surface_bootstrap.c"
u32 af_test_surface_items[64],af_test_surface_memory[1024];
static u32 prior_item,prior_capacity;
static unsigned calls,stage;
static int dma_error,crc_error,init_value=1;
int af_surface_prior_name(u8 *target,u32 capacity,u32 item) {
    assert(target);prior_item=item;prior_capacity=capacity;calls++;return 27;
}
int af_surface_prior_type(u32 item) {prior_item=item;calls++;return 28;}
u32 af_surface_prior_price(u32 item) {prior_item=item;calls++;return 29;}
int af_surface_dma(void *target,u32 source,u32 n) {
    assert(stage++==0 && target==af_test_surface_memory && source==AF_SURFACE_ITEMS_VROM && n==4096);
    return dma_error;
}
u32 af_surface_crc(const void *target,u32 n) {
    assert(stage++==1 && target==af_test_surface_memory && n==4096);
    return crc_error ? 0 : AF_SURFACE_ITEMS_CRC;
}
void af_surface_writeback(void *target,u32 n) {assert(stage++==2 && target==af_test_surface_memory && n==4096);}
void af_surface_invalidate(void *target,u32 n) {assert(stage++==3 && target==af_test_surface_memory && n==4096);}
int af_surface_prior_init(void) {assert(stage++==4);return init_value;}
int main(void) {
    u8 buffer[48];SurfaceItem *rows=(SurfaceItem *)(af_test_surface_items+4);
    header[0]=0x41465349;header[1]=1;header[2]=10;header[3]=24;
    for (u32 i=0;i<10;i++) {
        rows[i].item=(u16)(0x2649+i%5+(i/5)*256);rows[i].price=(u16)(800+i);
        memset(rows[i].name,'A'+(int)i,16);
    }
    for (u32 enabled=0;enabled<=2;enabled++) for (u32 i=0;i<10;i++) {
        SurfaceItem *r=rows+i;r->enabled=enabled;memset(buffer,0xA5,sizeof(buffer));calls=0;
        assert(af_v3_surface_item_name(buffer+16,16,r->item)==(enabled==1));
        assert(af_v3_surface_item_type(0xAABB0000u|r->item)==(enabled==1 ? 12 : 0));
        assert(af_v3_surface_item_price(0xAABB0000u|r->item)==(enabled==1 ? r->price : 0));
        for (u32 j=0;j<sizeof(buffer);j++)
            assert(buffer[j]==(enabled==1 && j>=16 && j<32 ? r->name[j-16] : 0xA5));
        assert(!calls);assert(!af_v3_surface_item_name(NULL,16,r->item));
        assert(!af_v3_surface_item_name(buffer,15,r->item));
        r->enabled=1;r->item^=1;assert(!af_v3_surface_item_price(r->item^1));r->item^=1;
    }
    for (u32 kind=0;kind<2;kind++) for (u32 i=64;i<256;i++) {
        if (i>=73 && i<78) continue;
        u32 item=0x2600+256*kind+i;calls=0;
        assert(!af_v3_surface_item_name(buffer,16,item));assert(!af_v3_surface_item_type(item));
        assert(!af_v3_surface_item_price(item));assert(!calls);
    }
    for (u32 k=0;k<4;k++) {header[k]^=1;assert(!af_v3_surface_item_price(0x2649));header[k]^=1;}
    const u32 original[]={0,0x2600,0x263F,0x2700,0x273F,0x3000,0x34BF,0x2200,0xFFFFFFFF,0x12342649};
    for (u32 i=0;i<sizeof(original)/sizeof(*original);i++) {
        u32 item=original[i];calls=0;
        assert(af_v3_surface_item_name(buffer,7,item)==27 && calls==1 && prior_item==item && prior_capacity==7);
        if (item==0x12342649) continue; /* Type/price deliberately use native u16 arguments. */
        assert(af_v3_surface_item_type(item)==28 && calls==2 && prior_item==item);
        assert(af_v3_surface_item_price(item)==29 && calls==3 && prior_item==item);
    }
    stage=0;assert(af_v3_surface_init()==1 && stage==5);
    stage=0;dma_error=1;assert(!af_v3_surface_init() && stage==1);dma_error=0;
    stage=0;crc_error=1;assert(!af_v3_surface_init() && stage==2);crc_error=0;
    stage=0;init_value=0;assert(!af_v3_surface_init() && stage==5);
    puts("surface metadata, disabled IDs, original routing, guards, and checked startup pass");
    return 0;
}
