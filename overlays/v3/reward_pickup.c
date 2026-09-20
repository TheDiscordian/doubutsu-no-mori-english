/* Shared source completion checks and collection-to-celebration transition. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
static void *native(u32 address) {
    return (void *)(*(volatile u32 *)0x80143900u-0x808DD748u+address);
}
#else
extern u8 af_test_reward_players[4*0xBD0], *af_test_reward_active;
#define players af_test_reward_players
#define active af_test_reward_active
extern void *af_test_reward_pickup_function(u32);
#define native af_test_reward_pickup_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_v3_reward_flag(u32,u32,u32,u32);
extern int af_v3_player_selected_equipment(u32);
extern int af_v3_reward_request(void *,int,int,int);

/* Invalid identities are not an unfinished reward belonging to player zero. */
int af_v3_reward_completed(u32 type) {
    if (type>=4) return -1;
    const u8 *p=active;
    for (u32 slot=0;slot<4;++slot)
        if (p==players+slot*0xBD0u) return af_v3_reward_flag(slot,1,type,0);
    return -1;
}

void af_v3_reward_pickup(void *actor,void *game,u32 item,int settle_first) {
    if (!actor || !game) return;
    if (settle_first) FN(0x808B3648u,void,void *)(actor);
    if (item==0x223Bu && af_v3_player_selected_equipment(item)>=0 &&
        af_v3_reward_completed(3)==0) {
        /* No idle fallback after rejection: the source retries next update. */
        (void)af_v3_reward_request(game,118,3,34);
    } else {
        if (!settle_first) FN(0x808B3648u,void,void *)(actor);
        FN(0x808C1064u,int,void *,float,int,int)(game,-5.0f,0,1);
    }
}
