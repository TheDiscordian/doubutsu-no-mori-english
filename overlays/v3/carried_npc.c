/* Native character services for the carried-quest owner. Source animation,
 * schedule, and event identities do not index the original native tables. */
#include "carried_event.h"
#include "room_rigs.h"
extern const u32 *volatile af_hp_native_npc_clip;
extern int af_holiday_observers_clip(void);
extern const u32 af_cw_available;
extern u32 af_carried_quantity(u32);
extern void af_hp_native_dying(int,ACTOR *);

int af_hp_owner_enabled(const AFHPRecord *record) {
    if(!record)return 0;
    if(record->event==114)
        return *(const volatile u32 *)&af_cw_available==1 && af_carried_quantity(0x2D28)==1;
    return af_hp_available!=0;
}
s16 *af_cw_actor_specific(ACTOR *actor) {return (s16 *)((u8 *)actor+0x24);}
xyz_t *af_cw_scale(ACTOR *actor) {return (xyz_t *)((u8 *)actor+0x5C);}
u8 *af_cw_shadow(ACTOR *actor) {return (u8 *)actor+0x108;}
/* Native initialization and voice submission store/read a word, not the
 * donor's short or a byte at the same offset. Big-endian byte stores here
 * would change the high byte of the instrument number. */
s32 *af_cw_melody(ACTOR *actor) {return (s32 *)((u8 *)actor+0x930);}
int af_cw_seconds(void) {
    const lbRTC_time_c *t=af_cw_clock();
    return t->hour*3600+t->min*60+t->sec;
}
void af_cw_dying(int source,ACTOR *actor) {
    if(source==114 && actor && af_hp_owned(actor))af_hp_native_dying(115,actor);
}
void af_cw_draw(ACTOR *actor,GAME *game,unsigned alpha) {
    if(!actor || !game || alpha>255 || !af_hp_admit(actor,game) ||
       !af_hp_native_npc_clip || !af_holiday_observers_clip())return;
    RoomRigGraphics *graphics=*(RoomRigGraphics **)game;
    if(!graphics)return;
    uptr head=(uptr)graphics->xlu_head,tail=(uptr)graphics->xlu_tail;
    if(!head || ((head|tail)&7u) || tail<head || tail-head<16)return;
    *graphics->xlu_head++=(RoomCommand){0xE7000000,0};
    *graphics->xlu_head++=(RoomCommand){0xFB000000,0xFFFFFF00u|alpha};
    af_hp_npc_services.draw_proc(actor,game);
}
