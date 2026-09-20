/* Shared golden-reward message phase. Full action/acquisition stays separate. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct { float timer; int mode, type; } RewardMessage;
#ifdef __mips__
#define FN(at, result, ...) ((result (*)(__VA_ARGS__))(at))
#else
extern void *af_test_reward_function(u32);
#define FN(at, result, ...) ((result (*)(__VA_ARGS__))af_test_reward_function(at))
#endif

static RewardMessage *state(void *actor) { return (RewardMessage *)((u8 *)actor+0xD10); }

int af_v3_reward_message_id(int type) {
    static const unsigned short messages[4]={AF_V3_REWARD_MESSAGE_FIRST+2,
        AF_V3_REWARD_MESSAGE_FIRST,AF_V3_REWARD_MESSAGE_FIRST+1,AF_V3_REWARD_MESSAGE_FIRST+3};
    return (u32)type<4u ? messages[type] : -1;
}

int af_v3_reward_message_reset(void *actor,int type) {
    if (!actor || (u32)type>=4u) return 0;
    RewardMessage *message=state(actor);
    message->timer=0;message->mode=0;message->type=type;
    return 1;
}

void af_v3_reward_message_begin(void *actor) {
    if (!actor) return;
    int id=af_v3_reward_message_id(state(actor)->type);
    if (id<0) return;
    const u8 colour[4]={185,245,80,255};
    void *window=FN(0x8009D1F0u,void *,void)();
    FN(0x8007B5C0u,void,int)(id);
    FN(0x8007B79Cu,void,int)(0);
    FN(0x8007BA1Cu,void,int)(5);
    FN(0x8007D098u,void,void)();
    FN(0x8009E9E8u,void,void *)(window);
    FN(0x8007B980u,void,const u8 *)(colour);
    FN(0x80065508u,void,void *)(FN(0x80065040u,void *,void)());
}

int af_v3_reward_message_update(void *actor,int animation_ended) {
    if (!actor || (u32)state(actor)->type>=4u) return 0;
    RewardMessage *message=state(actor);
    /* Native animations advance 1.0 per update versus donor 0.5. Preserve
       the source's 42-update wait in the native timing units. */
    if (message->timer<42.0f) { message->timer+=2.0f; return 0; }
    switch (message->mode) {
    case 0:
        if (!FN(0x8007CF00u,int,int,void *)(9,actor))
            FN(0x8007CDD8u,int,int,void *,void (*)(void *))(9,actor,af_v3_reward_message_begin);
        else message->mode=1;
        return 0;
    case 1:
        if (animation_ended) {
            FN(0x8009E9F8u,void,void *)(FN(0x8009D1F0u,void *,void)());
            message->mode=2;
        }
        return 0;
    case 2:
        if (!FN(0x8007CF00u,int,int,void *)(9,actor)) message->mode=3;
        return 0;
    default:return 1;
    }
}
