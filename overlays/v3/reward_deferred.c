/* Deferred source rewards retain native bury/release actions and their timing. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define WORD(p,o) (*(int *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define REAL(p,o) (*(float *)((u8 *)(p)+(o)))
#ifdef __mips__
static void *native(u32 address) {
    if (address>=0x808B2D50u) address=*(volatile u32 *)0x80143900u-0x808DD748u+address;
    return (void *)address;
}
#else
extern void *af_test_deferred_function(u32);
#define native af_test_deferred_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_v3_reward_request(void *,int,int,int);

void af_v3_reward_bury_submenu(void *actor,void *game) {
    if (!actor || !game) return;
    u8 *change=FN(0x800B1F74u,u8 *,void)();
    if (FN(0x808D2458u,int,void *,const void *,int,int)(game,change+8,HALF(change,0x14),31))
        WORD(actor,0xD70)=WORD(change,0x20)!=0;
}

void af_v3_reward_release_submenu(void *actor,void *game) {
    if (!actor || !game) return;
    u8 *change=FN(0x800B1F74u,u8 *,void)();
    if (FN(0x808D71F8u,int,void *,int,const void *,void *,int)(game,WORD(change,8),change+12,0,31))
        WORD(actor,0xD70)=WORD(change,0x20)!=0;
}

void af_v3_reward_bury_setup(void *actor,void *game) {
    if (!actor || !game) return;
    int flag=WORD(actor,0xD70);
    FN(0x808D251Cu,void,void *,void *)(actor,game);
    WORD(actor,0xD20)=flag!=0;
}

void af_v3_reward_release_setup(void *actor,void *game) {
    if (!actor || !game) return;
    int flag=WORD(actor,0xD70);
    FN(0x808D72E0u,void,void *,void *)(actor,game);
    WORD(actor,0xD20)=flag!=0;
}

void af_v3_reward_bury_transition(void *actor,void *game,int ended) {
    if (!actor || !game) return;
    if (!WORD(actor,0xD20)) {
        FN(0x808D10D8u,void,void *,void *,int)(actor,game,ended);
    } else if (ended) {
        FN(0x808B3648u,void,void *)(actor);
        (void)af_v3_reward_request(game,118,3,34);
    }
}

void af_v3_reward_release_transition(void *actor,void *game) {
    if (!actor || !game) return;
    /* Native fish/insect Look has no balloon-dependent continuation result.
       Full balloon release needs its own actor and Look integration. */
    float *timer=(float *)((u8 *)actor+0xD18);
    *timer+=1.0f;
    if (*timer>=42.0f) {
        FN(0x808B3648u,void,void *)(actor);
        if (WORD(actor,0xD20)) (void)af_v3_reward_request(game,118,3,34);
        else FN(0x808C1064u,int,void *,float,int,int)(game,-5.0f,0,1);
        *timer=42.0f;
    }
}
