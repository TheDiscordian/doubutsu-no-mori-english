#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CATALOGUE_RECORDS 1
#define AF_V3_CATALOGUE_PREVIEW_RECORDS 1
#define AF_V3_CLOTHING_CATALOGUE 1
#define AF_V3_ALOHA_DISPLAY 1
#include "../overlays/v3/catalogue.c"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
u8 *af_catalogue_active;
u32 af_catalogue_profiles[AF_V3_FURNITURE_CAPACITY];
u8 af_catalogue_item_records[1024][32];
struct PreviewFraming af_catalogue_framing[AF_V3_PREVIEW_COUNT];
static int enabled = 1;
int af_v3_catalogue_owned(const u8 *a,u32 b) {(void)a;(void)b;return 0;}
int af_v3_furniture_import_profile(u32 i) {return enabled && i>=1024 && i<2048;}
void af_v3_save_halt(int a) {(void)a;abort();}
int af_v3_native_catalogue_bit(const u32 *a,int b) {(void)a;(void)b;return 0;}
void af_v3_original_catalogue_program(struct Preview *a) {(void)a;}
void af_v3_original_catalogue_furniture_init(struct Preview *a,u32 b) {(void)b;memset(a,0xAA,sizeof(*a));}
int af_v3_native_catalogue_available(u32 a,int b,int c,void *d) {(void)a;(void)b;(void)c;(void)d;return 77;}
int main(void) {
    const int masks[] = {0,7,8,32};
    for (int i=0;i<1024;i++) for (int m=0;m<4;m++) {
        /* Clothing displays retain their separate pocket-stock route. */
        if (display_pocket(0x3000u+(u32)i*4u)) continue;
        af_catalogue_item_records[i][7]=1;
        af_catalogue_item_records[i][24]=(u8)masks[m];
        for (int list=-1;list<8;list++) for (int rotation=0;rotation<4;rotation++) {
            u32 item=0x3000u+(u32)i*4u+(u32)rotation;
            int expected=list>=0 && list<6 && ((masks[m]>>list)&1);
            assert(af_v3_catalogue_available(item,0,list,0)==expected);
            assert(af_v3_catalogue_available(item,1,list,0)==0);
            enabled=0; assert(af_v3_catalogue_available(item,0,list,0)==0); enabled=1;
        }
        af_catalogue_item_records[i][7]=0;
        assert(af_v3_catalogue_available(0x3000u+(u32)i*4u,0,0,0)==0);
    }
    assert(af_v3_catalogue_available(0x1234,0,0,0)==77);
    assert(af_v3_catalogue_available(0x3AFC,0,0,0)==1);
    assert(af_v3_catalogue_available(0x3AFC,1,0,0)==0);
    struct Preview p,expected;
    const u32 item=0x3FFCu;
    af_catalogue_item_records[1023][7]=1;
    for (u32 mode=0;mode<AF_V3_PREVIEW_COUNT;mode++) {
        af_catalogue_framing[mode].scale=(float)(mode+1)/100.0f;
        af_catalogue_framing[mode].model_y=-(float)mode;
        af_catalogue_item_records[1023][26]=(u8)(mode+1);
        memset(&expected,0xAA,sizeof(expected));
        expected.scale=af_catalogue_framing[mode].scale;
        expected.model_y=af_catalogue_framing[mode].model_y;
        af_v3_catalogue_furniture_init(&p,item|3);
        assert(memcmp(&p,&expected,sizeof(p))==0);
    }
    memset(&expected,0xAA,sizeof(expected));
    enabled=0;af_v3_catalogue_furniture_init(&p,item);
    assert(memcmp(&p,&expected,sizeof(p))==0);enabled=1;
    af_catalogue_item_records[1023][7]=0;
    af_v3_catalogue_furniture_init(&p,item);assert(memcmp(&p,&expected,sizeof(p))==0);
    af_catalogue_item_records[1023][7]=1;
    const u8 invalid[]={0,AF_V3_PREVIEW_COUNT+1,255};
    for (u32 i=0;i<sizeof(invalid);i++) {
        af_catalogue_item_records[1023][26]=invalid[i];
        af_v3_catalogue_furniture_init(&p,item);assert(memcmp(&p,&expected,sizeof(p))==0);
    }
    af_v3_catalogue_furniture_init(&p,0x1000);assert(memcmp(&p,&expected,sizeof(p))==0);
    af_v3_catalogue_frame(NULL,item);
    puts("record-driven catalogue categories and bounds pass");
}
