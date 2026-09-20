/* Complete shared room rigs; each record retains its actual behaviour. */
#include "room_rigs.h"

#ifdef AF_V3_ROOM_TRIGGER_SOUND
void af_v3_room_sound_mv(RoomSoundActor *actor,void *room,RoomRigGame *game,u8 *data) {
    (void)room;(void)game;(void)data;
    if (!actor || actor->changed!=1 || (actor->state>=12 && actor->state<=15)) return;
    if (room_sound_table->magic!=ROOM_SOUND_MAGIC || room_sound_table->count>ROOM_SOUND_CAPACITY ||
            room_sound_table->stride!=sizeof(RoomSoundRecord) || room_sound_table->reserved) return;
    u32 index=actor->index;
    if (index>=2048u && index<3072u) index-=1024u;
    for (u32 i=0;i<room_sound_table->count;++i) {
        const RoomSoundRecord *r=room_sound_table->rows+i;
        if (r->index!=index) continue;
        if (r->index<1024 || r->index>=2048 || r->reserved || (r->word&0x80u) ||
                (((r->word>>8)&127u)!=1u && ((r->word>>8)&127u)!=4u)) return;
        /* The original N64 dispatcher lacks the donor's singleton flag.
           Its six live slots retain the full word, including that flag. */
        if (r->word&0x8000u) for (u32 j=0;j<6;++j)
            if (room_native_triggers[j].word==r->word) return;
        sAdo_OngenTrgStart(r->word,actor->position);
        return;
    }
}
#endif

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
#ifdef AF_V3_ROOM_RIG_PACKET
        if (r->reserved || r->mode>ROOM_RIG_STORAGE) return 0;
        if (r->mode==ROOM_RIG_SWITCH && (r->first.bits || r->last.bits)) return 0;
        if (r->mode==ROOM_RIG_CLOCK && (!r->first.bits || r->first.bits>=r->joints ||
                !r->last.bits || r->last.bits>=r->joints || r->first.bits==r->last.bits)) return 0;
        /* Positive finite floats compare in the same order as their bit words. */
        if (r->mode==ROOM_RIG_STORAGE && (r->first.bits<0x3F800000u ||
                r->last.bits<=r->first.bits || r->last.bits>0x43800000u)) return 0;
#endif
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
#ifdef AF_V3_ROOM_RIG_PACKET
    if (r->mode==ROOM_RIG_STORAGE)
        cKF_SkeletonInfo_R_init_standard_stop(&actor->keyframe,animation,(void *)0);
    else
#endif
        cKF_SkeletonInfo_R_init_standard_repeat(&actor->keyframe,animation,(void *)0);
    actor->speed.bits=0;actor->target.bits=0x3F000000u;
    actor->keyframe.speed.bits=0;
#ifdef AF_V3_ROOM_RIG_PACKET
    if (r->mode==ROOM_RIG_CLOCK) actor->keyframe.speed.bits=0x3F000000u;
#endif
    cKF_SkeletonInfo_R_play(&actor->keyframe);
}

void af_v3_room_rig_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    FloatWord high,idle,step;
    (void)room;(void)game;
    if (!data || !find(actor->index)) return;
#ifdef AF_V3_ROOM_RIG_PACKET
    const RoomRigRecord *r=find(actor->index);
    if (r->mode==ROOM_RIG_STORAGE) {
        RoomRigClip *clip=room_rig_clip;
        if (room && game && clip && clip->open_close)
            clip->open_close(actor,room,game,r->first.f,r->last.f);
        return;
    }
    if (r->mode==ROOM_RIG_CLOCK) {
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        return;
    }
#endif
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

#ifdef AF_V3_ROOM_RIG_PACKET
static int clock_before(void *game,RoomKeyframe *key,int joint,void *list,
                        void *flags,void *arg,s16 *rotation,void *position) {
    (void)game;(void)key;(void)list;(void)flags;(void)position;
    const RoomRigRecord *r=arg;
    if ((u32)joint==r->first.bits) rotation[2]=(s16)((u16)rotation[2]-room_rig_hour);
    else if ((u32)joint==r->last.bits) rotation[2]=(s16)((u16)rotation[2]-room_rig_minute);
    return 1;
}
#endif

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
#ifdef AF_V3_ROOM_RIG_PACKET
                    r->mode==ROOM_RIG_CLOCK ? (void *)clock_before : (void *)0,(void *)0,(void *)r);
#else
                    (void *)0,(void *)0,(void *)0);
#endif
}
