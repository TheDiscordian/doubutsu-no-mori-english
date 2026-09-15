#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CLOTHING_DISPLAY 1
#define AF_V3_ALOHA_DISPLAY 1
#include "../overlays/v3/furniture.c"
/* Avoid the furniture translation unit's local macros in the next source. */
#undef profiles
#undef indices
#undef owner
#undef imports
#undef dma
#include "../overlays/v3/display_roster.c"
#undef profile
#include "../overlays/v3/display_items.c"
#include "../overlays/v3/display_conversion.c"

struct Import af_v3_furniture_imports[2],af_v3_display_import;
struct Import af_v3_red_display_import,af_v3_blue_display_import;
u32 af_v3_furniture_profiles[CAPACITY],af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY],af_v3_display_profile[192];
volatile u32 af_v3_furniture_owner[8];
static u32 transferred,last_item;
static int transfers;

u32 af_v3_display_clothing_index(u32 item) { return af_v3_all_display_clothing_index(item); }
int af_v3_item_type(u32 item) { return af_v3_display_item_type(item); }
int af_v3_base_item_type(u32 item) {
    item=(u16)item;
    if (item!=0x34BF && item!=0x341A && item!=0x341B) return 0;
    u32 index=item&255;
    return af_v3_display_profile[160+index/8]&(1u<<(index&7)) ? 12 : 0;
}
int af_v3_base_item_name(u8 *out,u32 size,u32 item) {
    last_item=item;
    if (!out || size<16 || !af_v3_base_item_type(item) || item>65535) return 0;
    memcpy(out,item==0x34BF ? "cherry shirt    " : item==0x341A ? "red aloha shirt " : "blue aloha shirt",16);
    return 1;
}
u32 af_v3_base_item_price(u32 item) { last_item=item;return item==0x34BF ? 380 : 0; }
int af_v3_base_item_place(u32 item,int x,int z,void *out) {
    last_item=item;assert(x==2 && z==3 && out);return (item&0xFFFC)==0x17AC ? 0 : 3;
}
void af_v3_prior_catalogue_record(u32 item) { last_item=item; }
int af_v3_prior_catalogue_owned(const u8 *player,u32 item) {
    assert(player);last_item=item;return af_v3_base_item_type(item)==12;
}
u16 af_v3_prior_display_item(u32 item) {
    item=(u16)item;
    return item>=0x2400 && item<0x2500 ? (u16)(0x17AC+(item-0x2400)*4) : (u16)item;
}
u16 af_v3_prior_pocket_item(u32 item) {
    item=(u16)item;
    return item>=0x17AC && item<0x1BA8 ? (u16)(0x2400+((item-0x17AC)>>2)) : (u16)item;
}
int af_v3_furniture_test_dma(void *p,u32 address,u32 size) {
    (void)p;(void)address;(void)size;assert(0);return 1;
}
void af_v3_display_test_dma(u32 item,u32 bank) {
    assert(bank==0x80300000);transferred=item;++transfers;
}

int main(void) {
    struct Import *rows[]={&af_v3_display_import,&af_v3_red_display_import,&af_v3_blue_display_import};
    const u32 ids[]={0x3AFC,0x3868,0x386C}, clothes[]={0x34BF,0x341A,0x341B}, index[]={1727,1562,1563};
    u8 text[18],player[16]={0};memset(text,0xA5,sizeof text);
    memset(af_v3_furniture_indices,255,sizeof af_v3_furniture_indices);
    af_v3_display_profile[99]=af_v3_display_profile[163]=12;
    af_v3_display_profile[119]=af_v3_display_profile[183]=128;
    af_v3_furniture_owner[2]=0x80936710;af_v3_furniture_owner[3]=0x8094F610;
    af_v3_furniture_owner[4]=0x80200000;af_v3_furniture_banks[0]=0x80300000;
    for (unsigned n=0;n<3;++n) {
        struct Import *row=rows[n];row->index=index[n];row->item=ids[n];row->enabled=1;
        row->profile[16]=AF_V3_CLOTHING_DISPLAY_VTABLE;
        af_v3_furniture_profiles[index[n]]=(u32)(uintptr_t)row+8;
        assert(af_v3_furniture_import_profile(index[n]));
        assert(af_v3_room_display_item(clothes[n])==ids[n]);
        for (u32 rotation=0;rotation<4;++rotation) {
            u32 item=ids[n]|rotation;
            assert(af_v3_display_clothing_index(item)==0x1000+(clothes[n]&255));
            assert(af_v3_display_pocket_item(item)==clothes[n]);
            assert(af_v3_room_pocket_item(item)==clothes[n]);
            assert(af_v3_display_item_type(item)==10);
            assert(af_v3_display_item_type(clothes[n])==12);
            assert(af_v3_display_item_name(text+1,16,item));
            assert(last_item==clothes[n] && text[0]==0xA5 && text[17]==0xA5);
            assert(af_v3_display_item_price(item)==(n==0 ? 380u : 0u));
            assert(af_v3_display_item_place(item,2,3,text)==0 && last_item==(0x17AC|rotation));
            af_v3_display_catalogue_record(item);assert(last_item==clothes[n]);
            assert(af_v3_display_catalogue_owned(player,item) && last_item==clothes[n]);
            assert(af_v3_furniture_item(index[n],rotation)==item);
            assert(af_v3_furniture_import_dma(index[n],item,0x80300000,0) && transferred==item);
        }
    }
    assert(transfers==12);
    assert(af_v3_display_clothing_index(0x1BA7)==254);
    assert(af_v3_room_display_item(0x2400)==0x17AC);
    assert(af_v3_room_pocket_item(0x1AA8)==0x24BF);
    assert(af_v3_display_pocket_item(0x13868)==0x13868);
    assert(!af_v3_display_item_name(text+1,16,0x13868));
    for (int p=0;p<2;++p) {
        unsigned offset=p ? 163 : 99;af_v3_display_profile[offset]&=~4u;
        assert(!af_v3_furniture_import_profile(1562));
        assert(af_v3_furniture_import_profile(1563) && af_v3_furniture_import_profile(1727));
        assert(af_v3_room_display_item(0x341A)==0x341A);
        assert(af_v3_room_pocket_item(0x3868)==0x3868);
        assert(!af_v3_furniture_import_dma(1562,0x3868,0x80300000,0));
        af_v3_display_profile[offset]|=4;
    }
    struct Import saved=af_v3_red_display_import;
    for (int bad=0;bad<4;++bad) {
        if (bad==0) af_v3_red_display_import.enabled=2;
        if (bad==1) af_v3_red_display_import.item=0x386C;
        if (bad==2) af_v3_red_display_import.index=1563;
        if (bad==3) af_v3_red_display_import.profile[16]=0;
        assert(!af_v3_furniture_import_profile(1562));
        af_v3_red_display_import=saved;
    }
    assert(!af_v3_furniture_import_dma(1562,0x3868,0x80300008,0));
    assert(!af_v3_furniture_import_profile(2051));assert(transfers==12);
    puts("all three mannequins, four rotations, canonical metadata/ownership, and dependency rejection pass");
    return 0;
}
