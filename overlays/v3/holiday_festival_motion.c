/* Complete resident NPC motions, including expression programmes. Imported
 * sequence IDs never index the native animation/bank directory. Native hand
 * and talking motions retain their ordinary bank references and release path. */
#include "holiday_festival.h"
typedef struct {
    u32 arrays[4];s16 unused,duration;f32 start,end;u32 mode;f32 morph;
    const u8 *eye;s16 eye_type,eye_stop;const u8 *mouth;
    s16 mouth_type,mouth_stop,effect_frame,effect_type;const void *effect,*sound;
} Motion;
typedef struct {u32 index;const Motion *motion;} MotionRow;
extern const struct {u32 count;MotionRow rows[];} af_hg_motions;
extern const u32 *volatile af_hp_native_npc_clip;
extern const AFHPEffects *volatile af_hp_native_effects;
extern volatile u32 af_hp_native_segments[16];
extern int af_holiday_observers_clip(void);
extern void af_hg_previous_animation(ACTOR *,int,int);
extern void *af_hg_native_segment(const void *);
extern void af_holiday_keyframe_init(void *,void *,const void *,f32,f32,f32,f32,f32,int,void *);
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
#define WORD(a,at) (*(u32 *)((u8 *)(a)+(at)))
#define BYTE(a,at) (((u8 *)(a))[at])
#ifdef __mips__
_Static_assert(sizeof(Motion)==64,"Complete resident motion header");
#endif
static u32 entry(u32 at) {
    return af_hp_native_npc_clip[0x108/4]+at-0x8097F0BCu;
}
static const Motion *motion(int id) {
    for(u32 i=0;i<af_hg_motions.count;i++)
        if(af_hg_motions.rows[i].index==(u32)id)return af_hg_motions.rows[i].motion;
    return 0;
}
static const Motion *submotion(ACTOR *actor,void *owner,u32 frame,int id,const Motion *main) {
    WORD(actor,frame+0x1B4)=0;
    BYTE(actor,frame+0x1B8)=255; /* Native release ignores bank index -1. */
    if(id<0)return main;
    /* Slot 234 is the native talking-mouth record, outside the ordinary
     * 0..233 sequence range but inside the complete resident directory. */
    if(id>234)return 0;
    const void *info=(const void *)(entry(0x80981974)+(u32)id*8);
    s8 bank=FN(entry(0x80974610),s8,void *,const void *,u32 *)(
        owner,info,&WORD(actor,frame+0x1B4));
    BYTE(actor,frame+0x1B8)=(u8)bank;
    if(bank<0)return 0;
    af_hp_native_segments[6]=WORD(actor,frame+0x1B4)+0x80000000u;
    return af_hg_native_segment(*(const void *const *)info);
}
void af_hg_animation(ACTOR *actor,int id,int talk) {
    if(!actor || !af_hp_owned(actor) || !af_hp_native_npc_clip || !af_holiday_observers_clip()) {
        af_hg_previous_animation(actor,id,talk);return;
    }
    /* Native TALK/WAIT requests can resolve to an imported default motion. */
    int resolved=FN(entry(0x809747BC),int,ACTOR *,int)(actor,id);
    if(resolved<256) {af_hg_previous_animation(actor,id,talk);return;}
    const Motion *main=motion(resolved);
    if(!main) {Actor_delete(actor);return;}
    NPC_ACTOR *npc=(NPC_ACTOR *)actor;
    f32 current=npc->draw.animation_id==resolved?
        npc->draw.main_animation.keyframe.frame_control.current_frame:main->start;
    void *owner=*(void **)entry(0x80981970);
    if(!owner) {Actor_delete(actor);return;}
    int hand=-1;
    if(BYTE(actor,0x729)) {
        unsigned int type=BYTE(actor,0x729);
        if(type>2) {Actor_delete(actor);return;}
        hand=((const int *)entry(0x809821A4))[type];
    }
    /* Release all three previous references once, even when the next motion
     * has no native bank. A shared hand/mouth bank retains both references. */
    FN(entry(0x809742A0),void,void *,ACTOR *)(owner,actor);
    const Motion *motions[3];
    motions[0]=submotion(actor,owner,0x198,-1,main);
    motions[1]=submotion(actor,owner,0x354,hand,main);
    motions[2]=submotion(actor,owner,0x510,npc->talk_info.type?234:-1,main);
    if(!motions[1] || !motions[2]) {Actor_delete(actor);return;}
    static const u16 frames[]={0x198,0x354,0x510};
    for(unsigned int i=0;i<3;i++) {
        u8 *frame=(u8 *)actor+frames[i];const Motion *m=motions[i];
        af_hp_native_segments[6]=WORD(actor,frames[i]+0x1B4)+0x80000000u;
        af_holiday_keyframe_init(frame,*(void **)(frame+0x18),m,m->start,m->end,
            i?m->start:current,npc->draw.frame_speed,m->morph,(int)m->mode,0);
    }
    *(const u8 **)((u8 *)actor+0x714)=main->eye;
    BYTE(actor,0x70C)=(u8)main->eye_type;BYTE(actor,0x712)=(u8)main->eye_stop;
    *(const u8 **)((u8 *)actor+0x720)=main->mouth;
    BYTE(actor,0x718)=(u8)main->mouth_type;BYTE(actor,0x71E)=(u8)main->mouth_stop;
    const AFHPEffects *effects=af_hp_native_effects;
    if(npc->draw.effect_type!=-1 && npc->draw.effect_type!=main->effect_type &&
       effects && effects->effect_kill_proc)effects->effect_kill_proc(npc->draw.effect_type,actor->npc_id);
    npc->draw.effect_type=main->effect_type;npc->draw.effect_pattern=main->effect_frame;
    *(const void **)((u8 *)actor+0x730)=main->effect;
    AFHPFrame *mouth=(AFHPFrame *)((u8 *)actor+0x510);
    mouth->speed=1.0f;
    if(!main->mouth_type && !main->mouth && talk!=1) {mouth->current_frame=1.0f;mouth->speed=0.0f;}
    npc->draw.animation_id=resolved;
    WORD(actor,0x188)=0;WORD(actor,0x190)=0;WORD(actor,0x194)=0;
    WORD(actor,0x18C)=1;
    npc->draw.main_animation_frame=(u32)npc->draw.main_animation.keyframe.frame_control.current_frame;
    /* The converted records have no separate audio programme. Clear the same
     * complete 0x38-byte audio state as the original initializer's null arm. */
    bzero((u8 *)actor+0x6CC,0x38);
}
