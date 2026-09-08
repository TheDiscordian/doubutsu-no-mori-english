#include <stdlib.h>
#include <string.h>
#include "../overlays/mail_generation/fortune_actor.h"

unsigned char af_fortune_words[AF_FORTUNE_WORD_BYTES];
unsigned char *af_miko_private;
unsigned int af_mail_generation_capital;
unsigned int af_miko_test_rng, af_miko_test_draws;
unsigned int af_miko_test_allocations, af_miko_test_frees, af_miko_test_live;
unsigned int af_miko_test_fail_malloc, af_miko_test_bad_free, af_miko_test_alignment;
unsigned int af_miko_test_copies, af_miko_test_slots, af_miko_test_events[64];
unsigned int af_miko_test_event_count;
int af_miko_test_slot, af_miko_test_second_slot, af_miko_test_order;
unsigned int af_miko_test_cancel, af_miko_test_switch_owner;
unsigned char af_miko_test_other_player[4096];
static unsigned char *allocation;
static unsigned int allocation_bytes;

static void event(unsigned int value) {
    if (af_miko_test_event_count < 64u)
        af_miko_test_events[af_miko_test_event_count++] = value;
}

unsigned int af_miko_test_pending_bytes(void) { return sizeof(AfMikoPending); }
unsigned int af_miko_test_work_bytes(void) { return sizeof(AfMikoWork); }

float af_miko_random(void) {
    float value;
    unsigned int bits;
    af_miko_test_rng = af_miko_test_rng*0x19660Du+0x3C6EF35Fu;
    bits = (af_miko_test_rng>>9)|0x3F800000u;
    memcpy(&value,&bits,4);
    ++af_miko_test_draws;
    return value-1.0f;
}

void af_miko_original_init(unsigned char *actor, void *play) {
    (void)play;
    *(int *)(actor+0x940u) = (int)(af_miko_random()*4.0f);
    event(1);
}

void *af_miko_malloc(unsigned int bytes) {
    ++af_miko_test_allocations;
    if (af_miko_test_fail_malloc || af_miko_test_live) return NULL;
    allocation_bytes = bytes;
    allocation = malloc(bytes+64u);
    if (!allocation) return NULL;
    memset(allocation,0xA5,bytes+64u);
    af_miko_test_live = 1;
    event(2);
    return allocation+16u+af_miko_test_alignment;
}

void af_miko_free(void *pointer) {
    unsigned int i;
    if (!af_miko_test_live || pointer != allocation+16u+af_miko_test_alignment) {
        ++af_miko_test_bad_free;
        return;
    }
    for (i = 0; i < 16u+af_miko_test_alignment; ++i)
        if (allocation[i] != 0xA5u) ++af_miko_test_bad_free;
    for (i = 16u+af_miko_test_alignment+allocation_bytes; i < allocation_bytes+64u; ++i)
        if (allocation[i] != 0xA5u) ++af_miko_test_bad_free;
    free(allocation);
    allocation = NULL;
    af_miko_test_live = 0;
    ++af_miko_test_frees;
    event(5);
}

int af_miko_get_order(int group, int slot) {
    return group == 4 && slot == 9 ? af_miko_test_order : -1;
}

void af_miko_set_order(int group, int slot, int value) {
    event(0x10000000u|((unsigned int)group<<20)|((unsigned int)slot<<16)|(unsigned int)value);
    if (group == 4 && slot == 9) af_miko_test_order = value;
}

void af_miko_clear_mail(unsigned char *mail) {
    memset(mail,0x20,164);
    mail[36] = 0x6A; mail[37] = 0x2B;
    event(3);
}

void af_miko_set_recipient(unsigned char *mail, const unsigned char *player) {
    memcpy(mail,player,16);
    if (af_miko_test_cancel) af_miko_test_order = 0;
    if (af_miko_test_switch_owner) af_miko_private = af_miko_test_other_player;
}

int af_miko_free_mail(const unsigned char *mail, int count) {
    (void)mail;
    if (count != 10) return -1;
    return ++af_miko_test_slots == 1 ? af_miko_test_slot : af_miko_test_second_slot;
}

void af_miko_copy_mail(unsigned char *destination, const unsigned char *source) {
    memcpy(destination,source,164);
    ++af_miko_test_copies;
    event(4);
}

void af_miko_setup_action(unsigned char *actor, void *play, int action) {
    (void)play;
    *(int *)(actor+0x938u) = action;
    event(6);
}
