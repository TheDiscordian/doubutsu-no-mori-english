/* Native bindings for the shared complete player-exercise category. */
#include "player_exercise_native.h"
typedef unsigned int u32;
typedef unsigned char u8;
typedef unsigned short u16;
#define WORD(p,n) (*(int *)((u8 *)(p)+(n)))
#define REAL(p,n) (*(float *)((u8 *)(p)+(n)))
#ifdef __mips__
#define MEMORY(a) ((void *)(a))
static void *resolve(u32 address) {
    if (address >= 0x808B2D50u)
        address += *(u32 *)0x80143900u - 0x808DD748u;
    return (void *)address;
}
#else
#define MEMORY(a) af_test_exercise_memory(a)
#define resolve af_test_exercise_resolve
#endif
#define FN(a,r,...) ((r (*)(__VA_ARGS__))resolve(a))
#define STATE(p) ((AFExercise *)((u8 *)(p)+AF_EXERCISE_STATE_OFFSET))

unsigned int af_v3_exercise_native_clock(void) {
    return *(volatile u32 *)MEMORY(0x8014BDA0u);
}

int af_v3_exercise_native_tempo(int *tempo) {
    u8 handle=*(volatile u8 *)MEMORY(0x80113848u);
    /* The engine's configured count, not the GC group layout or a guessed
       fixed number of sequence players, bounds this read. */
    u16 count=*(volatile u16 *)MEMORY(0x8014BD60u);
    if (handle >= count) return -1;
    volatile u8 *group=MEMORY(0x8014CB90u+(u32)handle*0x160u);
    if (!(group[0]&0x80) || group[4]!=181) return -1;
    *tempo=*(volatile u16 *)(group+8)/48;
    return 0;
}

int af_v3_exercise_native_able(void *actor) {
    if (*(signed char *)((u8 *)actor+0x1117)>=0) return 0;
    /* Preserve GAFE01-r0's event-first condition, including its indoor
       restriction during an active aerobics event. Native calendar IDs differ. */
    if (FN(0x8007FF08u,int,int,int)(16,16) ||
            FN(0x8007FF08u,int,int,int)(8,16)) {
        int bx,bz,px,pz;
        if (!FN(0x80089440u,int,int *,int *,int)(&bx,&bz,4)) return 0;
        /* Native xyz_t is passed by value (three floats), not by pointer. */
        typedef struct {float x,y,z;} Position;
        Position position=*(Position *)((u8 *)actor+0x28);
        return FN(0x80088710u,int,int *,int *,Position)(&px,&pz,position) && px==bx && pz==bz;
    }
    return *(u8 *)MEMORY(0x80136EA1u)!=0 && FN(0x8005EAFCu,int,void)()==27;
}

int af_v3_exercise_native_input(void *actor,void *game) {
    int forbidden=FN(0x8007D90Cu,int,void)() ||
        *(signed char *)((u8 *)actor+0x1117)>=0 ||
        FN(0x808B32C4u,float,void)()!=0.0f ||
        FN(0x808B2D50u,int,void *)(game) || FN(0x808B3010u,int,void *)(game);
    u32 held=0;
    if (!forbidden) for (u32 mask=1;mask<=8;mask<<=1)
        if (FN(0x80078D30u,int,int)((int)mask)) held|=mask;
    return af_v3_exercise_buttons(held,forbidden);
}

typedef struct {void *actor,*game;} Context;
static int request(void *opaque,int command,float speed,int priority) {
    Context *c=opaque;
    if (!FN(0x808B8874u,int,void *,int,int)(c->game,111,priority)) return 0;
    WORD(c->actor,0xD58)=command;
    REAL(c->actor,0xD5C)=speed;
    FN(0x808B3334u,void,void *,int,int)(c->game,111,priority);
    return 1;
}
static void wait_request(void *opaque,float morph,int flags,int priority) {
    Context *c=opaque;
    FN(0x808C1064u,int,void *,float,int,int)(c->game,morph,flags,priority);
}
static void settle(void *opaque) {
    Context *c=opaque; FN(0x808B3648u,void,void *)(c->actor);
}
static void bee(void *opaque) {
    Context *c=opaque; FN(0x808B3AF0u,void,void *,int)(c->actor,1);
}
static AFExerciseCalls callbacks(Context *context) {
    AFExerciseCalls calls={context,request,wait_request,settle,bee};
    return calls;
}

