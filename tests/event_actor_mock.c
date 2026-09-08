/* Native owner callbacks only; complete letter generation uses production C. */
#include "../overlays/mail_generation/event_actor.h"

unsigned char af_event_saved[156],af_event_init_flag;
unsigned int af_mail_generation_capital;
unsigned int af_event_test_native_inits,af_event_test_native_fields;
unsigned int af_event_test_native_saves,af_event_test_native_destroys;
unsigned int af_event_test_template,af_event_test_count,af_event_test_nonletter;

void af_event_native_sale_fields(const unsigned char *event,unsigned int count) {
    (void)event;(void)count;++af_event_test_native_fields;
}

int af_event_native_special_init(void) {
    ++af_event_test_native_inits;
    if (af_event_test_nonletter) return af_event_test_nonletter == 1u;
    if (af_event_test_template < 49u) {
        af_event_sale_fields(af_event_saved,af_event_test_count);
        return af_event_register(af_event_test_template,55u,2u);
    }
    return af_event_register(af_event_test_template,54u,3u);
}

void af_event_native_save(void *actor,void *game) {
    (void)actor;(void)game;++af_event_test_native_saves;
}

void af_event_native_destroy(void *actor,void *game) {
    (void)actor;(void)game;++af_event_test_native_destroys;
}
