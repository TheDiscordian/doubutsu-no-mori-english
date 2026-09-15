#include "../overlays/v3/furniture_behaviours.c"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
struct Item af_test_furniture_records[1024];
int af_test_furniture_sounds[4] = {0x41F,0x422,0x420,0x423};
static int enabled=1,called_index,called_mode;
int af_v3_furniture_import_profile(u32 i) {return enabled && i>=1024 && i<2048;}
int af_v3_native_action_sound(int i,int mode) {called_index=i;called_mode=mode;return 99;}
int main(void) {
    for (int i=0;i<947;i++) {
        assert(af_v3_furniture_action_sound(i,INT_MIN)==99);
        assert(called_index==i && called_mode==INT_MIN);
    }
    const int invalid[]={INT_MIN,-1,947,1023,2048,INT_MAX};
    for (unsigned n=0;n<sizeof(invalid)/sizeof(*invalid);n++)
        assert(af_v3_furniture_action_sound(invalid[n],0)==-1);
    for (int slot=0;slot<1024;slot++) {
        struct Item *r=af_test_furniture_records+slot;
        r->index=(u16)(1024+slot);r->item=(u16)(0x3000+slot*4);r->enabled=1;
        for (int category=0;category<5;category++) {
            r->action_sound=(u8)category;
            for (int mode=-1;mode<3;mode++) {
                int expected=category>=1 && category<=2 && mode>=0 && mode<2 ?
                    af_test_furniture_sounds[(category-1)*2+mode] : -1;
                assert(af_v3_furniture_action_sound(r->index,mode)==expected);
            }
            enabled=0;assert(af_v3_furniture_action_sound(r->index,0)==-1);enabled=1;
        }
        r->action_sound=2;r->enabled=0;assert(af_v3_furniture_action_sound(r->index,0)==-1);
        r->enabled=1;r->item++;assert(af_v3_furniture_action_sound(r->index,0)==-1);
    }
    puts("shared furniture sounds, original fallbacks, and bounds pass");
}
