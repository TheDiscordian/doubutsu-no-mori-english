#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CATEGORY_COUNT 71
#include "../overlays/v3/item_categories.c"
u32 af_test_category_parents[340],af_test_categories[32];
static u32 enabled_item,expected_argument;
static int kind=107,original_calls;
int af_test_category_selected(u32 item) {return item==enabled_item?kind:-1;}
int af_test_category_original(u32 item) {
    assert(item==expected_argument);++original_calls;return 12;
}
int main(void) {
    parents[0]=0x41464849u;parents[1]=1;parents[2]=56;parents[3]=24;
    categories[0]=0x41464354u;categories[1]=1;categories[2]=71;categories[3]=53;
    Parent *rows=(Parent *)(parents+4);
    const u8 types[]={19,33,37,38,39,40,41,42,43};
    for (unsigned i=0;i<sizeof(types);++i)((u8 *)(categories+4))[types[i]]=27+types[i];
    for (u32 item=0;item<65536u;++item) {
        original_calls=0;expected_argument=item;
        int extra=item>=0x2224u && item<0x225Cu;
        assert(af_v3_equipment_category(item)==(extra?0:12));
        assert(original_calls==!extra);
    }
    for (unsigned i=0;i<56;++i) {
        enabled_item=0x2224+i;rows[i]=(Parent){enabled_item,600,0x314C,107,43,{0}};
        for (unsigned t=0;t<53;++t) {
            rows[i].source_type=t;
            assert(af_v3_equipment_category(enabled_item)==((u8 *)(categories+4))[t]);
        }
        rows[i].source_type=53;assert(!af_v3_equipment_category(enabled_item));
        rows[i].source_type=255;assert(!af_v3_equipment_category(enabled_item));
        memset(rows+i,0,sizeof(*rows));
    }
    enabled_item=0x225B;rows[55]=(Parent){0x225B,600,0x314C,107,43,{0}};
    assert(af_v3_equipment_category(0x225B)==70);
    assert(af_v3_equipment_category(0xFFFF225B)==70); /* Native u16 identity. */
    kind=106;assert(!af_v3_equipment_category(0x225B));kind=107;
    for (int h=0;h<2;++h)for (int i=0;i<4;++i) {
        u32 *p=h?categories:parents,saved=p[i];p[i]^=1;
        assert(!af_v3_equipment_category(0x225B));p[i]=saved;
    }
    Parent saved=rows[55];
    rows[55].item=0;assert(!af_v3_equipment_category(0x225B));rows[55]=saved;
    rows[55].kind=35;assert(!af_v3_equipment_category(0x225B));rows[55]=saved;
    rows[55].kind=115;assert(!af_v3_equipment_category(0x225B));rows[55]=saved;
    rows[55].display=0x314D;assert(!af_v3_equipment_category(0x225B));rows[55]=saved;
    ((u8 *)(categories+4))[43]=69;assert(!af_v3_equipment_category(0x225B));
    expected_argument=0xFFFF2200;assert(af_v3_equipment_category(expected_argument)==12);
    puts("Shared category bounds, profile selection, and original fallbacks pass");
}
