/* Complete shared room rigs; each record retains its actual behaviour. */
#include "room_rigs.h"
#include "room_motion.h"
#ifdef AF_V3_ROOM_MUSIC
#include "room_music_native.h"
#endif
#ifdef AF_V3_ROOM_DUAL_MOTION
#include "room_dual_motion.h"
#endif
#ifdef AF_V3_ROOM_EFFECT_RIG
#include "room_effect_rigs.h"
#endif
#ifdef AF_V3_ROOM_REVERSIBLE
#include "room_reversible.h"
#endif
#ifdef AF_V3_ROOM_MATERIALS
#include "room_materials.h"
#endif
#ifdef AF_V3_ROOM_EFFECTS
#include "room_effects.h"
#endif
#ifdef AF_V3_ROOM_ROLLING
typedef struct { u8 prefix[0x1A0];int direction; } RoomMotionOwner;
typedef struct { RoomMotionOwner *owner; } RoomMotionClip;
#ifdef __mips__
#define room_motion_clip (*(RoomMotionClip *volatile *)0x80136F2Cu)
#else
extern RoomMotionClip *af_v3_test_motion_clip;
#define room_motion_clip af_v3_test_motion_clip
#endif
extern float sqrtf(float);
static void rolling_move(RoomRig *actor,const RoomRigRecord *r) {
    /* The native owner overwrites last_position before invoking callbacks.
       Retain previous X/Z in this category's instance-local spare vectors. */
    float dx=actor->position[0]-actor->speed.f,dz=actor->position[2]-actor->target.f;
    actor->speed.f=actor->position[0];actor->target.f=actor->position[2];
    RoomKeyframe *key=&actor->keyframe;key->speed.f=0.0f;
    RoomMotionClip *clip=room_motion_clip;
    if (clip && clip->owner) {
        int direction=clip->owner->direction;
        int push=room_push_state(actor->state),pull=room_pull_state(actor->state);
        if ((push || pull) && (direction==1 || direction==3)) {
            float distance=sqrtf(dx*dx+dz*dz);
            key->speed.f=(0.1f+(distance*0.5f)/1.55f)*0.5f;
            int forward=push ? direction==3 : direction==1;
            key->start=forward ? 1.0f : r->first.f;
            key->end=forward ? r->first.f : 1.0f;
        }
    }
    /* Two donor-rate evaluations preserve the movement-independent base speed. */
    cKF_SkeletonInfo_R_play(key);cKF_SkeletonInfo_R_play(key);
}
#endif

#ifdef AF_V3_ROOM_TRIGGER_SOUND
static const RoomSoundRecord *sound_record(u32 index) {
    if (room_sound_table->magic!=ROOM_SOUND_MAGIC || room_sound_table->count>ROOM_SOUND_CAPACITY ||
            room_sound_table->stride!=sizeof(RoomSoundRecord) || room_sound_table->reserved) return 0;
    if (index>=2048u && index<3072u) index-=1024u;
    for (u32 i=0;i<room_sound_table->count;++i) {
        const RoomSoundRecord *r=room_sound_table->rows+i;
        if (r->index!=index) continue;
        u32 group=(r->word>>8)&127u;
        if (r->index<1024 || r->index>=2048 || (r->word&0x80u) ||
                (group!=0u && group!=1u && group!=4u)) return 0;
#ifdef AF_V3_ROOM_EFFECTS
        if (r->reserved && (r->wall!=76 || r->effect!=ROOM_EFFECT_FLASH_CONTROLLER ||
                (r->system&0x8080u)!=0x8000u || ((r->system>>8)&127u)!=1u)) return 0;
#else
        if (r->reserved) return 0;
#endif
        return r;
    }
    return 0;
}
static int sound_active(u32 word) {
    if (word&0x8000u) for (u32 j=0;j<6;++j)
        if (room_native_triggers[j].word==word) return 1;
    return 0;
}
static void trigger(u32 index,float *position) {
    const RoomSoundRecord *r=sound_record(index);
    if (r) {
        /* The original N64 dispatcher lacks the donor's singleton flag.
           Its six live slots retain the full word, including that flag. */
        if (sound_active(r->word)) return;
        sAdo_OngenTrgStart(r->word,position);
        return;
    }
}
#ifdef AF_V3_ROOM_EFFECTS
static void trigger_conditional(RoomRig *actor,RoomRigGame *game) {
    const RoomSoundRecord *r=sound_record(actor->index);
    if (!r || !r->reserved || af_v3_room_effect_wall()!=r->wall) return;
    if (!sound_active(r->system)) sAdo_SysTrgStart(r->system);
    RoomEffectClip *clip=room_effect_clip;
    if (clip) clip->request(r->effect,(EffectPosition){actor->position[0],actor->position[1],actor->position[2]},
        2,0,game,0xFFFF,0,0);
}
#endif
void af_v3_room_sound_mv(RoomSoundActor *actor,void *room,RoomRigGame *game,u8 *data) {
#ifdef AF_V3_ROOM_STATIC
    extern int af_v3_room_static_mv(RoomSoundActor *,void *,RoomRigGame *);
    if (af_v3_room_static_mv(actor,room,game)) return;
#endif
#if defined(AF_V3_ROOM_REACTIONS) || defined(AF_V3_ROOM_COLOURS) || defined(AF_V3_ROOM_PARTICLES) || defined(AF_V3_ROOM_SWITCHED_MATERIAL)
    if (af_v3_room_material_mv((RoomRig *)actor,room,game,data)) return;
#endif
    (void)room;(void)game;(void)data;
    if (!actor || actor->changed!=1 || room_transition_state(actor->state)) return;
    trigger(actor->index,actor->position);
}
#endif

