/* Shared reward setup and per-frame control. Persistent settlement and ordinary
   event registration remain separate requirements; these are not enabled actions. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed short s16;
#ifdef __mips__
static void *native(u32 address) {
    if (address>=0x808B2D50u) address=*(volatile u32 *)0x80143900u-0x808DD748u+address;
    return (void *)address;
}
#else
extern void *af_test_player_reward_function(u32);
#define native af_test_player_reward_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
#define WORD(p,at) (*(int *)((u8 *)(p)+(at)))
#define SHORT(p,at) (*(s16 *)((u8 *)(p)+(at)))

int af_v3_reward_bgm(int type) {
    static const u8 bgms[4]={AF_V3_REWARD_BGMS};
    return (u32)type<4u ? bgms[type] : -1;
}

void af_v3_reward_setup(void *actor,void *game) {
    if (!actor || !game) return;
    int type=WORD(actor,0xD58),bgm=af_v3_reward_bgm(type);
    if (bgm<0) return;
    int kind=FN(0x808BD5C4u,int,void *,int)(actor,WORD(actor,0xD00));
    int upper,unused,lower=258,part=3;
    FN(AF_V3_REWARD_RESET,int,void *,int)(actor,type);
    /* Base1 reaches the existing complete pinwheel/balloon Base0 adapter. */
    FN(0x808B846Cu,void,void *,int,float,int *,int *)(actor,258,-5.0f,&upper,&unused);
    if ((u32)kind-91u<8u) { lower=upper=260;part=0; }
    FN(0x808B4A44u,void,void *,void *,int,int,float,float,float,float,int,int)
        (actor,game,lower,upper,1.0f,1.0f,1.0f,-5.0f,0,part);
    FN(0x808B3BD0u,void,void *,void *)(actor,game);
    FN(0x8005DC9Cu,void,int,int)(bgm,0x168);
}

void af_v3_reward_stop_fanfare(void *actor) {
    if (!actor) return;
    int bgm=af_v3_reward_bgm(WORD(actor,0xD18));
    if (bgm>=0) FN(0x8005E494u,void,int,int)(bgm,0x168);
    /* Audio only; the shared settlement wrapper records the saved reward bit. */
}

void af_v3_reward_main(void *actor,void *game) {
    if (!actor || !game || (u32)WORD(actor,0xD18)>=4u) return;
    float last_frame;
    int ended=FN(0x808B488Cu,int,void *,float *)(actor,&last_frame);
    /* Two source turn steps preserve the source curve at the native interval. */
    for (int i=0;i<2;i++)
        FN(0x8009A974u,void,s16 *,int,float,int,int)((s16 *)((u8 *)actor+0xDE),0,
            0.2928932188134524f,2500,50);
    SHORT(actor,0x36)=SHORT(actor,0xDE);
    FN(0x808B3C74u,int,void *)(actor);
    FN(0x808B61E4u,void,void *,void *)(actor,game);
    FN(0x808B5310u,void,void *)(actor);
    if (ended) FN(0x808B36F4u,void,void *)(actor);
    else FN(0x808B3828u,void,void *)(actor);
    FN(0x808B4DACu,void,void *,void *)(actor,game);
    FN(0x808B5FFCu,void,void *)(actor);
    FN(0x808BF410u,void,void *,void *)(actor,game);
    if (FN(AF_V3_REWARD_UPDATE,int,void *,int)(actor,ended)) {
        FN(0x808B3648u,void,void *)(actor);
        FN(0x808C1064u,int,void *,float,int,int)(game,-5.0f,0,1);
    }
}
