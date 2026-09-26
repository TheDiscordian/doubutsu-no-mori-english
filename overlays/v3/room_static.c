#include "room_static.h"
#ifdef AF_V3_ROOM_PARTICLES
#include "room_effects.h"
#include "room_motion.h"
extern void sAdo_OngenPos(u32,u8,float *);

static void emit(RoomSoundActor *actor,RoomRigGame *game,const RoomStaticRecord *r) {
    if (!game || room_transition_state(actor->state)) return;
    RoomEffectClip *clip=room_effect_clip;
    EffectPosition pos={actor->position[0],actor->position[1],actor->position[2]};
    if (r->mode==3 && r->parameter==9 && r->sound==0x55) {
        sAdo_OngenPos((u32)(uptr)actor,(u8)r->sound,actor->position);
        /* Native play_frame advances at 30 Hz; source cadence is sixteen
           updates at 60 Hz. Do not use the graphics-context frame counter. */
        if (clip && !(*(u32 *)((u8 *)game+0x1EA0)&7u)) {
            pos.y+=30.0f;
            clip->request(ROOM_EFFECT_STEAM,pos,1,0,game,0xFFFF,r->parameter,0);
        }
    } else if (r->mode==4 && !r->parameter && actor->changed==1 && clip) {
        /* The native contact owner/stride are independently checked. */
        u8 **room=(u8 **)room_static_clip;
        if (!room || !*room) return;
        int direction=*(int *)(*room+0x178+0x28);
        if (direction!=0 && direction!=2) return;
        s16 angle=*(s16 *)((u8 *)actor+0x124);
        if (direction==2) angle=(s16)((u16)angle+0x8000u);
        clip->request(ROOM_EFFECT_PROJECTILE,pos,2,angle,game,0xFFFF,0,0);
    }
}
#endif

int af_v3_room_static_mv(RoomSoundActor *actor,void *room,RoomRigGame *game) {
    (void)game;
    const RoomStaticTable *table=&af_v3_room_static_table;
    if (!actor || table->magic!=0x41464931u || table->count>128 ||
            table->stride!=8 || table->reserved) return 0;
    u32 index=actor->index;
    if (index>=2048 && index<3072) index-=1024;
    for (u32 i=0;i<table->count;++i) {
        const RoomStaticRecord *r=table->rows+i;
        if (r->index!=index) continue;
        if (r->reserved) return 1;
        if (r->mode==1 && r->parameter==1) {
            RoomPrivateWallet *player=room_static_private;
            /* The donor accepts every nonzero pulse and has no state gate. */
            if (actor->changed && player && player->wallet) {
                sAdo_OngenTrgStart(r->sound,actor->position);
                --player->wallet;
            }
        } else if (r->mode==2 && r->parameter<16 && !r->sound) {
            RoomStaticClip *clip=room_static_clip;
            /* Native melody handles the press and refreshes position even
               when there is no new press. Do not apply the trigger gate. */
            if (clip && clip->melody) clip->melody(actor,room,r->parameter);
        }
#ifdef AF_V3_ROOM_PARTICLES
        else if (r->mode==3 || r->mode==4) emit(actor,game,r);
#endif
        return 1;
    }
    return 0;
}
