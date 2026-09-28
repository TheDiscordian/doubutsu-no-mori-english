/* Complete cane blending and walking-only decisions for the additive actor.
 * Original NPCs retain the exact original entries and animation bank ownership. */
#include "holiday_motion.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
#define BYTE(a,o) (((u8 *)(a))[o])
#define SHORT(a,o) (*(short *)((u8 *)(a)+(o)))
#define WORD(a,o) (*(u32 *)((u8 *)(a)+(o)))
#define REAL(a,o) (*(float *)((u8 *)(a)+(o)))
static int owned(const void *a) {
    const AFNpcExtra *r=af_v3_npc_extra_owned(a);
    return r && r->name==0xD090 && r->profile==0xCC && r->actor_bytes>=sizeof(AFHolidayNpc);
}
static int walking(void *a) {
    if(!owned(a))return 0;
    AFHolidayNpc *n=a;
    return n->constructed && !n->failed && (n->actor.think==3 || n->actor.think==4);
}
void af_holiday_motion_animation(void *a,int index,int talk) {
    int cane=owned(a) && BYTE(a,0x729)==3;
    /* The native table has no subtype three. Keep its main/face motion and all
     * three native bank reference counts; replace only the cane's keyframe.
     * The animation entry hook covers both clip calls and internal direct calls. */
    if(cane)BYTE(a,0x729)=0;
    af_holiday_animation_original(a,index,talk);
    if(cane) {
        BYTE(a,0x729)=3;
        af_holiday_keyframe_init((u8 *)a+0x354,(void *)(uptr)WORD(a,0x36C),
            &af_holiday_cane,af_holiday_cane.start,af_holiday_cane.end,
            af_holiday_cane.start,REAL(a,0x73C),af_holiday_cane.morph,af_holiday_cane.mode,0);
        WORD(a,0x190)=0;
    }
}
void af_holiday_motion_decide(void *a) {
    if(!walking(a)) {af_holiday_wander_original(a);return;}
    u16 args[6]={0};u8 action=0,type=0;
    if(af_holiday_fatigue(a)==1 || af_holiday_mood(a)==4) {
        /* No random number or destination query in this branch. */
    } else if(BYTE(a,0x7C5)==3) {
        AFHolidayPosition p={(float)SHORT(a,0x7CC),0,(float)SHORT(a,0x7CE)};
        if(!BYTE(a,0x910) && af_holiday_range(a,0,p,BYTE(a,0x8CF))==1) {
            args[2]=(u16)SHORT(a,0x7CC);args[3]=(u16)SHORT(a,0x7CE);action=1;type=3;
        }
    } else if((int)(af_holiday_random_native()*10.0f)<=5) {
        if(af_holiday_move_next(args,a)) {
            action=af_holiday_ones_way(a,args)==1?3:1;type=3;
        }
    }
    af_holiday_request_native(a,1,action,type,args);
}
void af_holiday_motion_wander_init(void *a,void *game) {
    if(walking(a)) {
        AFHolidayPosition p={REAL(a,0x28),REAL(a,0x2C),REAL(a,0x30)};
        int x,z;af_holiday_unit(&x,&z,p);
        if(x==0 || x==15 || z==0 || z==15) {
            /* The donor refreshes home/block bounds when starting on an edge.
             * Keep the native home height; only X/Z are changed by the donor. */
            REAL(a,0x0C)=p.x;REAL(a,0x14)=p.z;
            p.y=REAL(a,0x10);af_holiday_block(&x,&z,p);
            BYTE(a,8)=x;BYTE(a,9)=z;BYTE(a,0x8CF)=0;
            REAL(a,0x8D0)=(0.5f+(signed char)BYTE(a,8))*640.0f;
            REAL(a,0x8D4)=(0.5f+(signed char)BYTE(a,9))*640.0f;
        }
    }
    /* Clears demo/force-call flags and requests WAIT with native priority one. */
    af_holiday_wander_init_original(a,game);
}
static void walk_wander(void *context) {
    AFHolidayNpc *a=context;af_holiday_schedule_native(a,a->game,4);
}
static void motion(void *context,AFHolidayMotion *m) {
    *m=(AFHolidayMotion){.clapping=WORD(context,0x704)==0x43};
}
static void repeat(void *context,int clap) {
    WORD(context,0x1AC)=1;
    af_holiday_motion_animation(context,clap?0x43:5,0);
}
static void clap_sound(void *context) {
    af_holiday_sound_native((u32)(uptr)context,0x2F,(u8 *)context+0x28);
}
static u32 random_bounded(void *context,u32 bound) {
    (void)context;return (u32)(af_holiday_random_native()*(float)bound);
}
int af_holiday_motion_bind(AFHolidayNpc *a) {
    if(!owned(a))return 0;
    a->ops.motion=motion;a->ops.walk_wander=walk_wander;
    a->ops.repeat_animation=repeat;a->ops.clap_sound=clap_sound;
    a->ops.random=random_bounded;return 1;
}
int af_holiday_motion_resources(AFHolidayNpc *a) {
    if(!owned(a) || !a->constructed || a->failed)return 0;
    BYTE(a,0x729)=3;
    af_holiday_motion_animation(a,(int)WORD(a,0x704),0);
    return 1;
}
