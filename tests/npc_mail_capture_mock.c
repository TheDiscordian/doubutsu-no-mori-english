#include <stdint.h>
#include <string.h>
#include "../runtime/mail/npc_generation.h"

unsigned char af_npc_test_fields[20][10];
unsigned char af_npc_test_other[12], af_npc_test_land[6] = {'T','O','W','N',' ',' '};
unsigned int af_npc_test_offsets[11], af_npc_test_calls[5];
uintptr_t af_npc_test_arguments[6];

static void set(unsigned int slot, const unsigned char *source, unsigned int size) {
    unsigned int i;
    for (i = 0; i < 10u; ++i) af_npc_test_fields[slot][i] = i < size ? source[i] : ' ';
}

void af_npc_test_name(unsigned char *destination, const unsigned char *animal) {
    ++af_npc_test_calls[1];
    af_npc_test_arguments[0] = (uintptr_t)destination; af_npc_test_arguments[1] = (uintptr_t)animal;
    memcpy(destination,"NATIVE",6);
}

void af_npc_test_word(unsigned char *destination, unsigned int size, unsigned int id) {
    ++af_npc_test_calls[2];
    af_npc_test_arguments[0] = (uintptr_t)destination; af_npc_test_arguments[1] = size; af_npc_test_arguments[2] = id;
    memset(destination,'w',size);
}

void af_npc_test_prepare(const unsigned char *player, const unsigned char *animal, const unsigned char *remail) {
    static const unsigned int bases[11] = {0x314,0x334,0x2F4,0x219,0x1E5,0x354,0x374,0x394,0x3D4,0x3F4,0x3B4};
    unsigned char temporary[10];
    unsigned int i;
    ++af_npc_test_calls[0];
    set(0,player,6);
    if (!remail) {
        af_npc_mail_sender_name(temporary,animal); set(1,temporary,6);
    } else set(1,remail+4u,6);
    af_npc_mail_other_name(temporary,af_npc_test_other); set(2,temporary,6);
    if (remail) { set(14,remail+10u,6); set(15,af_npc_test_land,6); }
    for (i = 0; i < 11u; ++i) {
        af_npc_mail_word(temporary,10,bases[i]+af_npc_test_offsets[i]);
        set(i+3u,temporary,10);
    }
}

int af_npc_test_composite(unsigned char *mail, unsigned int header, unsigned int a,
                        unsigned int b, unsigned int c, unsigned int footer) {
    ++af_npc_test_calls[3];
    af_npc_test_arguments[0] = (uintptr_t)mail; af_npc_test_arguments[1] = header;
    af_npc_test_arguments[2] = a; af_npc_test_arguments[3] = b;
    af_npc_test_arguments[4] = c; af_npc_test_arguments[5] = footer;
    return 37;
}

void af_npc_test_classic(unsigned char *header, unsigned int *split, unsigned char *footer,
                       unsigned char *body, unsigned int id) {
    ++af_npc_test_calls[4];
    af_npc_test_arguments[0] = (uintptr_t)header; af_npc_test_arguments[1] = (uintptr_t)split;
    af_npc_test_arguments[2] = (uintptr_t)footer; af_npc_test_arguments[3] = (uintptr_t)body;
    af_npc_test_arguments[4] = id;
    *split = 19;
}

const unsigned char *af_npc_test_town(void) { return af_npc_test_land; }
