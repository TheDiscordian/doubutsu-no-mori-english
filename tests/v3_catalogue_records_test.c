#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CATALOGUE_RECORDS 1
#include "../overlays/v3/catalogue.c"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
u8 *af_catalogue_active;
u32 af_catalogue_profiles[AF_V3_FURNITURE_CAPACITY];
u8 af_catalogue_item_records[1024][32];
static int enabled = 1;
int af_v3_catalogue_owned(const u8 *a,u32 b) {(void)a;(void)b;return 0;}
int af_v3_furniture_import_profile(u32 i) {return enabled && i>=1024 && i<2048;}
void af_v3_save_halt(int a) {(void)a;abort();}
int af_v3_native_catalogue_bit(const u32 *a,int b) {(void)a;(void)b;return 0;}
void af_v3_original_catalogue_program(struct Preview *a) {(void)a;}
int af_v3_native_catalogue_available(u32 a,int b,int c,void *d) {(void)a;(void)b;(void)c;(void)d;return 77;}
int main(void) {
    const int masks[] = {0,7,8,32};
    for (int i=0;i<1024;i++) for (int m=0;m<4;m++) {
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
    puts("record-driven catalogue categories and bounds pass");
}
