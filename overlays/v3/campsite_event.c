/* Summer-camper calendar, selection, and event lifecycle.
 * Native directory/visitor binding is a separate required installation step. */
#include "campsite_event.h"

static af_camp_u16 read16(const af_camp_u8 *p) {
    return ((af_camp_u16)p[0] << 8) | p[1];
}

static void write16(af_camp_u8 *p, af_camp_u16 value) {
    p[0] = value >> 8; p[1] = (af_camp_u8)value;
}

static int month_days(int month, af_camp_u16 year) {
    if (month == 2) return 28 + (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
    return 30 + ((0xAD5u >> (month - 1)) & 1u);
}

af_camp_u16 af_v3_campsite_after_day(af_camp_u16 date, int offset, af_camp_u16 year) {
    int month = date >> 8, day = date & 255;
    /* All callers use -7 or +1. Reject bad dates and accidental larger spans. */
    if (month < 1 || month > 12 || day < 1 || day > month_days(month, year)
            || offset < -7 || offset > 7) return 0;
    day += offset;
    if (day <= 0) {
        month = month == 1 ? 12 : month - 1;
        day += month_days(month, year);
    } else if (day > month_days(month, year)) {
        day -= month_days(month, year);
        month = month == 12 ? 1 : month + 1;
    }
    return (af_camp_u16)((month << 8) | day);
}

int af_v3_campsite_schedule(const AfCampClock *clock, const AfCampCalendar *ops) {
    af_camp_u8 row[12];
    af_camp_u32 raw;
    af_camp_u16 today, begin, end;
    int i, calls = 0;
    if (!clock || !ops || !clock->enabled || clock->working) return 0;
    if (clock->month < 1 || clock->month > 12 || !clock->day
            || clock->day > month_days(clock->month, clock->year)
            || clock->weekday > 6 || clock->hour > 23 || ops->event < 70 || ops->event > 118) return 0;
    for (i = 0; i < 12; ++i) row[i] = ops->donor_schedule[i];
    write16(row + 10, (af_camp_u16)ops->event);
    today = ((af_camp_u16)clock->month << 8) | clock->day;
    if (clock->month >= 6 && clock->month <= 8) row[0] = clock->month;
    raw = ops->decode_date(((af_camp_u32)row[0] << 24) | ((af_camp_u32)row[1] << 16)
        | ((af_camp_u32)row[2] << 8) | row[3]);
    begin = (af_camp_u16)(raw >> 16);
    if (clock->weekday == 0) begin = af_v3_campsite_after_day(begin, -7, clock->year);
    end = af_v3_campsite_after_day(begin, 1, clock->year);
    if (begin && end && ops->date_range(today, begin, end)) {
        write16(row, begin); row[2] = (af_camp_u8)(raw >> 8); row[3] = (af_camp_u8)raw;
        write16(row + 4, end);
        ops->add_today(today, row); ++calls;
    }
    /* Preserve the donor's separately ordered exit-frame and inside-tent rows.
     * 23..0 supplies no ordinary active hours, but requests one-time activity. */
    for (i = 0; i < 12; ++i) row[i] = 0;
    write16(row, today); write16(row + 4, today);
    write16(row + 10, (af_camp_u16)ops->event);
    if (clock->last_scene == 35 && clock->frame == 0) {
        row[3] = 23;
        ops->add_today(today, row); ops->one_time_active(ops->event); ++calls;
    }
    if (clock->scene == 35) {
        row[3] = 0; row[7] = 23;
        ops->add_today(today, row); ++calls;
    }
    /* This counts submitted rows, not successfully allocated today slots. */
    return calls;
}

int af_v3_campsite_choose(af_camp_u8 *saved, const AfCampSelection *ops) {
    int personalities[6], i, index;
    if (!saved || !ops) return 0;
    write16(saved, 0);
    ops->reset_appeared();
    /* The supplied donor swaps this six-entry table NPC_NUM (236) times. */
    ops->shuffle(personalities, 6, 236);
    for (i = 0; i < 6; ++i) {
        if (personalities[i] < 0 || personalities[i] >= 6) return 0;
        if (ops->unseen((af_camp_u32)personalities[i]) <= 0) continue;
        index = ops->grow((af_camp_u32)personalities[i]);
        if (index < 0 || index >= 238 || index == 216 || index == 217 || !ops->eligible(index)) continue;
        write16(saved, (af_camp_u16)(0xE000u | (unsigned int)index));
        ops->mark_appeared(read16(saved));
        return 1;
    }
    return 0;
}

int af_v3_campsite_start(void *manager, void *control, const AfCampLifecycle *ops) {
    af_camp_u8 *saved;
    af_camp_u16 animal;
    int result = 2;
    if (!ops->check_keep(ops->event)) { ops->set_keep(ops->event); result = 1; }
    saved = ops->get_save(ops->event, 0);
    if (!saved) {
        saved = ops->reserve_save(ops->event, 0);
        if (saved) {
            af_v3_campsite_choose(saved, ops->selection);
            *ops->greeted = 0;
        }
    }
    if (saved) {
        animal = read16(saved);
        if (animal >= 0xE000u && animal < 0xE0EEu && animal != 0xE0D8u && animal != 0xE0D9u
                && ops->selection->eligible(animal & 255u) && !ops->has_mask(0xD08Fu))
            ops->register_mask(0xD08Fu, animal, 0);
    }
    ops->place_tent(manager, control, 0x5849u, 0x51u);
    return result;
}

int af_v3_campsite_stop(void *control, const AfCampLifecycle *ops) {
    int result = 2;
    if (ops->check_keep(ops->event)) { ops->clear_keep(ops->event); result = 1; }
    ops->remove_tent(control, 0x51u);
    return result;
}
