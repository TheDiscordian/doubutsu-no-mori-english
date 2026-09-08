#include "fortune_actor.h"

extern unsigned char *af_miko_private;
extern int af_miko_find_item(unsigned char *player, unsigned int item, unsigned int condition);
extern void af_miko_original_charge(unsigned int amount);
extern int af_miko_original_end(unsigned char *actor, void *play);
extern void af_miko_original_save(unsigned char *actor, void *play);
extern void af_miko_original_destroy(unsigned char *actor, void *play);
extern const unsigned short af_miko_money_items[4];
extern const unsigned int af_miko_money_values[4];

#define PAYMENT_TAG 0xA5000000u
#define PAYMENT_MASK 0xFF800000u

/* Fifty Bells consume wallet money or at most one normal-condition Bell bag.
 * Capture that exact original payment, including the bag's identity and slot.
 * The original charge and earlier luck store retain their native timing.
 */
void af_miko_fortune_charge(unsigned char *actor) {
    AfMikoPending *pending;
    unsigned char *player = af_miko_private;
    unsigned int money, kind = 0, slot = 0;
    int found;
    if (!actor) return;
    pending = (AfMikoPending *)(actor+AF_MIKO_PENDING_OFFSET);
    if (!player || pending->owner != player || pending->state != AF_MIKO_ARMED || pending->payment) return;
    money = *(unsigned int *)(player+0x38u);
    if (money > 0x1FFFFu) return;
    if (money < 50u) {
        for (kind = 0; kind < 4u; ++kind) {
            found = af_miko_find_item(player,af_miko_money_items[kind],0);
            if (found >= 0 && found < 15) { slot = (unsigned int)found+1u; break; }
        }
        if (!slot) return;
    }
    pending->payment = PAYMENT_TAG|money|(slot<<17)|(kind<<21);
    af_miko_original_charge(50);
}

/* Recover only an unfinished payment whose native post-charge values remain
 * intact. Never overwrite another player's money or a subsequently used slot.
 * The already revealed luck is neither rerolled nor rewritten on interruption.
 */
int af_miko_fortune_abort(unsigned char *actor) {
    AfMikoPending *pending;
    unsigned char *player;
    unsigned int payment, money, slot, kind, expected;
    if (!actor) return 1;
    pending = (AfMikoPending *)(actor+AF_MIKO_PENDING_OFFSET);
    payment = pending->payment;
    if (pending->state != AF_MIKO_ARMED && pending->state != AF_MIKO_SELECTED) return 1;
    if (!payment) return 1;
    if ((payment&PAYMENT_MASK) != PAYMENT_TAG || !af_miko_private || pending->owner != af_miko_private) return 0;
    player = pending->owner;
    money = payment&0x1FFFFu;slot = (payment>>17)&15u;kind = (payment>>21)&3u;
    if ((money < 50u) != (slot != 0) || (!slot && kind)) return 0;
    expected = money+(slot ? af_miko_money_values[kind] : 0u)-50u;
    if (*(unsigned int *)(player+0x38u) != expected) return 0;
    if (slot) {
        --slot;
        if (*(unsigned short *)(player+0x14u+slot*2u)
                || ((*(unsigned int *)(player+0x34u)>>(slot*2u))&3u)) return 0;
        *(unsigned short *)(player+0x14u+slot*2u) = af_miko_money_items[kind];
    }
    *(unsigned int *)(player+0x38u) = money;
    pending->payment = 0;
    pending->state = AF_MIKO_CANCELLED;
    return 1;
}

int af_miko_fortune_end(unsigned char *actor, void *play) {
    int ended = af_miko_original_end(actor,play);
    if (ended) af_miko_fortune_abort(actor);
    return ended;
}

void af_miko_fortune_save(unsigned char *actor, void *play) {
    af_miko_fortune_abort(actor);
    af_miko_original_save(actor,play);
}

void af_miko_fortune_destroy(unsigned char *actor, void *play) {
    af_miko_fortune_abort(actor);
    af_miko_original_destroy(actor,play);
}
