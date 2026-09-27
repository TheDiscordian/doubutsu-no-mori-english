/* Donor coastal patrol on native actor fields. Source 60-Hz counters/phase
 * increments are converted to the N64 30-Hz update; actor sizes stay unchanged.
 * The original functions remain callable for the explicit native alternative.
 */
#include "creature_water.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef short s16;
typedef unsigned int u32;
#define H(p,n) (*(s16 *)((u8 *)(p)+(n)))
#define U(p,n) (*(u16 *)((u8 *)(p)+(n)))
#define W(p,n) (*(int *)((u8 *)(p)+(n)))
#define F(p,n) (*(float *)((u8 *)(p)+(n)))
#ifdef __mips__
const u32 af_v3_fish_patrol_mode=0;
#else
extern u32 af_v3_fish_patrol_mode;
#endif
extern float af_patrol_random(void),af_patrol_random2(void),af_patrol_sin(s16);
extern int af_patrol_chase_angle(s16 *,s16,s16),af_patrol_chase_float(float *,float,float);
extern int af_patrol_player_near(void *,void *),af_patrol_search(void *,void *);
extern void af_patrol_setup(void *,int);
extern void af_patrol_old_swim(void *,void *),af_patrol_old_wait(void *,void *);
extern void af_patrol_old_escape(void *,void *);
extern void af_patrol_old_swim_init(void *),af_patrol_old_wait_init(void *),af_patrol_old_escape_init(void *);
static int donor(void *actor) {
    return ((u8 *)actor)[0x1DA] && *(volatile const u32 *)&af_v3_fish_patrol_mode==1;
}
static int uki(void *actor,void *game) {
    if (!af_patrol_player_near(actor,game) && af_patrol_search(actor,game)) {
        af_patrol_setup(actor,3);return 1;
    }
    return 0;
}
static int timer(void *actor) {
    if (W(actor,0x214)>0) W(actor,0x214)--;
    return W(actor,0x214);
}
static int speed(void *actor,float target,float amplitude) {
    int done=af_patrol_chase_float((float *)((u8 *)actor+0x224),target,5.0f);
    s16 angle=(s16)(int)(F(actor,0x224)*(65536.0f/360.0f));
    F(actor,0x74)=amplitude*af_patrol_sin(angle);return done;
}
void af_v3_patrol_swim_init(void *actor) {
    if (!donor(actor)) {af_patrol_old_swim_init(actor);return;}
    switch (((u8 *)actor)[0x23E]) {
    case 0:F(actor,0x224)=50.0f;break;
    case 1:
        F(actor,0x224)=0.0f;
        H(actor,0x36)=(s16)(H(actor,0x36)+(int)(af_patrol_random2()*32768.0f));break;
    case 2:
        H(actor,0x22E)=(s16)(H(actor,0x36)+(int)(af_patrol_random2()*16384.0f));
        H(actor,0xDE)=H(actor,0x36);break;
    case 3: {
        F(actor,0x224)=5.0f;
        s16 angle=(s16)((H(actor,0xDE)>0?16384:-16384)-H(actor,0x36));
        H(actor,0x22C)=(s16)(angle/36);break;
    }
    }
}
void af_v3_patrol_wait_init(void *actor) {
    if (!donor(actor)) {af_patrol_old_wait_init(actor);return;}
    U(actor,0x23C)&=(u16)~2u;
    W(actor,0x214)=(int)(100.0f+af_patrol_random()*30.0f);
    F(actor,0x74)=-0.15f+af_patrol_random2()*0.2f;F(actor,0x7C)=0.0f;
}
void af_v3_patrol_escape_init(void *actor) {
    if (!donor(actor)) {af_patrol_old_escape_init(actor);return;}
    H(actor,0x228)=0;W(actor,0x214)=50;F(actor,0x74)=1.0f;
}
void af_v3_patrol_swim(void *actor,void *game) {
    if (!donor(actor)) {af_patrol_old_swim(actor,game);return;}
    if (af_v3_water_wall(actor)) {af_patrol_setup(actor,2);return;}
    unsigned kind=((u8 *)actor)[0x23E];int done=0;
    switch (kind) {
    case 0:done=speed(actor,360.0f,0.5f);break;
    case 1:
        done=speed(actor,180.0f,0.5f);
        if (done) H(actor,0x36)=H(actor,0xDE);
        break;
    case 2: {
        int turned=af_patrol_chase_angle((s16 *)((u8 *)actor+0x36),H(actor,0x22E),0x400);
        H(actor,0xDE)=H(actor,0x36);
        if (turned) {((u8 *)actor)[0x23E]=3;af_v3_patrol_swim_init(actor);return;}
        break;
    }
    case 3:
        H(actor,0xDE)=(s16)(H(actor,0xDE)+H(actor,0x22C)*2);
        done=speed(actor,180.0f,1.0f);
        if (done) H(actor,0x36)=H(actor,0xDE);
        break;
    default:af_patrol_setup(actor,1);return;
    }
    if (done) af_patrol_setup(actor,1);
    else uki(actor,game);
}
void af_v3_patrol_wait(void *actor,void *game) {
    if (!donor(actor)) {af_patrol_old_wait(actor,game);return;}
    if (!timer(actor)) {
        F(actor,0x74)=F(actor,0x7C)=0;
        unsigned roll=(unsigned)(af_patrol_random()*3.0f);
        ((u8 *)actor)[0x23E]=(roll==1); /* Source sequence: SWIM, SWIM2, SWIM. */
        af_patrol_setup(actor,0);
    } else if (af_v3_water_wall(actor)) af_patrol_setup(actor,2);
    else uki(actor,game);
}
void af_v3_patrol_escape(void *actor,void *game) {
    if (!donor(actor)) {af_patrol_old_escape(actor,game);return;}
    if (!uki(actor,game) && ((U(actor,0x23C)&0x40u) || !af_v3_water_wall(actor))) {
        if (!timer(actor)) {U(actor,0x23C)&=(u16)~0x40u;af_patrol_setup(actor,1);}
        else af_patrol_chase_float((float *)((u8 *)actor+0x74),0.0f,0.02f);
    }
}