#ifdef AF_V3_ROOM_MATERIAL_RIG
static u32 rig_frame_u16(const u8 *p) { return ((u32)p[0]<<8)|p[1]; }
static const RoomRigMaterial *rig_material(const RoomRigRecord *r,const u8 *data) {
    if (!data || ((uptr)data&7) || (r->first.bits&3) ||
            r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-32u) return 0;
    const RoomRigMaterial *p=(const RoomRigMaterial *)(data+(r->first.bits-0x06000000u));
    u32 size=rig_frame_u16(p->frame_bytes);
    if ((p->segment!=8 && p->segment!=9) || !p->frames || p->frames>8 || p->reserved ||
            p->sound<68 || p->sound>=96 || !rig_frame_u16(p->divisor) || !size || size>r->bytes) return 0;
    for (u32 i=0;i<8;++i) {
        u32 offset=rig_frame_u16(p->offsets[i]);
        if (p->padding[i] || (i<p->frames ? ((offset&7) || offset>r->bytes-size) : offset!=0)) return 0;
    }
    return p;
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
#ifdef AF_V3_ROOM_MUSIC
        if (r->mode==ROOM_RIG_RADIO) {
            if (index<1024 || index>=2048 || r->bytes<32 || r->bytes>9216 || (r->bytes&15) ||
                    r->skeleton || r->animation || r->joints || r->shown || r->reserved ||
                    (r->first.bits&7) || (r->last.bits&7) ||
                    r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-8 ||
                    r->last.bits<0x06000000u || r->last.bits>0x06000000u+r->bytes-32) return 0;
            return r;
        }
#endif
#ifdef AF_V3_SELECTED_PALETTE
        if (r->mode==ROOM_RIG_ROOF) {
            if (index<1024 || index>=2048 || r->bytes<800 || r->bytes>9216 || (r->bytes&15) ||
                    r->skeleton || r->animation || r->joints || r->shown || r->reserved ||
                    r->first.bits!=12 || r->last.bits) return 0;
            return r;
        }
#endif
        if (r->index<1024 || r->index>=2048 || r->bytes<32 ||
#ifdef AF_V3_ROOM_EMBEDDED
                r->bytes>(r->mode==ROOM_RIG_EMBEDDED ? 12288 : 9216) ||
#else
                r->bytes>9216 ||
#endif
                (r->bytes&15) ||
                !r->joints || !r->shown || r->shown>r->joints ||
#ifdef AF_V3_ROOM_REVERSIBLE
                (r->mode==ROOM_RIG_REVERSIBLE || r->mode==ROOM_RIG_EFFECT || r->mode==ROOM_RIG_DUAL ? (r->joints>16 || r->shown>6) : r->joints>8) ||
#else
                r->joints>8 ||
#endif
                (r->skeleton&3) || r->skeleton<0x06000000u || r->skeleton>0x06000000u+r->bytes-8 ||
                (r->animation&3) || r->animation<0x06000000u || r->animation>0x06000000u+r->bytes-20) return 0;
#ifdef AF_V3_ROOM_RIG_PACKET
        if ((r->mode==ROOM_RIG_DUAL ? !r->reserved || r->reserved>127 : r->reserved) ||
                r->mode>ROOM_RIG_EMBEDDED || r->mode==ROOM_RIG_ROOF || r->mode==ROOM_RIG_RADIO) return 0;
#ifdef AF_V3_ROOM_EMBEDDED
        if (r->mode==ROOM_RIG_EMBEDDED && (r->first.bits || r->last.bits)) return 0;
#else
        if (r->mode==ROOM_RIG_EMBEDDED) return 0;
#endif
#ifdef AF_V3_ROOM_DUAL_MOTION
        if (r->mode==ROOM_RIG_DUAL && ((r->first.bits&3) || r->first.bits==r->animation ||
                r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-20)) return 0;
#else
        if (r->mode==ROOM_RIG_DUAL) return 0;
#endif
#ifdef AF_V3_ROOM_EFFECT_RIG
        if (r->mode==ROOM_RIG_EFFECT && (r->last.bits || (r->first.bits&3) ||
                r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-32)) return 0;
#else
        if (r->mode==ROOM_RIG_EFFECT) return 0;
#endif
#if defined(AF_V3_ROOM_REVERSIBLE) && defined(AF_V3_ROOM_TRIGGER_SOUND)
        if (r->mode==ROOM_RIG_REVERSIBLE && (r->last.bits || r->first.bits<0x3F800000u || r->first.bits>0x46FFFE00u)) return 0;
#else
        if (r->mode==ROOM_RIG_REVERSIBLE) return 0;
#endif
#ifdef AF_V3_ROOM_MATERIAL_RIG
        if (r->mode==ROOM_RIG_MATERIAL && (r->last.bits || (r->first.bits&3) ||
                r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-32)) return 0;
#else
        if (r->mode==ROOM_RIG_MATERIAL) return 0;
#endif
#ifdef AF_V3_ROOM_JOINT
        if (r->mode==ROOM_RIG_JOINT && !((r->first.bits==1 || r->first.bits==2
#ifdef AF_V3_ROOM_NEEDLE
                || r->first.bits==4
#endif
                ) ?
                r->last.bits==0 : r->first.bits==0x5103 && r->last.bits==0x00160017)) return 0;
#else
        if (r->mode==ROOM_RIG_JOINT) return 0;
#endif
        if ((r->mode==ROOM_RIG_SWITCH || r->mode==ROOM_RIG_ROLLING) && r->joints>6) return 0;
#ifdef AF_V3_ROOM_ROLLING
        if (r->mode==ROOM_RIG_ROLLING && (r->last.bits || r->first.bits<0x3F800000u || r->first.bits>0x47000000u)) return 0;
#else
        if (r->mode==ROOM_RIG_ROLLING) return 0;
#endif
#ifdef AF_V3_ROOM_BILLBOARD
        if (r->mode==ROOM_RIG_BILLBOARD && (r->last.bits || (r->first.bits&3) ||
                r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-16)) return 0;
#else
        if (r->mode==ROOM_RIG_BILLBOARD) return 0;
#endif
        if (r->mode==ROOM_RIG_SWITCH && (r->first.bits || r->last.bits)) return 0;
        if (r->mode==ROOM_RIG_HIT && (r->first.bits==0 ? r->last.bits!=0 :
                r->first.bits==1 ? r->last.bits!=0x3E800000u :
                r->first.bits!=2 || r->last.bits!=0x3F000000u)) return 0;
#ifndef AF_V3_ROOM_EFFECTS
        if (r->mode==ROOM_RIG_HIT && r->first.bits==2) return 0;
#endif
#ifndef AF_V3_ROOM_TRIGGER_SOUND
        if (r->mode==ROOM_RIG_HIT) return 0;
#endif
        if (r->mode==ROOM_RIG_CLOCK && (!r->first.bits || r->first.bits>=r->joints ||
                !r->last.bits || r->last.bits>=r->joints || r->first.bits==r->last.bits)) return 0;
        /* Positive finite floats compare in the same order as their bit words. */
        if (r->mode==ROOM_RIG_STORAGE && (r->first.bits<0x3F800000u ||
                r->last.bits<=r->first.bits || r->last.bits>0x43800000u)) return 0;
#endif
#ifndef AF_V3_ROOM_RIG_PACKET
        if (r->joints>6) return 0;
#endif
        return r;
    }
    return 0;
}

