/* Appended to the complete English event-letter owner. All old control and
 * letter-work addresses stay intact. The native dispatcher owns retries. */
#include "campsite_manager.h"

static const AfCampSelection selection = {
    native_reset_appeared, native_shuffle, native_unseen, native_grow,
    selected_villager, native_mark_appeared
};

static int enabled(void) {
    static const camp_u16 items[] = {0x335C,0x3360,0x3364,0x336C,0x3370,0x339C,0x33A4,0x33A8,0x33AC,0x33B0};
    unsigned int i;
    if (native_installed != 1) return 0;
    for (i = 0; i < 10; ++i) {
        const camp_u8 *p = selected_furniture + ((items[i]-0x3000)/4)*80;
        if ((((camp_u16)p[2]<<8)|p[3])==items[i]
                && !p[4] && !p[5] && !p[6] && p[7]==1) return 1;
    }
    return 0;
}

static AfCampToday *today(void) {
    unsigned int i = native_event_index[70];
    return i<16 && native_today[i].type==70 ? native_today+i : 0;
}

int af_v3_camper_event_start(void *manager, AfCampControl *control) {
    camp_u8 *saved;
    camp_u32 animal;
    AfCampToday *event;
    int keep;
    if (!control || control->type!=70 || !enabled()) return 0;
    event = today();
    if (!event || !native_field_valid()) return 0;
    saved = native_get_save(70,0);
    if (!saved) {
        /* Do not choose or clear state under an existing masked actor. Native
         * scene setup clears aliases before a genuinely new event can start. */
        if (native_event(0xD08F)) return 0;
        saved = native_reserve_save(70,0);
        if (!saved) return 0;
        if (!af_v3_campsite_choose(saved,&selection)) {
            native_clear_save(70,0);
            return 0;
        }
        camper.greeted = 0;
    }
    animal = ((camp_u32)saved[0]<<8)|saved[1];
    if (!af_v3_camper_register(0xD08F,animal,0)) return 0;
    if (!(native_field_id()&0xF000)) {
        AfCampPlace *place = native_get_place(70,0x51);
        camp_u16 foreground = 0;
        if (place && place->foreground==0x5849)
            (void)native_get_fg(&foreground,place->block_x,place->block_z,place->unit_x,place->unit_z);
        /* Retain a successfully placed tent on a repeated start. A live
         * exterior temporarily changes its centre to F127. */
        if (foreground!=0x5849 && foreground!=0xF127) {
            camp_u16 status = event->status;
            camp_u32 changes = native_changes;
            if (!native_place_tent(manager,control,0x5849,0x51)) {
                /* Native ERROR is an abort, not a retry flag: setting it
                 * clears all other statuses and masks their readers. Keep
                 * the pending transition and original change word instead. */
                event->status = status;
                native_changes = changes;
                return 0;
            }
        }
    }
    /* Indoors the same saved visitor must register, but there is no outdoor
     * field in which to place a tent. Placement runs on returning outdoors. */
    keep = native_check_keep(70);
    native_set_keep(70);
    native_clear_status(70,0x20);
    return keep ? 2 : 1;
}

int af_v3_camper_event_stop(void *manager, AfCampControl *control) {
    AfCampToday *event;
    camp_u16 status;
    camp_u32 changes;
    int keep;
    (void)manager;
    if (!control || control->type!=70 || native_installed!=1) return 0;
    event = today();
    if (!event) return 0;
    status = event->status;
    changes = native_changes;
    /* Preserve keep/start state if native removal fails, so the dispatcher
     * retries. Do not unregister an Animal that a live actor may still use. */
    if (!native_remove_tent(control,0x51)) {
        event->status = status;
        native_changes = changes;
        return 0;
    }
    keep = native_check_keep(70);
    native_clear_keep(70);
    native_clear_status(70,0x20);
    return keep ? 1 : 2;
}

int af_v3_camper_event_in(void *manager, AfCampControl *control) {
    (void)manager;
    return control && control->type==70;
}

int af_v3_camper_event_out(void *manager, AfCampControl *control) {
    return af_v3_camper_event_in(manager,control);
}
