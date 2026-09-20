/* Complete indexed looping room rigs with source switch-driven speed changes. */
#include "room_rigs.h"

static const RoomRigRecord *find(u32 index) {
    /* Catalogue actors retain the catalogue's index, 1024 above the room
       index for imported furniture. Both contexts use the same full model. */
    if (index>=2048u && index<3072u) index-=1024u;
    if (room_rig_table->magic!=ROOM_RIG_MAGIC || room_rig_table->count>ROOM_RIG_CAPACITY ||
            room_rig_table->stride!=sizeof(RoomRigRecord) || room_rig_table->reserved) return 0;
    for (u32 i=0;i<room_rig_table->count;++i) {
        const RoomRigRecord *r=room_rig_table->rows+i;
        if (r->index!=index) continue;
        if (r->index<1024 || r->index>=2048 || r->bytes<32 || r->bytes>9216 || (r->bytes&15) ||
                !r->joints || r->joints>6 || !r->shown || r->shown>r->joints ||
                (r->skeleton&3) || r->skeleton<0x06000000u || r->skeleton>0x06000000u+r->bytes-8 ||
                (r->animation&3) || r->animation<0x06000000u || r->animation>0x06000000u+r->bytes-20) return 0;
        return r;
    }
    return 0;
}

void af_v3_room_rig_ct(RoomRig *actor,u8 *data) {
    const RoomRigRecord *r=find(actor->index);
    if (!r || !data) return;
    u8 *skeleton=Lib_SegmentedToVirtual((void *)(uptr)r->skeleton);
    void *animation=Lib_SegmentedToVirtual((void *)(uptr)r->animation);
    if (skeleton[0]!=r->joints || skeleton[1]!=r->shown) return;
    cKF_SkeletonInfo_R_ct(&actor->keyframe,skeleton,animation,actor->joint,actor->morph);
    cKF_SkeletonInfo_R_init_standard_repeat(&actor->keyframe,animation,(void *)0);
    actor->speed.bits=0;actor->target.bits=0x3F000000u;
    actor->keyframe.speed.bits=0;
    cKF_SkeletonInfo_R_play(&actor->keyframe);
}

void af_v3_room_rig_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    FloatWord high,idle,step;
    (void)room;(void)game;
    if (!data || !find(actor->index)) return;
    high.bits=0x3FA00000u;idle.bits=0x3F000000u;step.bits=0x3C23D70Au;
    /* Two exact source updates at the N64 update rate. Retain the native
       owner's changed-switch flag until the owner clears it after callbacks. */
    for (u32 i=0;i<2;++i) {
        if (!i && actor->changed) actor->target=high;
        else if (actor->speed.f>=high.f) actor->target=idle;
        if (actor->speed.f<actor->target.f) {
            actor->speed.f+=step.f;
            if (actor->speed.f>actor->target.f) actor->speed=actor->target;
        } else if (actor->speed.f>actor->target.f) {
            actor->speed.f-=step.f;
            if (actor->speed.f<actor->target.f) actor->speed=actor->target;
        }
        actor->keyframe.speed=actor->speed;
        cKF_SkeletonInfo_R_play(&actor->keyframe);
    }
}

void af_v3_room_rig_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    (void)room;
    const RoomRigRecord *r=find(actor->index);
    if (!r || !data) return;
    RoomRigGraphics *gfx=game->gfx;
    RoomCommand *commands=gfx->head;
    uptr front=(uptr)commands,back=(uptr)gfx->tail;
    uptr xlu=(uptr)gfx->xlu_head,xlu_back=(uptr)gfx->xlu_tail;
    /* Parent matrix plus the skeleton's segment, matrix, and list commands.
       Both joint callbacks are verified no-ops in this source category. */
    /* Native graph allocations are eight-byte aligned. A valid tail ending
       in eight must not suppress an entire room model. */
    if ((front&7) || (back&7) || (xlu&7) || back<front || back-front<64u+(2u+2u*r->shown)*8u ||
            xlu_back<xlu || xlu_back-xlu<8) return;
    gfx->head=commands+1;
    commands[0]=(RoomCommand){0xDA380003,(u32)(uptr)_Matrix_to_Mtx_new(gfx)};
    cKF_Si3_draw_R_SV(game,&actor->keyframe,actor->matrices[game->frame&1],
                    (void *)0,(void *)0,(void *)0);
}