void af_v3_room_rig_ct(RoomRig *actor,u8 *data) {
    const RoomRigRecord *r=find(actor->index);
    if (!data) return;
    if (!r) {
#ifdef AF_V3_ROOM_MATERIALS
        af_v3_room_material_ct(actor,data);
#endif
        return;
    }
#ifdef AF_V3_SELECTED_PALETTE
    if (r->mode==ROOM_RIG_ROOF) { af_v3_roof_ct(actor,data);return; }
#endif
#ifdef AF_V3_ROOM_MUSIC
    if (r->mode==ROOM_RIG_RADIO) { af_v3_room_radio_ct(actor);return; }
#endif
#ifdef AF_V3_ROOM_MATERIAL_RIG
    if (r->mode==ROOM_RIG_MATERIAL && !rig_material(r,data)) return;
#endif
    u8 *skeleton=Lib_SegmentedToVirtual((void *)(uptr)r->skeleton);
    void *animation=Lib_SegmentedToVirtual((void *)(uptr)r->animation);
    if (skeleton[0]!=r->joints || skeleton[1]!=r->shown) return;
#ifdef AF_V3_ROOM_DUAL_MOTION
    if (r->mode==ROOM_RIG_DUAL) {
        RoomDualMotion motion;
        if (!af_v3_room_dual_resolve(r,data,&motion)) return;
        af_v3_room_dual_ct(actor,skeleton,&motion,room_dual_scene==6);
        af_v3_room_dual_dt(actor);return;
    }
#endif
#ifdef AF_V3_ROOM_EFFECT_RIG
    if (r->mode==ROOM_RIG_EFFECT) {
        const RoomEffectRigParams *p=af_v3_room_effect_rig_params(r,data);
        if (!p) return;
        af_v3_room_effect_rig_ct(actor,skeleton,animation,p);
        af_v3_room_reverse_dt(actor);return;
    }
#endif
#ifdef AF_V3_ROOM_REVERSIBLE
    if (r->mode==ROOM_RIG_REVERSIBLE) {
        af_v3_room_reverse_ct(actor,skeleton,animation,r->first.f);
        /* N64 captures switch flags before destruction, unlike the donor.
           Keep its persistence input equal to the accepted internal state. */
        af_v3_room_reverse_dt(actor);return;
    }
#endif
    cKF_SkeletonInfo_R_ct(&actor->keyframe,skeleton,animation,actor->joint,actor->morph);
#ifdef AF_V3_ROOM_RIG_PACKET
    if (r->mode==ROOM_RIG_STORAGE || r->mode==ROOM_RIG_HIT ||
            (r->mode==ROOM_RIG_JOINT && r->first.bits==4))
        cKF_SkeletonInfo_R_init_standard_stop(&actor->keyframe,animation,(void *)0);
    else
#endif
        cKF_SkeletonInfo_R_init_standard_repeat(&actor->keyframe,animation,(void *)0);
#ifdef AF_V3_ROOM_EMBEDDED
    if (r->mode==ROOM_RIG_EMBEDDED) {
        actor->keyframe.speed.f=0.5f;
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        return;
    }
#endif
    if (r->joints<=6) {actor->speed.bits=0;actor->target.bits=0x3F000000u;}
#ifdef AF_V3_ROOM_JOINT
    if (r->mode==ROOM_RIG_JOINT) { af_v3_room_joint_ct(actor,r);return; }
#endif
#ifdef AF_V3_ROOM_ROLLING
    if (r->mode==ROOM_RIG_ROLLING) {
        actor->keyframe.speed.f=0.5f;
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        actor->keyframe.speed.f=0.0f;
        actor->speed.f=actor->position[0];actor->target.f=actor->position[2];
        return;
    }
#endif
#ifdef AF_V3_ROOM_RIG_PACKET
    if (r->mode==ROOM_RIG_HIT) {
        /* The donor initializer supplies .5; the native one supplies 1.
           Preserve the donor's first evaluation before stopping the motion. */
        actor->keyframe.speed.bits=0x3F000000u;
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        actor->keyframe.speed.bits=r->first.bits==2 ? 0x3F000000u : 0;
        if (!r->first.bits) actor->changed=0;
        return;
    }
#endif
    actor->keyframe.speed.bits=0;
#ifdef AF_V3_ROOM_RIG_PACKET
    if (r->mode==ROOM_RIG_CLOCK || r->mode==ROOM_RIG_BILLBOARD || r->mode==ROOM_RIG_MATERIAL)
        actor->keyframe.speed.bits=0x3F000000u;
#endif
    cKF_SkeletonInfo_R_play(&actor->keyframe);
}

