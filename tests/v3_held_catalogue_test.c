#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_HELD_CATALOGUE 1
#include "../overlays/v3/furniture.c"
#undef profiles
#define AF_V3_CLOTHING_CATALOGUE 1
#define AF_V3_CATALOGUE_RECORDS 1
#include "../overlays/v3/catalogue.c"

struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
u8 *af_catalogue_active, af_catalogue_item_records[1024][32];
u32 af_catalogue_profiles[CAPACITY];
static u8 player[0xBD0], selected[8], collected[8];
static unsigned initializations, native_programs, native_bits, prices;
static int halt_reason;
static jmp_buf halted;

int af_v3_furniture_test_dma(void *p,u32 v,u32 n) {(void)p;(void)v;(void)n;assert(0);return 0;}
u32 af_v3_held_item_collection(u32 item) {
    item &= 0xFFFC;
    if(item<0x314C || item>0x3168) return 0;
    return selected[(item-0x314C)/4] ? item : 0;
}
u32 af_v3_catalogue_item_price(u32 item) {assert(af_v3_held_item_collection(item));++prices;return 600;}
void af_v3_save_halt(int n) {halt_reason=n;longjmp(halted,1);}
int af_v3_catalogue_owned(const u8 *p,u32 item) {
    assert(p==player);u32 canonical=af_v3_held_item_collection(item);
    return canonical && collected[(canonical-0x314C)/4];
}
int af_v3_native_catalogue_bit(const u32 *p,int i) {(void)p;(void)i;++native_bits;return 7;}
void af_v3_original_catalogue_program(struct Preview *p) {(void)p;++native_programs;}
void af_v3_original_catalogue_furniture_init(struct Preview *p,u32 item) {
    (void)item;++initializations;memset(p,0xA5,sizeof *p);
}
int af_v3_native_catalogue_available(u32 item,int category,int list,void *game) {
    (void)item;(void)category;(void)list;(void)game;return 9;
}

int main(void) {
    active=player;
    const u32 *bits=(const u32 *)(player+0xAF0);
    for(unsigned n=0;n<8;++n) {
        u32 item=0x314C+4*n,i=(item-0x3000)/4,index=1024+i;
        struct Import *row=af_v3_furniture_imports+i;
        row->index=index;row->item=item;row->enabled=1;row->pad=1;
        af_v3_furniture_profiles[index]=AF_V3_STATIC_IMPORT_RAM+8+i*80;
        af_catalogue_profiles[index]=af_v3_furniture_profiles[index];
        assert(!af_v3_furniture_import_profile(index));
        selected[n]=1;
        assert(af_v3_furniture_import_profile(index));
        assert(!af_v3_catalogue_bit(bits,index+1024));
        collected[n]=1;assert(af_v3_catalogue_bit(bits,index+1024));
        for(u32 rotation=0;rotation<4;++rotation) {
            struct Preview preview,expected;
            memset(&preview,0x3C,sizeof preview);preview.index=index+1024;
            expected=preview;expected.profile=af_catalogue_profiles[index];
            af_v3_catalogue_program(&preview);assert(!memcmp(&preview,&expected,sizeof preview));
            memset(&expected,0xA5,sizeof expected);expected.model_y=0;expected.scale=1;
            expected.height=36;expected.price=600;
            af_v3_catalogue_furniture_init(&preview,item+rotation);
            assert(!memcmp(&preview,&expected,sizeof preview));
            assert(af_v3_furniture_item(index,rotation)==item+rotation);
        }
        row->pad=2;assert(!af_v3_furniture_import_profile(index));row->pad=1;
        row->enabled=0;assert(!af_v3_furniture_import_profile(index));row->enabled=1;
        selected[n]=0;assert(!af_v3_furniture_import_profile(index));
        assert(!af_v3_catalogue_bit(bits,index+1024));
        struct Preview p,e;memset(&e,0xA5,sizeof e);
        af_v3_catalogue_furniture_init(&p,item);assert(!memcmp(&p,&e,sizeof p));
    }
    assert(prices==32 && initializations==40 && !native_programs && !native_bits);
    /* Ordinary sparse furniture needs no handheld selection. */
    struct Import *row=af_v3_furniture_imports+0x89;
    row->index=1161;row->item=0x3224;row->enabled=1;
    af_v3_furniture_profiles[1161]=AF_V3_STATIC_IMPORT_RAM+8+0x89*80;
    assert(af_v3_furniture_import_profile(1161));
    struct Preview p,e;memset(&e,0xA5,sizeof e);
    af_v3_catalogue_furniture_init(&p,0x1004);assert(!memcmp(&p,&e,sizeof p));
    p.index=946;af_v3_catalogue_program(&p);assert(native_programs==1);
    assert(af_v3_catalogue_bit(bits,946)==7 && native_bits==1);
    assert(!af_v3_catalogue_bit(bits,3072));
    assert(!af_v3_catalogue_bit((const u32 *)(player+4),2131));
    p.index=2131;
    if(!setjmp(halted)){af_v3_catalogue_program(&p);assert(0);}assert(halt_reason==-7);
    if(!setjmp(halted)){af_v3_catalogue_program(0);assert(0);}assert(halt_reason==-1);
    puts("Shared held profiles, selected ownership, framing, prices, native fallbacks, and bounds pass");
}
