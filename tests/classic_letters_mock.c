#include <stddef.h>
#include <string.h>
#include "../overlays/classic_letters/classic.h"

unsigned char af_npc_word_data[AF_NPC_WORD_BYTES], af_npc_alias_data[AF_NPC_ALIAS_BYTES];
unsigned char af_classic_test_fields[200];
unsigned int af_classic_test_loads, af_classic_test_fallbacks, af_classic_test_delegations;
unsigned int af_classic_test_fail_load, af_classic_test_capital, af_classic_test_flushes, af_classic_test_errors;
volatile unsigned int af_classic_test_entry[2];

unsigned int af_classic_test_mask(unsigned int number) { return af_classic_mask(number); }
unsigned int af_classic_test_work_bytes(void) { return sizeof(AfNpcMailCreateWork); }
unsigned int af_classic_test_text_offset(void) { return offsetof(AfNpcMailCreateWork, generation.text); }

int af_notice_seasonal_create(AfNpcMailCreateWork *work, unsigned char *destination,
                              AfNpcMailSession **active, unsigned int *capital) {
    (void)work; (void)destination; (void)active; (void)capital;
    ++af_classic_test_delegations;
    return 7;
}

/* Unchanged NPC metadata generation is not part of this isolated fixture. */
void af_npc_creator_test_clear(unsigned char *mail) { (void)mail; ++af_classic_test_errors; }
void af_npc_creator_test_metadata(unsigned char *mail, const unsigned char *player,
                                  const unsigned char *animal, const unsigned char *remail,
                                  unsigned int condition, unsigned int foreign) {
    (void)mail; (void)player; (void)animal; (void)remail; (void)condition; (void)foreign;
    ++af_classic_test_errors;
}
int af_npc_mail_sources_init(AfNpcMailSources *out, const unsigned char *words, unsigned int word_size,
                              const unsigned char *aliases, unsigned int alias_size) {
    (void)out; (void)words; (void)word_size; (void)aliases; (void)alias_size;
    ++af_classic_test_errors; return 0;
}
int af_npc_mail_capture_event(AfNpcMailSession *session, unsigned int event, const void *data, unsigned int value) {
    (void)session; (void)event; (void)data; (void)value;
    ++af_classic_test_errors; return 0;
}

unsigned char *af_npc_mail_load(unsigned char *destination, const unsigned char *player,
                                const unsigned char *animal, const unsigned char *remail,
                                unsigned int condition, unsigned int foreign) {
    AfNpcMailCreateWork work __attribute__((aligned(16)));
    AfNpcMailSession *active = 0;
    ++af_classic_test_loads;
    if (af_classic_test_fail_load) return 0;
    memset(&work, 0x5A, sizeof(work));
    work.captured.session.player = player; work.captured.session.animal = animal;
    work.captured.session.remail = remail; work.captured.session.condition = condition;
    work.captured.session.foreign = foreign;
    return af_classic_mail_create(&work, destination, &active, &af_classic_test_capital) == 1 ? destination : 0;
}

void af_classic_test_sized(unsigned char *header, unsigned int header_size, unsigned int *split,
                           unsigned char *footer, unsigned int footer_size, unsigned char *body, unsigned int number) {
    (void)number; ++af_classic_test_fallbacks;
    if (header_size != 10u || footer_size != 16u) { ++af_classic_test_errors; return; }
    memset(header, 'H', 10u); memset(body, 'B', 96u); memset(footer, 'F', 16u); *split = 3u;
}
void af_classic_test_writeback(void *pointer, unsigned int bytes) {
    if (pointer != (void *)af_classic_test_entry || bytes != 8u) ++af_classic_test_errors;
    ++af_classic_test_flushes;
}
void af_classic_test_invalidate(void *pointer, unsigned int bytes) {
    af_classic_test_writeback(pointer, bytes);
}