void af_v3_room_rig_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    FloatWord high,idle,step;
    (void)room;(void)game;
    const RoomRigRecord *r=find(actor->index);
    if (!data || !r) return;
#ifdef AF_V3_ROOM_EMBEDDED
    if (r->mode==ROOM_RIG_EMBEDDED) {
        /* Generic source motion runs even while an item appears/disappears.
           The native owner dispatch must preserve that when profiles enable. */
        for (u32 i=0;i<2;++i) {
            cKF_SkeletonInfo_R_play(&actor->keyframe);
            actor->keyframe.speed.f=0.5f;
        }
        return;
    }
#endif
#ifdef AF_V3_ROOM_MUSIC
    if (r->mode==ROOM_RIG_RADIO) {
        af_v3_room_music_native_move(actor,room);
        af_v3_room_radio_notes(actor,game,AF_ROOM_RADIO_SOURCE_ITEM);return;
    }
#endif
#ifdef AF_V3_ROOM_DUAL_MOTION
    if (r->mode==ROOM_RIG_DUAL) {
        RoomDualMotion motion;
        if (!af_v3_room_dual_resolve(r,data,&motion)) return;
        int front=af_v3_room_dual_front();
        af_v3_room_dual_step(actor,&motion,actor->changed,front);
        af_v3_room_dual_step(actor,&motion,0,front);
        af_v3_room_dual_dt(actor);return;
    }
