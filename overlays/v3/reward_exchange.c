/* Native inventory exchange with source reward timing; no new item is awarded. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef struct { float x,y,z; } Pos;
#define WORD(p,o) (*(int *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(u16 *)((u8 *)(p)+(o)))
#ifdef __mips__
#define PTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define game (*(void **)0x8010EF90u)
#define active (*(u8 **)0x80136FD8u)
static void *native(u32 address,u32 context) {
    if (address>=0x8086F310u) address=context-0x80873AECu+address;
    return (void *)address;
}
#else
extern void *af_test_exchange_pointer(void *,u32), *af_test_exchange_function(u32,u32);
extern u8 *af_test_exchange_game, *af_test_exchange_active;
#define PTR af_test_exchange_pointer
#define native af_test_exchange_function
#define game af_test_exchange_game
#define active af_test_exchange_active
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at,context))
extern int af_v3_reward_completed(u32),af_v3_player_selected_equipment(u32);
extern u32 af_v3_present_encode(u32,u32);

static int reward(u32 incoming,u32 outgoing) {
    return incoming==0x223Bu && outgoing!=0x223Bu &&
        af_v3_player_selected_equipment(incoming)>=0 && af_v3_reward_completed(3)==0;
}

void af_v3_reward_exchange(void *submenu,void *menu,u32 context) {
    if (!submenu || !menu || !game) return;
    void *actor=FN(0x800B1C84u,void *,void *)(game);
    if (!actor) return;
    u8 *change=FN(0x800B1F74u,u8 *,void)();
    void *overlay=PTR(submenu,0x2C);
    int sound=0x31;
    if (!FN(0x80871708u,int,void *)(submenu)) {
        void *hand=PTR(overlay,0x106D4);
        u32 raw=HALF(hand,0x23C),item=af_v3_present_encode(raw,(u32)WORD(hand,0x2E4));
        int flag=reward((u16)WORD(menu,0x3C),item);
        if (raw>>12==2u && (raw>>8&15u)==3u) {
            FN(0x800B2060u,void,int,int)((s16)HALF(menu,0x46),(s16)item);
            WORD(change,0x20)=flag;
        } else if (raw>>12==2u && (raw>>8&15u)==13u) {
            FN(0x80873968u,void,u32)(item);
            WORD(change,0x20)=flag;
        } else {
            Pos pos;
            if (FN(0x80870C6Cu,int,void *,Pos *,int)(actor,&pos,0) &&
                FN(0x808715C8u,int,void *,u32,Pos *)(game,item,&pos)) {
                WORD(change,0)=flag?118:7;WORD(change,4)=1;WORD(change,0x20)=0;
                if (!flag) sound=-1;
            } else {
                void *dig=PTR(menu,0x40);
                u32 equipped=HALF(active,0x3EC);
                if (dig && (equipped==0x2202u ||
                    (equipped==0x223Bu && af_v3_player_selected_equipment(equipped)>=0))) {
                    FN(0x800B2008u,void,const void *,u32)(dig,item);
                    WORD(change,0x20)=flag;
                } else {
                    FN(0x80871570u,void,void *,void *,int)(submenu,menu,11);
                    return;
                }
            }
        }
    } else {
        WORD(change,0)=reward((u16)WORD(menu,0x3C),0)?118:7;
        WORD(change,4)=1;WORD(change,0x20)=0;
    }
    ((void (*)(void *,int))PTR(overlay,0x106B0))(menu,0);
    if (sound>=0) FN(0x800D1A9Cu,void,int)(sound);
}
