/* Shared source reward requests; no acquisition event or item is fabricated. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
static void *native(u32 address) {
    if (address>=0x808B2D50u) address=*(volatile u32 *)0x80143900u-0x808DD748u+address;
    return (void *)address;
}
#else
extern void *af_test_reward_route_function(u32);
#define native af_test_reward_route_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))

int af_v3_reward_request(void *game,int action,int type,int priority) {
    if (!game || (u32)(action-118)>=3u || (u32)type>=4u || (action==120 && type)) return 0;
    if (!FN(0x808B8874u,int,void *,int,int)(game,action,priority)) return 0;
    void *actor=FN(0x800B1C84u,void *,void *)(game);
    if (!actor) return 0;
    FN(0x808B3334u,void,void *,int,int)(game,action,priority);
    if (action!=120) *(int *)((u8 *)actor+0xD58)=type;
    return 1;
}

int af_v3_reward_event(void *game,int type) {
    return af_v3_reward_request(game,119,type,34);
}

int af_v3_reward_axe_wait_request(void *game) {
    return af_v3_reward_request(game,120,0,33);
}

void af_v3_reward_submenu(void *actor,void *game) {
    (void)actor;
    (void)af_v3_reward_request(game,118,3,31);
}
