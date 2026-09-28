#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_transition.h"
#include "holiday_native.h"
#include "holiday-identity-data.h"
AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
unsigned char af_holiday_native_index[128];
static int current=-1,bind_calls,fade_calls;
int af_holiday_transition_native_map(void) {return current;}
int af_holiday_transition_native_collision(int x,int z) {assert(x==4 && z==6);return 2;}
int af_decor_actor_resolve(unsigned short name) {return name==0x582A?0x5F00:-1;}
int af_holiday_scene_bind(AFHolidayTransitionServices *s) {
    assert(s && s->maps==af_holiday_transition_maps && s->map_bytes==1496);
    assert(s->status && s->resolve && s->original_rank && s->original_collision);
    ++bind_calls;return 1;
}
int af_holiday_transition_native_fade(void *context,void *manager,unsigned int donor,
        unsigned int native,unsigned int title,unsigned int landmark) {
    AFHolidayTransitionServices *s=context;
    assert(s->status && manager==af_holiday_native_days && donor==20 &&
        native==(unsigned int)af_holiday_native_type(20) && title==1 && landmark==4);
    ++fade_calls;return 1;
}
int main(void) {
    AFHolidayTransitionServices s;
    memset(af_holiday_native_index,255,sizeof(af_holiday_native_index));
    assert(af_holiday_transition_bind(&s) && bind_calls==1);
    for(unsigned int donor=0;donor<128;donor++) {
        int type=af_holiday_native_type(donor);
        assert(!s.status(0,donor,AF_HE_ACTIVE));
        if(type<0)continue;
        af_holiday_native_index[type]=0;
        af_holiday_native_days[0]=(AFHolidayNativeDay){.type=(unsigned int)type,.status=AF_HE_EXIST};
        assert(!s.status(0,donor,AF_HE_ACTIVE));
        af_holiday_native_days[0].status|=AF_HE_ACTIVE;
        assert(s.status(0,donor,AF_HE_ACTIVE)==1);
        af_holiday_native_days[0].status|=AF_HE_ERROR;
        assert(!s.status(0,donor,AF_HE_ACTIVE));
        af_holiday_native_days[0].type=0;assert(s.status(0,donor,AF_HE_ACTIVE)==-1);
        af_holiday_native_index[type]=AF_HN_DAYS;assert(s.status(0,donor,AF_HE_ACTIVE)==-1);
        af_holiday_native_index[type]=255;
    }
    assert(s.resolve(0,0x582A)==0x5F00 && s.resolve(0,0x5829)==-1);
    assert(s.resolve(0,0x1582A)==-1 && s.resolve(0,0xD074)==-1);
    const int types[]={11,12,10,8,7,9,13,3,20,2,16,21,22,6,14};
    const int ranks[]={0,1,2,3,4,5,6,7,8,9,10,11,11,13,14};
    for(unsigned int i=0;i<15;i++) {current=types[i];assert(s.original_rank(0)==ranks[i]);}
    current=-1;assert(s.original_rank(0)==-1);current=37;assert(s.original_rank(0)==-2);
    assert(s.original_collision(0,4,6)==2);
    assert(af_holiday_transition_live_fade(0,af_holiday_native_days,20,
        af_holiday_native_type(20),1,4)==1 && fade_calls==1 && bind_calls==2);
    puts("Live identity binding: all 44 scheduled owners, real status slots, absent/error/corrupt state, decoration resolver, all 15 native layout priorities, and the connected fade wrapper pass. Native I/O is doubled.");
}
