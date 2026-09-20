/* Source golden-axe waiting action, with native animation/timer intervals. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
static void *native(u32 address) {
    if (address>=0x808B2D50u) address=*(volatile u32 *)0x80143900u-0x808DD748u+address;
    return (void *)address;
}
#else
extern void *af_test_reward_wait_function(u32);
#define native af_test_reward_wait_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
#define WORD(p,at) (*(int *)((u8 *)(p)+(at)))
#define REAL(p,at) (*(float *)((u8 *)(p)+(at)))

void af_v3_reward_wait_setup(void *actor,void *game) {
    if (!actor || !game) return;
    int upper,part;
    float first=1.0f,second=1.0f,morph=-5.0f;
    REAL(actor,0xD10)=0.0f;
    FN(0x808B846Cu,void,void *,int,float,int *,int *)(actor,0,-5.0f,&upper,&part);
    /* Native Base1 lacks the donor's WAIT1 continuation optimization. Keep the
       complete source predicate rather than restarting an already idle pose. */
    if (REAL(actor,0x194)==0.0f && WORD(actor,0xDAC)==0 && WORD(actor,0xDB0)==upper &&
            (part!=0 || upper==0)) {
        first=REAL(actor,0x184);second=REAL(actor,0x1F4);morph=0.0f;
    }
    FN(0x808B4924u,void,void *,void *,int,int,float,float,float,float,int)
        (actor,game,0,upper,first,second,1.0f,morph,part);
    FN(0x808B3BD0u,void,void *,void *)(actor,game);
}

void af_v3_reward_wait_main(void *actor,void *game) {
    if (!actor || !game) return;
    FN(0x808B61E4u,void,void *,void *)(actor,game);
    FN(0x808B482Cu,int,void *)(actor);
    FN(0x808B5310u,void,void *)(actor);
    FN(0x808B36F4u,void,void *)(actor);
    FN(0x808B4DACu,void,void *,void *)(actor,game);
    FN(0x808B5FB0u,void,void *)(actor);
    FN(0x808BF410u,void,void *,void *)(actor,game);
    if (REAL(actor,0xD10)<320.0f) REAL(actor,0xD10)+=2.0f;
    else (void)FN(AF_V3_REWARD_EVENT,int,void *,int)(game,0);
}