void af_v3_exercise_native_init(void *actor,void *game) {
    /* This checked predecessor includes the native constructor and the flying
       balloon lifetime initialization. Never replace the profile ctor pointer. */
    FN(AF_EXERCISE_PRIOR_INIT,void,void *,void *)(actor,game);
    af_v3_exercise_init(STATE(actor),af_v3_exercise_native_clock());
}
void af_v3_exercise_native_after(void *actor,void *game) {
    FN(0x808BD218u,void,void *,void *)(actor,game);
    STATE(actor)->old_sound_frame=af_v3_exercise_native_clock();
}
int af_v3_exercise_native_camera(void *actor) {
    if (af_v3_exercise_native_able(actor)) return 0;
    return FN(0x808BBDE8u,int,void *)(actor);
}
void af_v3_exercise_native_wait_setup(void *actor,void *game) {
    af_v3_exercise_wait_setup(STATE(actor),WORD(actor,0xD5C));
    FN(0x808C1118u,void,void *,void *)(actor,game);
}
void af_v3_exercise_native_wait(void *actor,void *game) {
    AFExercise *s=STATE(actor);Context context={actor,game};
    AFExerciseCalls calls=callbacks(&context);
    int able=af_v3_exercise_native_able(actor);
    int command=af_v3_exercise_native_input(actor,game);
    /* Two source recognition ticks, but only one native physics/collision
       update. Keep the actual request after the native WAIT priority checks. */
    af_v3_exercise_input(s,able,command);
    af_v3_exercise_check(s,af_v3_exercise_patterns,able,1,&calls);
    af_v3_exercise_input(s,able,command);
    FN(0x808C1370u,void,void *,void *)(actor,game);
    af_v3_exercise_check(s,af_v3_exercise_patterns,able,0,&calls);
}
void af_v3_exercise_native_setup(void *actor,void *game) {
    float speed=REAL(actor,0xD5C);
    u32 animation=af_v3_exercise_setup(STATE(actor),af_v3_exercise_patterns,WORD(actor,0xD58));
    FN(0x808B4A44u,void,void *,void *,int,int,float,float,float,float,int,int)
        (actor,game,(int)animation,(int)animation,1.0f,1.0f,0.0f,-5.0f,0,0);
    REAL(actor,0x180)=REAL(actor,0x1F0)=speed;
    FN(0x808B3BD0u,void,void *,void *)(actor,game);
}
void af_v3_exercise_native_main(void *actor,void *game) {
    AFExercise *s=STATE(actor);Context context={actor,game};
    AFExerciseCalls calls=callbacks(&context);
    int able=af_v3_exercise_native_able(actor);
    int command=af_v3_exercise_native_input(actor,game);
    int tempo=0,status=af_v3_exercise_native_tempo(&tempo);
    u32 now=af_v3_exercise_native_clock();
    u32 midpoint=s->old_sound_frame+(now-s->old_sound_frame)/2u;
    af_v3_exercise_input(s,able,command);
    FN(0x808B3C74u,void,void *)(actor);
    FN(0x808B61E4u,void,void *,void *)(actor,game);
    for (int step=0;step<2;++step) {
        if (step) af_v3_exercise_input(s,able,command);
        u32 clock=step ? now : midpoint;
        float speed=af_v3_exercise_speed(s,af_v3_exercise_patterns,REAL(actor,0x180),clock,status,tempo);
        REAL(actor,0x180)=REAL(actor,0x1F0)=speed;
        float last;
        int ended=FN(0x808B48F0u,int,void *,float *)(actor,&last);
        if (!step) {
            FN(0x808B5310u,void,void *)(actor);
            FN(0x808B36F4u,void,void *)(actor);
            FN(0x808B4DACu,void,void *,void *)(actor,game);
            FN(0x808B5FB0u,void,void *)(actor);
            FN(0x808BF410u,void,void *,void *)(actor,game);
        }
        af_v3_exercise_finish(s,af_v3_exercise_patterns,able,REAL(actor,0x184),
            REAL(actor,0x178),speed,ended,&calls);
        s->old_sound_frame=clock;
    }
}
