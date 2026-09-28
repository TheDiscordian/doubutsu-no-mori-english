#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CLOTHING_BATCH 1
#include "../overlays/v3/clothing_roster.c"
#include "../overlays/v3/clothing_stock.c"
#include "clothing_fixture.h"
#undef profile
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CLOTHING_DISPLAY 1
#define AF_V3_ALOHA_DISPLAY 1
#define AF_V3_BATCH_CLOTHING_DISPLAY 1
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_SPARSE_FURNITURE 1
#include "../overlays/v3/furniture.c"
#undef imports
#undef profiles
#undef indices
#undef owner
#undef dma
#define AF_V3_DISPLAY_ALIASES 1
#include "../overlays/v3/display_roster.c"
#undef profile

struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
struct Import af_v3_display_import,af_v3_red_display_import,af_v3_blue_display_import;
u32 af_v3_furniture_profiles[CAPACITY],af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY],af_v3_display_profile[192];
volatile u32 af_v3_furniture_owner[8];
struct DisplayAliasIndex af_v3_test_alias_index;
u16 af_v3_test_alias_items[1024*16];
static u32 transferred;
int af_v3_item_type(u32 item) {return af_v3_roster_clothing_record(item) ? 12 : 0;}
u32 af_v3_display_clothing_index(u32 item) {return af_v3_all_display_clothing_index(item);}
int af_v3_furniture_test_dma(void *p,u32 vrom,u32 bytes) {
    (void)p;(void)vrom;(void)bytes;assert(0);return 1;
}
void af_v3_display_test_dma(u32 item,u32 bank) {assert(bank==0x80300000);transferred=item;}

u8 af_v3_roster_profile[192],af_stock_month,af_stock_selected;
static float next_random;
static unsigned rng_calls,native_calls;
const void *af_stock_segment(u32 address) {
    for (u32 i=0;i<3;i++)
        if (address==af_v3_batch_stock[i].pointer) return fixture_lists[i];
    assert(0);return 0;
}
float af_stock_random_float(void) {rng_calls++;return next_random;}
int af_stock_native_index(int *index) {native_calls++;*index=77;return 88;}

static int enabled(u32 item) {
    if (item>=0x2400 && item<0x2500) return 1;
    for (u32 i=0;i<8;i++) if (af_v3_batch_clothing[i].item==item)
        return !!(af_v3_roster_profile[160+(item&255)/8]&(1u<<(item&7)));
    return 0;
}