#endif
#ifdef AF_V3_ROOM_EFFECT_RIG
    if (r->mode==ROOM_RIG_EFFECT) {
        const RoomEffectRigParams *p=af_v3_room_effect_rig_params(r,data);
        if (!p) return;
        af_v3_room_effect_rig_step(actor,game,p,actor->changed);
        af_v3_room_effect_rig_step(actor,game,p,0);
        af_v3_room_reverse_dt(actor);return;
    }
#endif
#ifdef AF_V3_SELECTED_PALETTE
    if (r->mode==ROOM_RIG_ROOF) { af_v3_roof_mv(actor,room,game,data);return; }
#endif
#ifdef AF_V3_ROOM_RIG_PACKET
#if defined(AF_V3_ROOM_REVERSIBLE) && defined(AF_V3_ROOM_TRIGGER_SOUND)
    if (r->mode==ROOM_RIG_REVERSIBLE) {
        const RoomSoundRecord *sound=sound_record(actor->index);
        if (!sound) return;
        af_v3_room_reverse_step(actor,r->first.f,sound->word,actor->changed);
        af_v3_room_reverse_step(actor,r->first.f,sound->word,0);
        af_v3_room_reverse_dt(actor);
        return;
    }
#endif
#ifdef AF_V3_ROOM_MATERIAL_RIG
    if (r->mode==ROOM_RIG_MATERIAL) {
        const RoomRigMaterial *p=rig_material(r,data);
        if (!p) return;
        actor->keyframe.speed.f=1.0f;
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        sAdo_OngenPos((u32)(uptr)actor,p->sound,actor->position);
        return;
    }
#endif
#ifdef AF_V3_ROOM_JOINT
    if (r->mode==ROOM_RIG_JOINT) { af_v3_room_joint_mv(actor,r);return; }
