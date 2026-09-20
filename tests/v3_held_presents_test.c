#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/held_presents.c"
u32 af_test_present_table[8];
static unsigned enabled;
int af_test_present_selected(u32 item) {
    return item>=0x2239u && item<=0x223Cu && (enabled&(1u<<(item-0x2239u))) ? 44 : -1;
}
#undef selected
#define AF_V3_CATEGORY_COUNT 71
#define AF_V3_PRESENT_DECODE 1
#include "../overlays/v3/item_categories.c"
u32 af_test_category_parents[340],af_test_categories[32];
static unsigned original_calls;
int af_test_category_selected(u32 item) {return af_test_present_selected(item);}
int af_test_category_original(u32 item) {(void)item;++original_calls;return 12;}
u32 af_test_present_decode(u32 item) {return af_v3_present_decode(item);}
int main(void) {
    header[0]=0x41465057u;header[1]=1;header[2]=4;header[3]=4;
    Present *rows=(Present *)(header+4);
    for (unsigned i=0;i<4;++i)rows[i]=(Present){0x251Fu+i,0x2239u+i};
    for (enabled=0;enabled<16;++enabled)for (unsigned i=0;i<4;++i) {
        u32 parent=0x2239u+i,wrapped=0x251Fu+i,yes=(enabled>>i)&1u;
        assert(af_v3_present_decode(wrapped)==(yes?parent:0));
        for (unsigned cond=0;cond<4;++cond)
            assert(af_v3_present_encode(parent,cond)==(yes && cond==1?wrapped:parent));
        original_calls=0;
        assert(af_v3_equipment_category(wrapped)==(yes?14:0));
        assert(af_v3_equipment_category(0xFFFF0000u|wrapped)==(yes?14:0));
        assert(!original_calls);
    }
    enabled=15;
    const u32 other[]={0,0x2200,0x2238,0x223D,0x251C,0x251E,0x2523,65535,65536,0xFFFF251F};
    for (unsigned i=0;i<sizeof(other)/sizeof(*other);++i) {
        assert(!af_v3_present_decode(other[i]));
        assert(af_v3_present_encode(other[i],1)==other[i]);
    }
    original_calls=0;assert(af_v3_equipment_category(0x251C)==12);assert(original_calls==1);
    for (unsigned i=0;i<4;++i) {
        u32 old=header[i];header[i]^=1;
        assert(!af_v3_present_decode(0x251F));assert(af_v3_present_encode(0x2239,1)==0x2239);
        header[i]=old;
    }
    rows[0].parent^=1;assert(!af_v3_present_decode(0x251F));rows[0].parent^=1;
    rows[0].wrapped^=1;assert(!af_v3_present_decode(0x251F));
    puts("Wrapped parent/profile/condition/category bounds pass");
}
