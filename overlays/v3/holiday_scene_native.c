/* Mainland scene services. Use the existing N64 room owner for rhythm and
 * gyroid capture, including its installed imported-furniture profile readers. */
#include "holiday_scene_native.h"
#include "holiday_demo.h"
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
extern const u32 af_holiday_scene_room_descriptor[8];
extern void **af_holiday_scene_room_clip;
extern int af_holiday_scene_pool_variant(void);
#ifndef AF_HOLIDAY_SCENE_CALL
#define AF_HOLIDAY_SCENE_CALL(at) ((void (*)(void))(uptr)(at))()
#endif
static int room(u32 *loaded,unsigned char **actor) {
    *actor=0;*loaded=0;
    if(!af_holiday_scene_room_clip || !af_holiday_scene_room_clip[0])return 1;
    const u32 *d=af_holiday_scene_room_descriptor;
    if(d[0]!=0x0082D7F0 || d[2]!=0x80936710 || d[1]<d[0] ||
       d[3]<d[2] || d[1]-d[0]>d[3]-d[2] ||
       d[1]-d[0]<0x40E4 || d[4]<0x80000000 || d[4]>=0x80800000 ||
       d[3]-d[2]>0x80800000-d[4])return 0;
    *actor=af_holiday_scene_room_clip[0];*loaded=d[4];return 1;
}
int af_holiday_scene_read(void *context,AFHolidayTransition *s) {
    (void)context;
    if(!s || !af_hd_game)return 0;
    u32 loaded;unsigned char *actor;
    int shape=af_holiday_scene_pool_variant();
    if(shape<0 || shape>=7 || !room(&loaded,&actor))return 0;
    const signed char *game=af_hd_game;
    s->pool_variant=(u32)shape;
    s->play.block_table.block_x=game[0xE4];
    s->play.block_table.block_z=game[0xE5];
    /* 47C is the live console request, set by the same room callback used
     * by imported consoles. It stays set through the requested scene change.
     * Source bit 2 protects this interval, not every ordinary room message. */
    s->common.my_room_message_control_flags=actor && *(int *)(actor+0x47C)?4:0;
    /* The installed N64 owners have no separate PRESENT_DEMO/second demo
     * clip. Ordinary and imported handovers use the existing demo gate that
     * native_fade already reads. A future PRESENT_DEMO import needs a reader. */
    s->present_busy=0;
    /* Ceremony owner 7 is not a scheduled diary owner. This service must not
     * manufacture its live actor/common area from another event's storage. */
    s->groundhog_present=s->groundhog_save_present=0;
    s->common.event_title_fade_in_progress=af_hd_state.fading_title;
    return 1;
}
void af_holiday_scene_commit(void *context,const AFHolidayTransition *s,unsigned int phase) {
    (void)context;
    if(s && phase==AF_HT_RETURN_STATE)
        af_hd_state.fading_title=s->common.event_title_fade_in_progress;
}
void af_holiday_scene_tempo(void *context) {
    (void)context;u32 loaded;unsigned char *actor;
    if(!room(&loaded,&actor) || !actor)return;
    AF_HOLIDAY_SCENE_CALL(loaded+0x8093A7C4-0x80936710); /* actual room tempo */
    AF_HOLIDAY_SCENE_CALL(loaded+0x80936E98-0x80936710); /* all gyroid steps */
}
void af_holiday_scene_climate(void *context,int climate) {
    (void)context;(void)climate;
    /* Source mainland 0 -> 2 -> 4 -> 0 has GetClimate()==0 and
     * CheckBeforeScenePerpetual()==0 throughout. N64 has only that mainland
     * climate. Island 1 -> 3 -> 5 is not an imported feature, and must not
     * introduce a bogus N64 weather change during a holiday announcement. */
}
static int alternate(void *context) {(void)context;return AF_HD_EVENTMSG2;}
int af_holiday_scene_bind(AFHolidayTransitionServices *s) {
    if(!s || !s->maps || !s->map_bytes || !s->status || !s->resolve)return 0;
    s->read=af_holiday_scene_read;s->commit=af_holiday_scene_commit;
    s->climate=af_holiday_scene_climate;s->tempo=af_holiday_scene_tempo;
    s->alternate_demo=alternate;
    return 1;
}
