/* Complete source-title comparison; native initializer I/O is a host double. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "holiday_scene.h"
#include "holiday_native.h"
#include "holiday-scene-data.h"
volatile short af_holiday_scene_event,af_holiday_scene_flags;
static unsigned int demo[0x328/4];
unsigned char *af_holiday_scene_demo=(unsigned char *)demo;
static unsigned int calls;
int af_holiday_scene_original_init(void) {
    memset(demo,0xA5,sizeof(demo));calls++;
    demo[0x300/4]=0x1743;demo[0x304/4]=0x12345678;
    demo[0x2F8/4]=6;demo[0x308/4]=0;demo[0x30C/4]=30;
    return 1;
}
int main(void) {
    unsigned int baseline[sizeof(demo)/sizeof(demo[0])];
    const unsigned int flags[]={0,1,9,65535};
    for(unsigned int donor=0;donor<128;donor++) {
        int title=get_title_no_for_event(donor);
        for(unsigned int f=0;f<4;f++) {
            int expected=title<0?0:message_ids[title+(flags[f]==1?0:16)];
            assert(af_holiday_scene_message(af_holiday_scene_titles,208,donor,flags[f])==expected);
            int native=af_holiday_native_type(donor);
            if(native<0)continue;
            af_holiday_scene_event=native;af_holiday_scene_flags=flags[f];
            af_holiday_scene_original_init();memcpy(baseline,demo,sizeof(demo));
            baseline[0x300/4]=expected;unsigned int before=calls;
            assert(af_holiday_scene_demo_init()==1 && calls==before+1);
            assert(!memcmp(demo,baseline,sizeof(demo)));
        }
    }
    for(int native=-1;native<=128;native++) {
        if(native>=AF_HN_FIRST && native<AF_HN_END)continue;
        af_holiday_scene_event=native;af_holiday_scene_original_init();memcpy(baseline,demo,sizeof(demo));
        assert(af_holiday_scene_demo_init()==1 && !memcmp(demo,baseline,sizeof(demo)));
    }
    unsigned char bad[208];memcpy(bad,af_holiday_scene_titles,sizeof(bad));
    assert(af_holiday_scene_message(0,208,1,1)==-1);
    assert(af_holiday_scene_message(bad,207,1,1)==-1);
    assert(af_holiday_scene_message(bad,208,128,1)==0);
    bad[16+1]=16;assert(af_holiday_scene_message(bad,208,1,1)==-1);
    bad[16+1]=0;bad[144]=0x80;assert(af_holiday_scene_message(bad,208,1,1)==-1);
    bad[0]=0;assert(af_holiday_scene_message(bad,208,1,1)==-1);
    puts("All source event-title cases and flags match; original-event fallback, door/colour/camera/timers, and malformed packets pass. Native initializer is doubled.");
}
