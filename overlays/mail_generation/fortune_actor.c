#include "fortune_actor.h"

/* Linker-bound imports retain explicit relocation records for verification. */
extern unsigned char *af_miko_private;
extern unsigned int af_mail_generation_capital;
extern const unsigned char af_fortune_words[AF_FORTUNE_WORD_BYTES];
extern float af_miko_random(void);
extern void *af_miko_malloc(unsigned int bytes);
extern void af_miko_free(void *allocation);
extern int af_miko_get_order(int group, int slot);
extern void af_miko_set_order(int group, int slot, int value);
extern void af_miko_clear_mail(unsigned char *mail);
extern void af_miko_set_recipient(unsigned char *mail, const unsigned char *player);
extern int af_miko_free_mail(const unsigned char *mail, int count);
extern void af_miko_copy_mail(unsigned char *destination, const unsigned char *source);
extern void af_miko_original_init(unsigned char *actor, void *play);
extern void af_miko_setup_action(unsigned char *actor, void *play, int action);

#ifdef __mips__
typedef char pending_size_check[sizeof(AfMikoPending) == 24 ? 1 : -1];
typedef char work_size_check[sizeof(AfMikoWork) == 5456 ? 1 : -1];
#endif

static int action(const unsigned char *actor) {
    return *(const int *)(actor+0x938u);
}

static int outcome(const unsigned char *actor) {
    return *(const int *)(actor+0x940u);
}

void af_miko_fortune_init(unsigned char *actor, void *play) {
    AfMikoPending *pending;
    unsigned int i;
    if (!actor) return;
    if (!af_miko_fortune_abort(actor)) return;
    pending = (AfMikoPending *)(actor+AF_MIKO_PENDING_OFFSET);
    for (i = 0; i < sizeof(*pending); ++i) ((unsigned char *)pending)[i] = 0;
    pending->owner = af_miko_private;
    pending->state = AF_MIKO_ARMED;
    /* Keep the original one-draw outcome initializer and native ordering. */
    af_miko_original_init(actor,play);
}

void af_miko_fortune_give(unsigned char *actor, void *play) {
    AfMikoPending *pending;
    AfMikoWork *work;
    unsigned char *owner;
    void *allocation;
    unsigned int i, capital;
    int slot, result;
    if (!actor || action(actor) != 3 || af_miko_get_order(4,9) != 1) return;
    pending = (AfMikoPending *)(actor+AF_MIKO_PENDING_OFFSET);
    owner = af_miko_private;
    if (!owner || pending->owner != owner || (pending->payment & 0xFF800000u) != 0xA5000000u
            || (pending->state != AF_MIKO_ARMED && pending->state != AF_MIKO_SELECTED)
            || outcome(actor) < 0 || outcome(actor) >= 4
            || af_mail_generation_capital > 1u) return;
    if (pending->state == AF_MIKO_SELECTED && pending->choice.outcome != outcome(actor)) return;
    slot = af_miko_free_mail(owner+AF_MIKO_MAIL_OFFSET,10);
    if (slot < 0 || slot >= 10) return;
    allocation = af_miko_malloc(sizeof(*work)+15u);
    if (!allocation) return;
    work = (AfMikoWork *)(((__UINTPTR_TYPE__)allocation+15u)&~(__UINTPTR_TYPE__)15u);
    if (pending->state == AF_MIKO_ARMED) {
        for (i = 0; i < 4u; ++i)
            pending->choice.phrases[i] = (unsigned char)(int)(af_miko_random()*16.0f);
        pending->choice.outcome = (unsigned char)outcome(actor);
        pending->choice.template_index = (unsigned char)(int)(af_miko_random()*3.0f);
        pending->choice.reserved[0] = pending->choice.reserved[1] = 0;
        pending->capital = af_mail_generation_capital;
        pending->state = AF_MIKO_SELECTED;
    }
    /* Start with deterministic owned bytes before preparing native metadata. */
    for (i = 0; i < sizeof(work->mail); ++i) work->mail[i] = 0;
    af_miko_clear_mail(work->mail);
    af_miko_set_recipient(work->mail,owner);
    capital = pending->capital;
    result = af_fortune_slip_create(work->mail,164,&pending->choice,af_fortune_words,
                                   AF_FORTUNE_WORD_BYTES,&capital,&work->generation);
    /* No fortune template changes the sticky flag. In particular, a retry
     * must not restore an old captured flag over another creator's new value.
     */
    if (result && capital == pending->capital && af_miko_private == owner
            && pending->state == AF_MIKO_SELECTED && pending->owner == owner
            && pending->choice.outcome == outcome(actor) && action(actor) == 3
            && af_miko_get_order(4,9) == 1) {
        slot = af_miko_free_mail(owner+AF_MIKO_MAIL_OFFSET,10);
        if (slot >= 0 && slot < 10) {
            af_miko_copy_mail(owner+AF_MIKO_MAIL_OFFSET+(unsigned int)slot*164u,work->mail);
            pending->state = AF_MIKO_DELIVERED;
            pending->payment = 0;
        }
    }
    af_miko_free(allocation);
    if (pending->state != AF_MIKO_DELIVERED) return;
    /* Only a stored complete letter may trigger the unchanged native demo. */
    af_miko_set_order(4,9,0);
    af_miko_set_order(4,1,2);
    af_miko_set_order(5,0,0x2513);
    af_miko_set_order(5,1,7);
    af_miko_set_order(5,2,0);
    af_miko_setup_action(actor,play,0);
}
