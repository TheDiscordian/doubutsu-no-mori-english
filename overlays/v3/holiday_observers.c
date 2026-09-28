/* Live observations for the complete shared Tortimer controller. */
#include "holiday_observers.h"
#include "holiday_native.h"
#include "holiday_world.h"
#ifndef AF_HOLIDAY_MIKO_PROFILE
#error Supply the fixed additive New Year Miko reservation
#endif

static unsigned int event(void *context) {
    (void)context;return af_holiday_native_current();
}
static unsigned int field(void *context) {
    (void)context;return af_holiday_native_field();
}
static int shrine(void *context,short position[3]) {
    (void)context;return position && af_holiday_observers_shrine(position);
}
static int runner(void *context,short position[2]) {
    (void)context;
    int type=af_holiday_native_type(15); /* donor foot race, NOT native event 10 */
    if(type<0 || !position)return 0;
    const unsigned char *saved=af_holiday_observers_save(type,8);
    if(!saved || !(saved[2]&4))return 0; /* big-endian u16 flags & 0x400 */
    position[0]=(short)((unsigned int)saved[10]<<8|saved[11]);
    position[1]=(short)((unsigned int)saved[12]<<8|saved[13]);
    return 1;
}
static void restore_melody(void *context) {
    /* The complete donor actor initializes melody_inst=0 and has no nonzero
     * assignment. Its conditional restoration therefore performs no write. */
    (void)context;
}
int af_holiday_npc_bind(AFHolidayNpc *a) {
    if(!a || !a->game || !af_holiday_world_resources(a) || !af_holiday_observers_clip())return 0;
    a->ops.context=a;a->ops.event=event;a->ops.field_event=field;
    a->ops.shrine=shrine;a->ops.runner=runner;a->ops.restore_melody=restore_melody;
    /* af_holiday_world_bind supplies variant; retain animation and transport. */
    return 1;
}
void af_holiday_npc_unregister(AFHolidayNpc *a) {
    if(!a || !a->game)return;
    int type=af_holiday_native_cleanup();
    if(type>=0)af_holiday_native_notify((unsigned int)type,a);
    else if(type==-2) {
        /* The additive owner uses its own reserved profile. Never delete the
         * original N64 Miko (84) merely because its donor profile is also 84. */
        void *miko=af_holiday_observers_find(a->game,AF_HOLIDAY_MIKO_PROFILE,3);
        if(miko)af_holiday_observers_delete(miko);
    }
}
unsigned int af_holiday_observers_clip_address(const unsigned int d[8]) {
    if(!d || d[0]!=0x008681F0 || d[2]!=0x809735B0 ||
       d[1]<=d[0] || d[1]-d[0]>0x30000 || d[3]<0x80983B9C ||
       d[3]-d[2]<d[1]-d[0] || d[3]-d[2]>0x30000 ||
       d[4]<0x80000000 || d[4]&3 || d[4]>=0x80800000 ||
       d[3]-d[2]>0x80800000-d[4])return 0;
    return d[4]+0x80983A80-0x809735B0;
}
int af_holiday_observers_clip_entries(unsigned int base,const unsigned int *clip) {
    static const unsigned int entries[][2]={
        {0,0x80980328},{0xBC,0x8097FC44},{0xC0,0x8097F520},
        {0xC4,0x8097F94C},{0xCC,0x8097F358},{0xD0,0x80977AB0},
        {0xE4,0x8097866C},{0xF8,0x8097BF90},{0x108,0x8097F0BC},
        {0x10C,0x809774A0},{0x110,0x8097E7F4}};
    if(!clip || base<0x80000000 || base>0x807D0000)return 0;
    for(unsigned int i=0;i<sizeof(entries)/sizeof(entries[0]);i++)
        if(clip[entries[i][0]/4]!=base+entries[i][1]-0x809735B0)return 0;
    return 1;
}