#endif
#ifdef AF_V3_ROOM_ROLLING
    if (r->mode==ROOM_RIG_ROLLING) { rolling_move(actor,r);return; }
#endif
#ifdef AF_V3_ROOM_BILLBOARD
    if (r->mode==ROOM_RIG_BILLBOARD) {
        const RoomBillboard *p=Lib_SegmentedToVirtual((void *)(uptr)r->first.bits);
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        actor->keyframe.speed.bits=0x3F000000u;
        if (!p->suppress_states || !room_transition_state(actor->state))
            sAdo_OngenPos((u32)(uptr)actor,p->sound,actor->position);
        return;
    }
#endif
#ifdef AF_V3_ROOM_TRIGGER_SOUND
    if (r->mode==ROOM_RIG_HIT) {
        RoomKeyframe *key=&actor->keyframe;
#ifdef AF_V3_ROOM_EFFECTS
        if (r->first.bits==2) {
            if (cKF_SkeletonInfo_R_play(key)!=1) {
                cKF_SkeletonInfo_R_play(key);key->speed=r->last;
            } else if (actor->changed) {
                if (!room_transition_state(actor->state)) {
                    trigger(actor->index,actor->position);
                    trigger_conditional(actor,game);
                }
                key->current.f=1.0f;
                cKF_SkeletonInfo_R_play(key);key->speed=r->last;
            }
            return;
        }
#endif
        if (r->first.bits) {
            if (!(key->speed.bits&0x7FFFFFFFu)) {
                if (actor->changed) {
                    if (!room_transition_state(actor->state)) trigger(actor->index,actor->position);
                    key->current.f=1.0f;
                    cKF_SkeletonInfo_R_play(key);key->speed=r->last;
                }
            } else if (cKF_SkeletonInfo_R_play(key)!=1) {
                cKF_SkeletonInfo_R_play(key);key->speed=r->last;
            } else key->speed.bits=0;
            return;
        }
        if (cKF_SkeletonInfo_R_play(key)!=1 && (key->speed.bits&0x7FFFFFFFu)) {
            cKF_SkeletonInfo_R_play(key);
            key->speed.bits=0x3F000000u;
        }
        if (actor->changed) {
            if (!room_transition_state(actor->state))
                trigger(actor->index,actor->position);
            key->current.bits=0x3F800000u;
            cKF_SkeletonInfo_R_play(key);
            key->speed.bits=0x3F000000u;
        }
        return;
    }
#endif
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
    if (!actor || !game || !game->gfx || !data) return;
    const RoomRigRecord *r=find(actor->index);
    if (!r) return;
#ifdef AF_V3_ROOM_MUSIC
    if (r->mode==ROOM_RIG_RADIO) {
        af_v3_room_radio_draw(actor,game,r->first.bits,r->last.bits);return;
    }
#endif
#ifdef AF_V3_ROOM_DUAL_MOTION
    if (r->mode==ROOM_RIG_DUAL) {
        RoomDualMotion motion;
        if (!af_v3_room_dual_resolve(r,data,&motion)) return;
        /* Checked native scenes have no basement or island cottage. Their
           source-only darkness condition cannot hold in these rooms. */
        af_v3_room_dual_dw(actor,game,r->shown,0);return;
    }
#endif
#ifdef AF_V3_ROOM_EFFECT_RIG
    if (r->mode==ROOM_RIG_EFFECT) {
        const RoomEffectRigParams *p=af_v3_room_effect_rig_params(r,data);
        if (p) af_v3_room_effect_rig_dw(actor,game,r,p,data);
        return;
    }
#endif
#ifdef AF_V3_SELECTED_PALETTE
    if (r->mode==ROOM_RIG_ROOF) {
        const u16 *layout=(const u16 *)data;
        if (((uptr)data&7) || layout[2]!=r->bytes || layout[3]!=3) return;
        af_v3_roof_dw(actor,room,game,data);return;
    }
#endif
#ifdef AF_V3_ROOM_JOINT
    if (r->mode==ROOM_RIG_JOINT) { af_v3_room_joint_dw(actor,game,r);return; }
#endif
#ifdef AF_V3_ROOM_BILLBOARD
    if (r->mode==ROOM_RIG_BILLBOARD) {
        af_v3_room_billboard_dw(actor,room,game,r,Lib_SegmentedToVirtual((void *)(uptr)r->first.bits));
        return;
    }
