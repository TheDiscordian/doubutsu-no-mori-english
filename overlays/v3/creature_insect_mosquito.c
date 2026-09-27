/* Complete mosquito sting/notice actions on the existing native player ABI.
 * Transient data fits the native main/request unions; no player/save growth. */
#include "creature_insect_player.h"
#include "creature_insect_engine.h"
extern const void *af_insect_demo_clip;
#define WORD(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define REAL(p,n) (*(float *)((u8 *)(p)+(n)))
#define HALF(p,n) (*(s16 *)((u8 *)(p)+(n)))
#define FN(a,r,...) ((r (*)(__VA_ARGS__))af_insect_player_resolve(a))
enum { STUNG=107,NOTICE=108,RELAX_ROD=51,MOTION1=262,MOTION2=263,REPORT=9 };

static int request(void *actor,GAME *game,int action,u32 label,int priority) {
    if (!FN(0x808B8874u,int,GAME *,int,int)(game,action,priority)) return 0;
    WORD(actor,0xD58)=label;
    FN(0x808B3334u,void,GAME *,int,int)(game,action,priority);
    return 1;
}
int mPlib_request_main_stung_mosquito_type1(void *label) {
    GAME *game=af_insect_game;
    void *actor=game?af_insect_native_player(game):NULL;
    if (!actor || FN(0x8007D90Cu,int,void)() || af_insect_demo_clip) return 0;
    int index=(int)WORD(actor,0xCF0);
    if (index==RELAX_ROD) {
        /* Native RELAX has one insect-interruption flag, reset at setup and
         * read only for the same command-seven cancellation as the source's
         * (bee_flag || mosquito_flag). It does not cause a bee sting or injury. */
        WORD(actor,0xD10)=1;
        return 0;
    }
    if (FN(0x808B6424u,int,int)(index) || FN(0x808B3AE4u,int,void *)(actor)!=1) return 0;
    return request(actor,game,STUNG,(u32)(uintptr_t)label,25);
}
int mPlib_Check_stung_mosquito(void *label) {
    GAME *game=af_insect_game;
    void *actor=game?af_insect_native_player(game):NULL;
    if (!actor) return 0;
    int index=(int)WORD(actor,0xCF0);
    /* This is the donor's requested label, not its main-data label. */
    return (index==STUNG || index==NOTICE) && WORD(actor,0xD58)==(u32)(uintptr_t)label;
}
void af_insect_mosquito_setup(void *actor,GAME *game) {
    int upper,part;
    WORD(actor,0xD10)=WORD(actor,0xD58);
    FN(0x808B846Cu,void,void *,int,float,int *,int *)(actor,MOTION1,-5,&upper,&part);
    FN(0x808B4A44u,void,void *,GAME *,int,int,float,float,float,float,int,int)
        (actor,game,MOTION1,upper,1,1,.5f,-5,0,2);
    FN(0x808B3BD0u,void,void *,GAME *)(actor,game);
}
void af_insect_mosquito_notice_setup(void *actor,GAME *game) {
    int upper,part;
    WORD(actor,0xD10)=WORD(actor,0xD58);REAL(actor,0xD14)=0;WORD(actor,0xD18)=0;
    FN(0x808B846Cu,void,void *,int,float,int *,int *)(actor,MOTION2,-5,&upper,&part);
    FN(0x808B4924u,void,void *,GAME *,int,int,float,float,float,float,int)
        (actor,game,MOTION2,upper,1,1,.5f,-5,2);
    FN(0x808B36E8u,void,void *,int)(actor,4);
    FN(0x808B37F8u,void,void *,int)(actor,4);
    FN(0x808B3BD0u,void,void *,GAME *)(actor,game);
}
static void collision(void *actor,GAME *game) {
    FN(0x808B5310u,void,void *)(actor);
    FN(0x808B4DACu,void,void *,GAME *)(actor,game);
    FN(0x808B5FB0u,void,void *)(actor);
}
void af_insect_mosquito_main(void *actor,GAME *game) {
    float last;int ended=0;
    /* Two source animation ticks, one native movement/collision/item update.
     * The native braking helper receives the two source ticks' total braking. */
    FN(0x808B3C10u,int,void *,float)(actor,0.32625001f*2);
    FN(0x808B61E4u,void,void *,GAME *)(actor,game);
    for (int step=0;step<2;step++) ended|=FN(0x808B48F0u,int,void *,float *)(actor,&last);
    FN(0x808B36F4u,void,void *)(actor);
    collision(actor,game);
    FN(0x808BF410u,int,void *,GAME *)(actor,game);
    if (ended) request(actor,game,NOTICE,WORD(actor,0xD10),26);
}
static void report(void *actor) {
    (void)actor;
    u8 colour[4]={225,165,255,255};
    FN(0x8007B5C0u,void,int)((int)af_insect_mosquito_message);
    FN(0x8007B79Cu,void,int)(0);
    FN(0x8007BA1Cu,void,int)(5);
    FN(0x8007D098u,void,void)();
    FN(0x8007B980u,void,void *)(colour);
    FN(0x8005DF70u,void,int,int)(68,0x168);
}
static int message(void *actor) {
    switch (WORD(actor,0xD18)) {
        case 0:
            if (REAL(actor,0xD14)<0) REAL(actor,0xD14)+=1;
            else WORD(actor,0xD18)=1;
            break;
        case 1:
            if (!FN(0x8007CF00u,int,int,void *)(REPORT,actor))
                FN(0x8007CDD8u,void,int,void *,void (*)(void *))(REPORT,actor,report);
            else WORD(actor,0xD18)=2;
            break;
        case 2:
            if (!FN(0x8007CF00u,int,int,void *)(REPORT,actor)) WORD(actor,0xD18)=3;
            break;
        default:return 1;
    }
    return 0;
}
void af_insect_mosquito_notice_main(void *actor,GAME *game) {
    float last;int finished=0;
    for (int step=0;step<2;step++)
        FN(0x8009A974u,s16,s16 *,s16,float,s16,s16)
            ((s16 *)((u8 *)actor+0xDE),0,0.2928932188f,2500,50);
    HALF(actor,0x36)=HALF(actor,0xDE);
    FN(0x808B3C10u,int,void *,float)(actor,0.32625001f*2);
    for (int step=0;step<2;step++) FN(0x808B48F0u,int,void *,float *)(actor,&last);
    FN(0x808B61E4u,void,void *,GAME *)(actor,game);
    collision(actor,game);
    for (int step=0;step<2;step++) finished|=message(actor);
    FN(0x808BF410u,int,void *,GAME *)(actor,game);
    if (finished) {
        FN(0x808B3648u,void,void *)(actor);
        FN(0x808C1064u,int,GAME *,float,int,int)(game,-5,0,1);
    }
}
void af_insect_mosquito_settle(void *actor,GAME *game) {
    (void)actor;(void)game;
    FN(0x8005E58Cu,void,int,int)(68,0x168);
    /* The native game has no GameCube museum insect-room scene/music owner.
     * Outdoor response is complete; no fictitious museum callback is installed. */
}