int main(void) {
    memset(af_v3_roster_profile,255,sizeof(af_v3_roster_profile));
    memset(af_v3_display_profile,255,sizeof af_v3_display_profile);
    memset(af_v3_furniture_indices,255,sizeof af_v3_furniture_indices);
    af_v3_furniture_owner[2]=0x80936710;af_v3_furniture_owner[3]=0x8094F610;
    af_v3_furniture_owner[4]=0x80200000;af_v3_furniture_banks[0]=0x80300000;
    for (u32 i=0;i<8;i++) {
        const struct Clothing *r=af_v3_batch_clothing+i;
        u32 display=0x3800+(r->item&255)*4,index=1024+(display-0x3000)/4;
        struct Import *f=i==0 ? &af_v3_display_import : i==1 ? &af_v3_red_display_import :
            i==2 ? &af_v3_blue_display_import : af_v3_furniture_imports+index-1024;
        f->index=index;f->item=display;f->enabled=1;f->profile[16]=AF_V3_CLOTHING_DISPLAY_VTABLE;
        af_v3_furniture_profiles[index]=i<3 ? (u32)(uptr)f+8 : AF_V3_STATIC_IMPORT_RAM+(index-1024)*80+8;
        u16 *alias=af_v3_test_alias_items+(index-1024)*16;
        alias[0]=index;alias[1]=display;alias[14]=r->item;alias[15]=0x17AC;
        for (u32 rotation=0;rotation<4;rotation++) {
            assert(af_v3_furniture_import_profile(index));
            assert(af_v3_furniture_item(index,rotation)==(display|rotation));
            assert(af_v3_display_clothing_index(display|rotation)==r->index);
            transferred=0;
            assert(af_v3_furniture_import_dma(index,display|rotation,0x80300000,0));
            assert(transferred==(display|rotation) && af_v3_furniture_indices[index]==0);
        }
        f->enabled=0;
        assert(!af_v3_furniture_import_dma(index,display,0x80300000,0));
        f->enabled=1;
        assert(af_v3_roster_clothing_record(r->item)==r);
        assert(af_v3_roster_clothing_source(r->index,0)==r->vrom);
        assert(af_v3_roster_clothing_source(r->index,1)==r->vrom+512);
        u8 item[4]={r->item>>8,r->item,0xA5,0x5A};
        assert(af_v3_roster_clothing_index(item)==r->index && item[2]==0xA5 && item[3]==0x5A);
        assert(af_v3_roster_outfit_ready(r->item));
        af_v3_roster_profile[160+(r->item&255)/8]&=~(1u<<(r->item&7));
        assert(!af_v3_roster_clothing_record(r->item));
        assert(!af_v3_roster_clothing_source(r->index,0));
        assert(!af_v3_roster_outfit_ready(r->item));
        assert(!af_v3_roster_clothing_index(item) && item[0]==0x24 && !item[1]);
        af_v3_roster_profile[160+(r->item&255)/8]|=1u<<(r->item&7);
    }
    for (int i=0;i<256;i++) {
        assert(af_v3_roster_clothing_source(i,0)==0xB68000u+(u32)i*512);
        assert(af_v3_roster_clothing_source(i,1)==0xB88000u+(u32)i*32);
        assert(af_v3_roster_outfit_ready(0x2400u+i));
    }
    assert(!af_v3_roster_clothing_source(-1,0));
    assert(!af_v3_roster_clothing_source(256,0));
    assert(!af_v3_roster_clothing_source(0x101A,2));
    assert(!af_v3_roster_clothing_record(0x1341A));
    assert(!af_v3_roster_clothing_index(0));
    /* Actual installed lists, every eligible RNG interval, all months, and
       none/individual/all imported selections share one reader. */
    const u8 by_month[]={0,4,4,1,1,1,2,2,2,3,3,3,4};
    for (u32 selection=0;selection<10;selection++) {
        memset(af_v3_roster_profile,0,sizeof(af_v3_roster_profile));
        for (u32 i=0;i<8;i++) if (selection==9 || selection==i+1) {
            u32 item=af_v3_batch_clothing[i].item;
            af_v3_roster_profile[160+(item&255)/8]|=1u<<(item&7);
        }
        for (af_stock_month=1;af_stock_month<=12;af_stock_month++) for (u32 group=0;group<3;group++) {
            int eligible[256],count=0;u32 offset=0;
            for (u32 s=0;s<5;s++) {
                for (u32 j=0;j<af_v3_batch_stock[group].counts[s];j++,offset++)
                    if ((!s || s==by_month[af_stock_month]) && enabled(fixture_lists[group][offset]))
                        eligible[count++]=(int)offset;
            }
            assert(count>0);
            for (int n=0;n<count;n++) {
                next_random=((float)n+0.25f)/(float)count;rng_calls=native_calls=0;
                int guarded[]={0x1357,-1,0x2468};
                assert(af_v3_clothing_stock_index(guarded+1,fixture_lists[group])==count);
                assert(guarded[1]==eligible[n] && guarded[0]==0x1357 && guarded[2]==0x2468);
                assert(rng_calls==1 && native_calls==0);
                if (fixture_lists[group][guarded[1]]==0x34CB)
                    assert(af_stock_month>=6 && af_stock_month<=8);
            }
        }
    }
    int result=-1;native_calls=rng_calls=0;
    assert(af_v3_clothing_stock_index(&result,0)==88 && result==77 && native_calls==1 && !rng_calls);
    assert(!af_v3_clothing_stock_index(0,0));
    puts("pass: eight garments, mannequin DMA/rotations, selected outfits, all stock groups and seasons");
}