#endif
    u32 prefix=1;
#ifdef AF_V3_ROOM_MATERIAL_RIG
    const RoomRigMaterial *material=0;
    if (r->mode==ROOM_RIG_MATERIAL) {
        material=rig_material(r,data);
        if (!material) return;
        prefix=2;
    }
#endif
    RoomRigGraphics *gfx=game->gfx;
    RoomCommand *commands=gfx->head;
    uptr front=(uptr)commands,back=(uptr)gfx->tail;
    uptr xlu=(uptr)gfx->xlu_head,xlu_back=(uptr)gfx->xlu_tail;
    u32 xlu_bytes=8,matrix_bytes=64;
#ifdef AF_V3_ROOM_EMBEDDED
    /* Profile-owned skeletons can contain translucent joints. Their source
       drawer supplies a parent matrix and enough command space in both lists. */
    if (r->mode==ROOM_RIG_EMBEDDED) {
        xlu_bytes=(2u+2u*r->shown)*8u;matrix_bytes=128;
    }
#endif
    /* Parent matrix plus the skeleton's segment, matrix, and list commands.
       Both joint callbacks are verified no-ops in this source category. */
    /* Native graph allocations are eight-byte aligned. A valid tail ending
       in eight must not suppress an entire room model. */
    if (!front || !back || !xlu || !xlu_back || (front&7) || (back&7) || (xlu&7) || back<front ||
            back-front<matrix_bytes+(prefix+1u+2u*r->shown)*8u ||
            xlu_back<xlu || xlu_back-xlu<xlu_bytes) return;
    gfx->head=commands+prefix;
    commands[0]=(RoomCommand){0xDA380003,(u32)(uptr)_Matrix_to_Mtx_new(gfx)};
#ifdef AF_V3_ROOM_EMBEDDED
    if (r->mode==ROOM_RIG_EMBEDDED) {
        RoomCommand *parent=gfx->xlu_head++;
        /* Native matrix allocation uses the opaque tail for both streams. */
        *parent=(RoomCommand){0xDA380003,(u32)(uptr)_Matrix_to_Mtx_new(gfx)};
    }
#endif
#ifdef AF_V3_ROOM_MATERIAL_RIG
    if (material) {
        u32 frame=((game->frame*2u)/rig_frame_u16(material->divisor))%material->frames;
        commands[1]=(RoomCommand){0xDB060000u+4u*material->segment,
            (u32)(uptr)(data+rig_frame_u16(material->offsets[frame]))&0x1FFFFFFFu};
    }
#endif
    cKF_Si3_draw_R_SV(game,&actor->keyframe,actor->matrices[game->frame&1],
#ifdef AF_V3_ROOM_RIG_PACKET
                    r->mode==ROOM_RIG_CLOCK ? (void *)clock_before : (void *)0,(void *)0,
                    r->mode==ROOM_RIG_MATERIAL ? (void *)actor : r->mode==ROOM_RIG_REVERSIBLE ? (void *)0 : (void *)r);
#else
                    (void *)0,(void *)0,(void *)0);
#endif
}

#if defined(AF_V3_ROOM_REVERSIBLE) || defined(AF_V3_ROOM_MUSIC)
void af_v3_room_rig_dt(RoomRig *actor,u8 *data) {
    if (!actor || !data) return;
    const RoomRigRecord *r=find(actor->index);
#ifdef AF_V3_ROOM_MUSIC
    if (r && r->mode==ROOM_RIG_RADIO) { af_v3_room_music_native_radio_dt(actor);return; }
#endif
#ifdef AF_V3_ROOM_DUAL_MOTION
    if (r && r->mode==ROOM_RIG_DUAL) {
        RoomDualMotion motion;
        if (af_v3_room_dual_resolve(r,data,&motion)) af_v3_room_dual_dt(actor);
        return;
    }
#endif
#ifdef AF_V3_ROOM_REVERSIBLE
    if (r && (r->mode==ROOM_RIG_REVERSIBLE || r->mode==ROOM_RIG_EFFECT || r->mode==ROOM_RIG_DUAL)) af_v3_room_reverse_dt(actor);
#endif
}
#endif
