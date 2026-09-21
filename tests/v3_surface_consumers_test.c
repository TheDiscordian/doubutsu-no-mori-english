#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#define AF_SURFACE_FLOOR_VROM 0x0262C4A0u
#define AF_SURFACE_WALL_VROM 0x02636540u
#include "../overlays/v3/surface_single.c"
#include "../overlays/v3/surface_preview.c"

static unsigned char storage[0x2040];
static u32 address,size;
static unsigned transfers,queries,prices;
static int eligible,expected_kind;
static u16 expected_item;
int af_surface_dma(void *target,u32 vrom,u32 bytes) {
    assert(target==storage+16 && vrom==address && bytes==size);
    memset(target,0xC7,bytes);transfers++;return 0;
}
int af_surface_stock(u16 item,int kind,int stock,void *unused) {
    assert(item==expected_item && kind==expected_kind && stock==(int)queries && !unused);
    queries++;return stock==eligible;
}
u32 af_surface_price(u16 item) {assert(item==expected_item);prices++;return 1984;}
static void check_texture(int valid) {
    assert(transfers==(unsigned)valid);
    for (unsigned i=0;i<sizeof(storage);i++)
        assert(storage[i]==(valid && i>=16 && i<16+size ? 0xC7 : 0xA5));
}
int main(void) {
    const int indices[]={0,26,63,64,67,68,72,73,74,77,78,255,INT_MIN,INT_MAX,-1};
    for (unsigned wall=0;wall<2;wall++) {
        void (*single)(void *,int)=wall ? af_v3_single_wall : af_v3_single_floor;
        void (*preview)(SurfacePreview *,int)=wall ? af_v3_preview_wall : af_v3_preview_floor;
        size=wall ? 0x1020u : 0x2020u;
        for (unsigned n=0;n<sizeof(indices)/sizeof(indices[0]);n++) {
            int index=indices[n];int valid=(u32)index<68 || (u32)index-73u<5u;
            address=(u32)index<68 ? (wall ? 0x0182A000u : 0x017A1000u)+(u32)index*size
                : (wall ? AF_SURFACE_WALL_VROM : AF_SURFACE_FLOOR_VROM)+((u32)index-73u)*size;
            memset(storage,0xA5,sizeof(storage));transfers=0;single(storage+16,index);check_texture(valid);
            transfers=0;single(NULL,index);assert(!transfers);
            if (index<0 || index>255) continue;
            for (eligible=-1;eligible<3;eligible++) {
                SurfacePreview p;memset(&p,0x6A,sizeof(p));p.texture=storage+16;
                SurfacePreview expected=p;
                expected_kind=wall ? 4 : 3;expected_item=(u16)((wall ? 0x2700 : 0x2600)+index);
                expected.index=(u16)index;expected.profile=0;expected.type=wall ? 2 : 3;
                expected.offset=(u32)index*size;expected.scale=0x3F000000u;expected.y=0xC2B40000u;
                expected.price=eligible<0 ? 0 : 1984;
                transfers=queries=prices=0;memset(storage,0xA5,sizeof(storage));
                preview(&p,0x34560000u|expected_item);
                assert(!memcmp(&p,&expected,sizeof(p)));check_texture(valid);
                assert(queries==(eligible<0 ? 3u : (unsigned)eligible+1));assert(prices==(unsigned)(eligible>=0));
            }
        }
    }
    puts("single-buffer routing and full preview fields, price queries, missing IDs, and guards pass");
    return 0;
}
