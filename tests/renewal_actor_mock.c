/* Isolated native-helper equivalents; no ROM, save, or donor text is embedded. */
#include <stdlib.h>
#include <string.h>
#include "../overlays/mail_generation/renewal_actor.h"

unsigned char af_renewal_save[0xF980];
unsigned int af_mail_generation_capital;
unsigned int af_renewal_test_allocations,af_renewal_test_frees,af_renewal_test_live;
unsigned int af_renewal_test_fail_malloc,af_renewal_test_bad_heap,af_renewal_test_bad_free;
unsigned int af_renewal_test_alignment,af_renewal_test_copies,af_renewal_test_working;
unsigned int af_renewal_test_events[64],af_renewal_test_event_count;
int af_renewal_test_bad_slot;
static unsigned char *allocation;
static unsigned int allocation_bytes;

static void event(unsigned int value) {
    if (af_renewal_test_event_count < 64u)
        af_renewal_test_events[af_renewal_test_event_count++] = value;
}

void *af_renewal_malloc(unsigned int bytes) {
    ++af_renewal_test_allocations;event(1);
    if (af_renewal_test_fail_malloc || af_renewal_test_live) return NULL;
    allocation = malloc(bytes+64u);
    if (!allocation) return NULL;
    allocation_bytes = bytes;af_renewal_test_live = 1;
    memset(allocation,0xA5,bytes+64u);
    return allocation+16u+af_renewal_test_alignment;
}

int af_renewal_test_heap_range(void *pointer,unsigned int bytes) {
    return !af_renewal_test_bad_heap && bytes == allocation_bytes
        && pointer == allocation+16u+af_renewal_test_alignment;
}

void af_renewal_free(void *pointer) {
    unsigned int i;
    if (!af_renewal_test_live || pointer != allocation+16u+af_renewal_test_alignment) {
        ++af_renewal_test_bad_free;return;
    }
    for (i = 0; i < 16u+af_renewal_test_alignment; ++i)
        if (allocation[i] != 0xA5u) ++af_renewal_test_bad_free;
    for (i = 16u+af_renewal_test_alignment+allocation_bytes; i < allocation_bytes+64u; ++i)
        if (allocation[i] != 0xA5u) ++af_renewal_test_bad_free;
    free(allocation);allocation = NULL;af_renewal_test_live = 0;
    ++af_renewal_test_frees;event(4);
}

int af_renewal_house_player(unsigned int home) {
    unsigned int i,mapping = af_renewal_save[0xEF5A];
    for (i = 0; i < 4u; ++i,mapping >>= 2) if ((mapping&3u) == home) return (int)i;
    return 4;
}

int af_renewal_working_player(unsigned int player) {
    return (int)((af_renewal_test_working>>player)&1u);
}

int af_renewal_free_mail(unsigned char *mail,unsigned int count) {
    unsigned int i;
    if (af_renewal_test_bad_slot) return af_renewal_test_bad_slot;
    if (count != 10u) return -1;
    for (i = 0; i < count; ++i) if (mail[i*164u+38u] == 255u) return (int)i;
    return -1;
}

void af_renewal_clear_mail(unsigned char *mail) {
    memset(mail,0,164);
    memset(mail,' ',12);memset(mail+12,255,4);mail[16] = 255;
    memset(mail+18,' ',12);memset(mail+30,255,4);mail[34] = 255;
    mail[38] = 255;memset(mail+42,' ',122);event(2);
}

void af_renewal_copy_id(unsigned char *destination,const unsigned char *source) {
    memcpy(destination,source,16);
}

void af_renewal_copy_mail(unsigned char *destination,const unsigned char *source) {
    memcpy(destination,source,164);++af_renewal_test_copies;event(3);
}
