/* Source WALK_WANDER uses the native movement, collision, interruptions, and
 * pitfall transport, but keeps its actual 60% walk / 40% wait decision. Native
 * WANDER can run and is not a substitute for this schedule. */
#include "carried_event.h"
extern const u32 *volatile af_hp_native_npc_clip;
extern int af_holiday_observers_clip(void);
extern int af_cw_native_unit(int *,int *,xyz_t);
#define BYTE(a,o) (((u8 *)(a))[o])
#define WORD(a,o) (*(u32 *)((u8 *)(a)+(o)))
#define HALF(a,o) (*(s16 *)((u8 *)(a)+(o)))
#define FLOAT(a,o) (*(f32 *)((u8 *)(a)+(o)))
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))entry(at))
static NPC_ACTOR *walking;
static aNPC_SCHEDULE_PROC saved_schedule;
static u32 entry(u32 address) {return af_hp_native_npc_clip[0x108/4]+address-0x8097F0BCu;}
static int live(NPC_ACTOR *a,GAME *g) {
    return a && g && a->actor_class.npc_id==0xD0CD && af_hp_admit((ACTOR *)a,g) &&
        af_hp_native_npc_clip && af_holiday_observers_clip();
}
static void decide(NPC_ACTOR *a) {
    int action=0,type=0;u16 args[6]={0};
    if(FN(0x8097CBD0,int,NPC_ACTOR *)(a)==1 || FN(0x80974184,int,NPC_ACTOR *)(a)==4) {
        action=0;
    } else if(a->action.idx==3) {
        if(!a->collision.collision_flag) {
            xyz_t next={(f32)HALF(a,0x7CC),0,(f32)HALF(a,0x7CE)};
            if(FN(0x80976F74,int,NPC_ACTOR *,void *,xyz_t,int)(a,0,next,BYTE(a,0x8CF))==1) {
                args[2]=(u16)HALF(a,0x7CC);args[3]=(u16)HALF(a,0x7CE);
                action=1;type=3;
            }
        }
    } else {
        int roll=(int)(fqrand()*10.0f);
        if(roll<=5) {
            action=1;
            if(!FN(0x8097D520,int,u16 *,NPC_ACTOR *)(args,a))action=0;
            else {
                if(FN(0x8097D460,int,NPC_ACTOR *,u16 *)(a,args)==1)action=3;
                type=3;
            }
        }
    }
    FN(0x8097BF90,void,NPC_ACTOR *,int,int,int,u16 *)(a,1,action,type,args);
}
static void walk_schedule(NPC_ACTOR *a,GAME *g,int phase) {
    if(!live(a,g) || a!=walking || !saved_schedule)return;
    if(!phase) {
        FN(0x8097E8A0,void,NPC_ACTOR *,int)(a,0);
        int x,z;ACTOR *actor=(ACTOR *)a;
        af_cw_native_unit(&x,&z,actor->world.position);
        if(x==0 || x==15 || z==0 || z==15) {
            int bx,bz;
            actor->home.position.x=actor->world.position.x;
            actor->home.position.z=actor->world.position.z;
            mFI_Wpos2BlockNum(&bx,&bz,actor->home.position);
            actor->block_x=(s8)bx;actor->block_z=(s8)bz;
            BYTE(a,0x8CF)=0; /* native/source BLOCK movement range */
            FLOAT(a,0x8D0)=(bx+0.5f)*640.0f;
            FLOAT(a,0x8D4)=(bz+0.5f)*640.0f;
        }
        FN(0x8097E770,void,NPC_ACTOR *,GAME *,int)(a,g,1);
    } else if(phase==1) {
        if(WORD(a,0x798)==1) {
            if(!FN(0x8097D110,int,NPC_ACTOR *,GAME *)(a,g) && a->action.step==255)decide(a);
        } else FN(0x8097E7BC,void,NPC_ACTOR *,GAME *)(a,g);
        if(BYTE(a,0x79C)==1)FN(0x8097E770,void,NPC_ACTOR *,GAME *,int)(a,g,6);
    }
}
int af_cw_schedule(const ACTOR *actor) {
    if(!actor || actor->npc_id!=0xD0CD)return -1;
    const NPC_ACTOR *a=(const NPC_ACTOR *)actor;
    if(BYTE(a,0x7AC)!=4)return -1;
    return a==walking && a->schedule.schedule_proc==walk_schedule?5:6;
}
void af_cw_change_schedule(NPC_ACTOR *a,GAME *g,int source) {
    if(!live(a,g) || (source!=5 && source!=6))return;
    if(source==5) {
        if(a->schedule.schedule_proc!=walk_schedule) {
            saved_schedule=a->schedule.schedule_proc;walking=a;
            if(!saved_schedule)return;
            a->schedule.schedule_proc=walk_schedule;
        }
    } else if(a==walking && a->schedule.schedule_proc==walk_schedule) {
        if(!saved_schedule)return;
        a->schedule.schedule_proc=saved_schedule;walking=0;saved_schedule=0;
    }
    /* Both custom schedules use the native SPECIAL callback slot. Never put
     * donor schedule 5 or 6 into the native five-entry dispatch table. */
    FN(0x8097F0BC,void,NPC_ACTOR *,GAME *,int)(a,g,4);
}
