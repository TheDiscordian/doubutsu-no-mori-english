#ifndef AF_V3_NOOK_PASSWORD_H
#define AF_V3_NOOK_PASSWORD_H
#include "password_policy.h"

/* Transient conversation state, separate from the smaller native shop actor.
 * The three-gift counter belongs to shared session state, not this actor and
 * not a new daily/save field. Services must bind real UI, inventory, and clips. */
enum AfNookPasswordStage {
    AF_NP_IDLE, AF_NP_INPUT_START, AF_NP_HIDE_WAIT, AF_NP_MENU_WAIT,
    AF_NP_RESULT_WAIT, AF_NP_RETRY_WAIT, AF_NP_GIFT_START,
    AF_NP_GIFT_TAKEOUT, AF_NP_GIFT_TRANSFER, AF_NP_GIFT_END
};
enum AfNookPasswordMessage {
    AF_NP_SAY=10, AF_NP_FULL, AF_NP_FOREIGN, AF_NP_GIFT_LIMIT
};
struct AfNookPassword {
    void *shop, *play;
    af_pw_u8 code[28], player[8], town[8];
    struct AfPasswordOffer offer;
    af_pw_u32 stage, inserted;
};
struct AfNookPasswordOps {
    void *context;
    af_pw_u32 *gift_count;
    int (*foreign)(void *);
    int (*pocket_free)(void *);
    int (*order)(void *,int);
    void (*set_order)(void *,int,int);
    int (*message_ready)(void *);
    int (*message_hidden)(void *);
    int (*message_open)(void *);
    void (*hide_message)(void *);
    void (*open_message)(void *);
    int (*open_editor)(void *,af_pw_u8 *);
    int (*menu_active)(void *);
    int (*check)(void *,const af_pw_u8 *,const af_pw_u8 *,const af_pw_u8 *,struct AfPasswordOffer *);
    void (*message)(void *,int,const struct AfPasswordOffer *);
    void (*force_next)(void *);
    int (*choice)(void *);
    /* An inventory refusal cannot advance or increment the gift count. */
    int (*insert_present)(void *,af_pw_u32);
    void (*rustle)(void *);
    void (*lock_message)(void *,int);
    void (*lock_head)(void *,int);
    void *(*left_item)(void *);
    void (*set_left_item)(void *,void *);
    void *(*birth)(void *,af_pw_u32,int,int,void *);
    void (*request_handover)(void *,int);
    int (*animation_stopped)(void *);
    void (*animation)(void *,int);
    int (*handover_ready)(void *);
    void *(*handover_master)(void *);
    /* Return to native question/end actions, retaining their ordinary setup. */
    void (*finish)(void *,int);
};
int af_nook_password_begin(struct AfNookPassword *,const struct AfNookPasswordOps *,
    void *,void *,const af_pw_u8 *,const af_pw_u8 *);
int af_nook_password_step(struct AfNookPassword *,const struct AfNookPasswordOps *);
#endif
