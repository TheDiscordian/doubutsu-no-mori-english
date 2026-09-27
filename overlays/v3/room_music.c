/* Complete source room-music ownership and rotated-radio lifecycle. */
#include "room_music.h"
#include "room_effects.h"
extern void mBGMPsComp_make_ps_room(u8,u16);
extern void mBGMPsComp_delete_ps_room(u8,u16);
extern void mBGMPsComp_MDPlayerPos_make(void);
extern void mBGMPsComp_MDPlayerPos_delete(void);
extern void Matrix_RotateY(s16,int);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);

void af_v3_room_music_apply(RoomMusic *m,RoomRig *actor,u8 radio_song) {
    if (!m || m->reserved!=1) return;
    if (!m->active) {
        if (m->song!=-1) {
            mBGMPsComp_make_ps_room((u8)m->song,0);
            if (m->song!=radio_song) mBGMPsComp_MDPlayerPos_make();
            m->active=1;m->active_actor=actor;
        }
    } else if (m->song==-1) {
        mBGMPsComp_delete_ps_room((u8)m->previous_song,0);
        mBGMPsComp_MDPlayerPos_delete();
        m->active=0;m->active_actor=(void *)0;
    } else {
        mBGMPsComp_delete_ps_room((u8)m->previous_song,0);
        if (m->previous_song!=radio_song) mBGMPsComp_MDPlayerPos_delete();
        mBGMPsComp_make_ps_room((u8)m->song,0);
        if (m->song!=radio_song) mBGMPsComp_MDPlayerPos_make();
        m->active=1;m->active_actor=actor;
    }
    m->reserved=0;m->previous_song=m->song;
}

void af_v3_room_music_reserve(RoomMusic *m,RoomRig *actor,int song,s16 timer) {
    if (!m) return;
    m->reserved=1;m->timer=timer;m->song=song;m->reserved_actor=actor;
}

void af_v3_room_radio_ct(RoomRig *actor) { actor->changed=0;actor->switched=0; }

void af_v3_room_radio_dt(RoomRig *actor,RoomMusic *m,u8 song) {
    if (actor->switched==1) {
        af_v3_room_music_reserve(m,actor,-1,0);af_v3_room_music_apply(m,actor,song);
    }
}

void af_v3_room_radio_move(RoomRig *actor,RoomMusic *m,u8 song,void (*exclusive)(RoomRig *)) {
    if (!m || !exclusive) return;
    if (actor->haniwa_state==1) {
        af_v3_room_music_reserve(m,actor,song,0);actor->haniwa_state=0;
    } else if (actor->changed) {
        int on=actor->switched!=0;
        exclusive(actor);
        af_v3_room_music_reserve(m,actor,on ? song : -1,0);
        af_v3_room_music_apply(m,actor,song);actor->switched=on;
    }
}

void af_v3_room_music_disk_dt(RoomRig *actor,RoomMusic *m,u8 radio_song) {
    if (!actor || !m || actor->switched!=1) return;
    mBGMPsComp_delete_ps_room((u8)m->song,0);
    m->active=0;m->active_actor=(void *)0;m->previous_song=-1;
    if (m->song!=radio_song) mBGMPsComp_MDPlayerPos_delete();
}

void af_v3_room_radio_notes(RoomRig *actor,RoomRigGame *game,u16 source_item) {
    /* This category has no skeleton; its first joint halfword is private work. */
    s16 *counter=&actor->joint[0][0];
    if (actor->switched!=1 || !game) return;
    for (u32 step=0;step<2;++step) {
        if (*counter>=36) {
            RoomEffectClip *clip=room_effect_clip;
            if (clip) clip->request(32,
                (EffectPosition){actor->position[0],actor->position[1]-3.0f,actor->position[2]},
                1,(s16)((u16)actor->s_angle_y-0x1000u),game,source_item,1,0);
            *counter=0;
        }
        ++*counter;
    }
}

void af_v3_room_radio_draw(RoomRig *actor,RoomRigGame *game,u32 model,u32 palette) {
    (void)actor;
    if (!game || !game->gfx) return;
    RoomRigGraphics *g=game->gfx;uptr head=(uptr)g->head,end=(uptr)g->tail;
    if (!head || !end || ((head|end)&7) || end<head || end-head<64+15+24) return;
    uptr matrix=(end-64)&~(uptr)15;g->tail=(u8 *)matrix;
    Matrix_RotateY(-0x7000,1);_Matrix_to_Mtx((void *)matrix);
    *g->head++=(RoomCommand){0xDA380003,(u32)matrix};
    *g->head++=(RoomCommand){0xDB060020,palette};
    *g->head++=(RoomCommand){0xDE000000,model};
    osWritebackDCache((void *)matrix,64);
}
