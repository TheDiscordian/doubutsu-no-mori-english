#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CATEGORY_COUNT 71
#include "../overlays/v3/ground_categories.c"
Ground af_test_ground_config[4];
u8 af_test_ground_mapping[53], *af_test_ground_owners[4];
u32 af_test_ground_materials[71], af_test_ground_geometry[71];
static u32 storage[4][0x1000], calls;
void af_test_ground_constructor(void *actor, void *game, u32 variant) {
    assert(actor==(void *)1 && game==(void *)2 && variant<4); ++calls;
}
int main(void) {
    const u8 sources[]={19,33,37,38,39,40,41,42,43};
    for (u32 i=0;i<sizeof(sources);i++) {
        u32 category=27+sources[i];mapping[sources[i]]=category;
        materials[category]=0x4AA600+816*i+608;
        geometry[category]=0x4AA600+816*i+792;
    }
    assert(!af_v3_ground_prepare(4));assert(!af_v3_ground_prepare(0));
    for (u32 variant=0;variant<4;variant++) {
        u32 native=variant==1?63:64,total=native+44;
        Ground *r=config+variant;
        *r=(Ground){0,0,16,native,total,0x400,0x400+total*8+32,0x300,native-27};
        u8 *owner=(u8 *)storage[variant];af_test_ground_owners[variant]=owner;
        memset(owner,0xA5,sizeof(storage[variant]));
        u32 *old=(u32 *)(owner+16);
        for (u32 i=0;i<native*2;i++) old[i]=i+0x12340000;
        assert(af_v3_ground_prepare(variant)==owner);
        u32 *table=(u32 *)(owner+r->table),*part=(u32 *)(owner+r->parts);
        assert(!memcmp(table,old,native*8));
        for (u32 i=native;i<total;i++) {
            u32 match=0;
            for (u32 s=0;s<sizeof(sources);s++) match|=i==r->type_base+27+sources[s];
            assert(table[i*2]!=0);
            if (!match) assert(table[i*2]==(u32)(uptr)(owner+r->parts-32));
            assert(table[i*2+1]==(match?0x00010000u:0));
        }
        for (u32 i=0;i<8;i++) assert(!((u32 *)(owner+r->parts-32))[i]);
        for (u32 i=0;i<sizeof(sources);i++,part+=13) {
            u32 category=27+sources[i];
            assert(table[(r->type_base+category)*2]==(u32)(uptr)part);
            assert(part[0]==(u32)(uptr)(part+8) && part[1]==1 && part[2]==(u32)(uptr)(part+12));
            for (u32 j=3;j<8;j++) assert(!part[j]);
            assert(part[8]==materials[category] && part[9]==geometry[category]);
            assert(part[10]==(u32)(uptr)(owner+r->loop) && part[11]==0x00010000u);
            assert(part[12]==(u32)(uptr)(part+10));
        }
        assert(storage[variant][0]==0xA5A5A5A5 && part[0]==0xA5A5A5A5);
        /* A reloaded owner rebuilds pointers from its new address. */
        u32 moved[0x1000];memcpy(moved,storage[variant],sizeof(moved));
        af_test_ground_owners[variant]=(u8 *)moved;
        assert(af_v3_ground_prepare(variant)==(u8 *)moved);
        assert(*(u32 *)((u8 *)moved+r->parts)==(u32)(uptr)((u8 *)moved+r->parts+32));
        af_test_ground_owners[variant]=owner;
    }
    af_v3_ground_cherry((void *)1,(void *)2);af_v3_ground_winter((void *)1,(void *)2);
    af_v3_ground_xmas((void *)1,(void *)2);af_v3_ground_ordinary((void *)1,(void *)2);
    assert(calls==4);
    puts("All seasonal tables, complete parts, relocated ownership, and bounds pass");
}
