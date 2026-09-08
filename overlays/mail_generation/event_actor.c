#include "event_actor.h"

/* Owned by the loaded singleton event-manager image. No allocation or pointer
 * escapes. Native flags 0/1 mean complete/fresh initialization. Values 2..103
 * retain a selected template, item count, and initial capitalization while the
 * native event save retains stock and date. This extends flag semantics, not
 * the save layout. Normal event replacement/save routing needs gameplay proof.
 */
AfEventLeafletPending af_event_pending;
AfEventLeafletWork af_event_work __attribute__((aligned(16)));
unsigned int af_event_count, af_event_busy;

static int af_event_capture(unsigned int flag) {
    unsigned int i, choice;
    if (flag < 2u || flag > 103u) return 0;
    choice = (flag-2u)/2u;
    af_event_pending.template_id = choice < 48u ? 2u+choice/3u : 49u+choice-48u;
    af_event_pending.count = choice < 48u ? 1u+choice%3u : 0u;
    if (choice < 48u && af_event_pending.count > 1u+(af_event_pending.template_id-2u)/4u) return 0;
    af_event_pending.capital = (flag-2u)&1u;
    for (i = 0; i < 156u; ++i) af_event_pending.source[i] = af_event_saved[i];
    af_event_pending.active = flag;
    return 1;
}

int af_event_retry(void) {
    unsigned int i, flag = af_event_init_flag;
    int result;
    if (af_event_busy || af_mail_generation_capital > 1u) return 0;
    if (flag < 2u) {
        af_event_pending.active = 0;
        return flag == 0u;
    }
    if (af_event_pending.active && af_event_pending.active != flag) af_event_pending.active = 0;
    if (!af_event_pending.active && !af_event_capture(flag)) return 0;
    /* Do not publish a cached notice over a changed native event. An ordinary
     * replacement sets flag one and reaches fresh native initialization.
     */
    for (i = 0; i < 156u; ++i)
        if (af_event_pending.source[i] != af_event_saved[i]) return 0;
    af_event_busy = 1;
    result = af_event_leaflet_publish(af_event_pending.source,156u,
        af_event_pending.template_id,af_event_pending.count,&af_event_pending.capital,&af_event_work);
    if (result == 1) {
        /* GC capitalization is sticky. Another letter may set it while this
         * event waits; restoring this event's older zero would lose that state.
         */
        af_mail_generation_capital |= af_event_pending.capital;
        af_event_init_flag = 0;
        af_event_pending.active = 0;
    }
    af_event_busy = 0;
    return result;
}

void af_event_sale_fields(const unsigned char *event, unsigned int count) {
    af_event_count = event == af_event_saved && count >= 1u && count <= 3u ? count : 0u;
    af_event_native_sale_fields(event,count);
}

int af_event_register(unsigned int template_id, unsigned int paper, unsigned int type) {
    unsigned int flag, choice, sale = template_id >= 2u && template_id <= 17u;
    unsigned int count = sale ? af_event_count : 0u;
    if (af_event_busy || af_mail_generation_capital > 1u
            || (sale ? paper != 55u || type != 2u || !count || count > 3u
                       || count > 1u+(template_id-2u)/4u
                     : template_id < 49u || template_id > 51u || paper != 54u || type != 3u)) return 0;
    choice = sale ? (template_id-2u)*3u+count-1u : 48u+template_id-49u;
    flag = 2u+choice*2u+af_mail_generation_capital;
    if (af_event_init_flag >= 2u) {
        if ((af_event_init_flag-2u)/2u != choice) return 0;
        return af_event_retry();
    }
    if (af_event_init_flag != 1u || !af_event_capture(flag)) return 0;
    af_event_init_flag = (unsigned char)flag;
    return af_event_retry();
}

int af_event_special_init(void) {
    int result;
    if (af_event_busy) return 0;
    if (af_event_init_flag != 1u) return af_event_retry();
    af_event_pending.active = af_event_count = 0;
    result = af_event_native_special_init();
    if (result == 1) af_event_init_flag = 0;
    return result;
}

void af_event_save(void *actor, void *game) {
    af_event_retry();
    af_event_native_save(actor,game);
}

void af_event_destroy(void *actor, void *game) {
    af_event_retry();
    af_event_native_destroy(actor,game);
}
