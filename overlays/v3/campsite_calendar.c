/* Installed native event-directory and clock binding; visitor activation is
 * supplied separately by the event-manager/Animal adapter. */
#include "campsite_event.h"

extern af_camp_u8 campsite_index[128];
extern const AfCampCalendar campsite_calendar;
extern const af_camp_u8 native_rtc[6], selected_furniture[];
extern const int native_scene, native_last_scene;
extern af_camp_u8 *native_game;
extern void native_today_init(void);
extern int native_first_enter(void);
extern int native_add_today(af_camp_u16, const af_camp_u8 *);
extern int native_one_time(int);
extern af_camp_u32 native_decode_date(af_camp_u32);

void af_v3_campsite_today_init(void) {
    unsigned int i;
    native_today_init();
    for (i = 0; i < sizeof(campsite_index); ++i) campsite_index[i] = 255;
}

void af_v3_campsite_add_today(af_camp_u16 today, const af_camp_u8 *row) {
    (void)native_add_today(today, row);
}

void af_v3_campsite_one_time(int event) { (void)native_one_time(event); }

af_camp_u32 af_v3_campsite_decode_date(af_camp_u32 date) {
    unsigned int month = date >> 24, day, encoded;
    /* This adapter accepts only the checked camper template. Native weekly
     * codes use week 9 for current and 15 for last; GC uses 7 and 6. Native
     * current-week decoding also lacks the GC month-end clamp. */
    if ((date & 0xFFFFFFu) != 0xBE0049u || month < 6 || month > 8) return 0;
    if (month > native_rtc[3]) encoded = 0x8E; /* first Saturday */
    else if (month < native_rtc[3]) encoded = 0xFE; /* last Saturday */
    else {
        day = native_rtc[1] + 6u - native_rtc[2];
        if (day <= (month == 6 ? 30u : 31u)) return (date & 0xFF00FFFFu) | (day << 16);
        encoded = 0xFE;
    }
    return native_decode_date((date & 0xFF00FFFFu) | (encoded << 16));
}

static int enabled(void) {
    static const af_camp_u16 items[] = {0x335C,0x3360,0x3364,0x336C,0x3370,0x339C,0x33A4,0x33A8,0x33AC,0x33B0};
    unsigned int i;
    for (i = 0; i < 10; ++i) {
        const af_camp_u8 *row = selected_furniture + ((items[i] - 0x3000) / 4) * 80;
        if ((((unsigned int)row[2] << 8) | row[3]) == items[i]
                && !row[4] && !row[5] && !row[6] && row[7] == 1) return 1;
    }
    return 0;
}

int af_v3_campsite_before_cleanup(void) {
    AfCampClock clock;
    clock.year = ((af_camp_u16)native_rtc[4] << 8) | native_rtc[5];
    clock.month = native_rtc[3]; clock.day = native_rtc[1];
    clock.weekday = native_rtc[2]; clock.hour = native_rtc[0];
    clock.scene = native_scene; clock.last_scene = native_last_scene;
    clock.frame = native_game ? *(af_camp_u32 *)(native_game + 0xA0) : 1;
    clock.enabled = enabled();
    /* This call site is inside the original job gate, after native scene rows
     * and immediately before first-entry/old-event cleanup. */
    clock.working = 0;
    (void)af_v3_campsite_schedule(&clock, &campsite_calendar);
    return native_first_enter();
}
