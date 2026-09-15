#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/campsite_event.h"

static unsigned char donor[12], submitted[4][12];
static unsigned int decoded, input_date, hours;
static int submissions, decodes, one_time;
static unsigned int decode(unsigned int value) { input_date = value; ++decodes; return decoded; }
static unsigned short md(const unsigned char *p) { return ((unsigned short)p[0] << 8) | p[1]; }
static int range(unsigned short today, unsigned short start, unsigned short end) {
    return start <= end ? today >= start && today <= end : today >= start || today <= end;
}
static void add(unsigned short today, const unsigned char *row) {
    int first = row[3], last = row[7], h;
    assert(submissions < 4 && md(row + 10) == 70);
    memcpy(submitted[submissions++], row, 12);
    if (first & 0x40) {
        first &= ~0x40; last &= ~0x40;
        if (today != md(row)) first = 0;
        if (today != md(row + 4)) last = 23;
    }
    for (h = 0; h < 24; ++h) if (h >= first && h <= last) hours |= 1u << h;
}
static void once(int event) { assert(event == 70); ++one_time; }
static AfCampCalendar calendar = {decode, range, add, once, donor, 70};
static void clear_calendar(unsigned int raw) {
    decoded = raw; input_date = hours = 0; submissions = decodes = one_time = 0;
    memset(submitted, 0xCC, sizeof(submitted));
}

static int reset_count, shuffle_count, mark_count, picks[6], visible[6], enabled[238], bad_order;
static unsigned int marked;
static void reset(void) { ++reset_count; }
static void shuffle(int *table, int size, int swaps) {
    int i; assert(size == 6 && swaps == 236); ++shuffle_count;
    for (i = 0; i < 6; ++i) table[i] = 5 - i;
    if (bad_order) table[0] = 6;
}
static int unseen(unsigned int looks) { assert(looks < 6); return visible[looks]; }
static int grow(unsigned int looks) { assert(looks < 6); return picks[looks]; }
static int eligible(int index) { assert(index >= 0 && index < 238); return enabled[index]; }
static void mark(unsigned int actor) { ++mark_count; marked = actor; }
static AfCampSelection selection = {reset, shuffle, unseen, grow, eligible, mark};

static unsigned char save_data[40], greeted;
static int keep, has_saved, allocation_ok, has_visitor, allocations, registrations, placements, removals;
static int manager_object, control_object;
static int check_keep(int event) { assert(event == 70); return keep; }
static void set_keep(int event) { assert(event == 70); keep = 1; }
static void clear_keep(int event) { assert(event == 70); keep = 0; }
static unsigned char *get_save(int event, int id) {
    assert(event == 70 && id == 0); return has_saved ? save_data : 0;
}
static unsigned char *reserve_save(int event, int id) {
    assert(event == 70 && id == 0); ++allocations;
    if (!allocation_ok) return 0;
    has_saved = 1; memset(save_data, 0, sizeof(save_data)); return save_data;
}
static int has_mask(unsigned int mask) { assert(mask == 0xD08F); return has_visitor; }
static int register_mask(unsigned int mask, unsigned int actor, unsigned int cloth) {
    assert(mask == 0xD08F && actor == 0xE0DA && cloth == 0);
    ++registrations; has_visitor = 1; return 1;
}
static void place(void *manager, void *control, unsigned int tent, unsigned char id) {
    assert(manager == &manager_object && control == &control_object && tent == 0x5849 && id == 0x51);
    ++placements;
}
static void remove_tent(void *control, unsigned char id) {
    assert(control == &control_object && id == 0x51); ++removals;
}
static AfCampLifecycle lifecycle = {check_keep, set_keep, clear_keep, get_save, reserve_save,
    has_mask, register_mask, place, remove_tent, &greeted, &selection, 70};

int main(int argc, char **argv) {
    AfCampClock clock = {2026, 6, 6, 6, 9, 0, 0, 1, 1, 0};
    FILE *file;
    unsigned char candidate[4] = {0xCD, 0xCD, 0xCD, 0xCD};
    int i;
    assert(argc == 2);
    file = fopen(argv[1], "rb"); assert(file);
    assert(fread(donor, 1, 12, file) == 12 && fgetc(file) == EOF); fclose(file);
    assert(md(donor + 10) == 24);
    assert(af_v3_campsite_after_day(0x0607, -7, 2026) == 0x051F);
    assert(af_v3_campsite_after_day(0x0601, -1, 2026) == 0x051F);
    assert(af_v3_campsite_after_day(0x061E, 1, 2026) == 0x0701);
    assert(af_v3_campsite_after_day(0x0C1F, 1, 2026) == 0x0101);
    assert(af_v3_campsite_after_day(0x0101, -1, 2026) == 0x0C1F);
    assert(af_v3_campsite_after_day(0x021C, 1, 2000) == 0x021D);
    assert(af_v3_campsite_after_day(0x021C, 1, 1900) == 0x0301);
    assert(af_v3_campsite_after_day(0x0301, -1, 2024) == 0x021D);
    assert(!af_v3_campsite_after_day(0x021D, 1, 2026));
    assert(!af_v3_campsite_after_day(0, 1, 2026));
    assert(!af_v3_campsite_after_day(0x061F, 1, 2026));
    assert(!af_v3_campsite_after_day(0x0601, 8, 2026));

    clear_calendar(0x06060049);
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1);
    assert(input_date == 0x06BE0049 && decodes == 1 && !one_time);
    assert(md(submitted[0]) == 0x0606 && md(submitted[0] + 4) == 0x0607);
    assert(hours == 0xFFFE00 && submitted[0][7] == 14);
    clear_calendar(0x060D0049); clock.day = 7; clock.weekday = 0; clock.hour = 15;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1);
    assert(hours == 0x7FFF && !(hours & (1u << clock.hour)));
    clear_calendar(0x06070049); clock.year = 2025; clock.day = 1;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1);
    assert(md(submitted[0]) == 0x051F && md(submitted[0] + 4) == 0x0601 && hours == 0x7FFF);
    clear_calendar(0x08010049); clock.month = 8; clock.day = 1; clock.weekday = 6;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1 && input_date == 0x08BE0049);
    clear_calendar(0x061C0049); clock.month = 10; clock.day = 2; clock.weekday = 5;
    assert(!af_v3_campsite_schedule(&clock, &calendar));
    assert(input_date == 0x06BE0049);
    clear_calendar(0x061C0049); clock.scene = 35;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1 && hours == 0xFFFFFF);
    assert(submitted[0][3] == 0 && submitted[0][7] == 23 && md(submitted[0]) == 0x0A02);
    clear_calendar(0x061C0049); clock.last_scene = 35; clock.frame = 0;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 2 && one_time == 1);
    assert(submitted[0][3] == 23 && submitted[0][7] == 0 && submitted[1][7] == 23);
    clear_calendar(0x061C0049); clock.scene = 0;
    assert(af_v3_campsite_schedule(&clock, &calendar) == 1 && one_time == 1 && !hours);
    clear_calendar(0x061C0049); clock.frame = 1;
    assert(!af_v3_campsite_schedule(&clock, &calendar) && !one_time);
    clear_calendar(0x061C0049); clock.enabled = 0; clock.scene = 35;
    assert(!af_v3_campsite_schedule(&clock, &calendar) && !decodes);
    clock.enabled = 1; clock.working = 1;
    assert(!af_v3_campsite_schedule(&clock, &calendar) && !decodes);
    clock.working = 0; clock.day = 32;
    assert(!af_v3_campsite_schedule(&clock, &calendar) && !decodes);

    for (i = 0; i < 6; ++i) { visible[i] = 1; picks[i] = -1; }
    picks[4] = 237; picks[3] = 216; picks[2] = 218; enabled[218] = 1;
    assert(!af_v3_campsite_choose(0, &selection) && !reset_count);
    assert(af_v3_campsite_choose(candidate, &selection) == 1);
    assert(md(candidate) == 0xE0DA && candidate[2] == 0xCD && candidate[3] == 0xCD);
    assert(reset_count == 1 && shuffle_count == 1 && mark_count == 1 && marked == 0xE0DA);
    enabled[218] = 0;
    assert(!af_v3_campsite_choose(candidate, &selection) && md(candidate) == 0 && mark_count == 1);
    bad_order = 1; enabled[218] = 1;
    assert(!af_v3_campsite_choose(candidate, &selection) && md(candidate) == 0);
    bad_order = 0; allocation_ok = 1; greeted = 1;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 1);
    assert(keep && allocations == 1 && registrations == 1 && placements == 1 && !greeted);
    assert(md(save_data) == 0xE0DA);
    for (i = 2; i < 40; ++i) assert(save_data[i] == 0);
    greeted = 1;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 2);
    assert(allocations == 1 && registrations == 1 && greeted == 1);
    has_visitor = 0;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 2);
    assert(registrations == 2 && greeted == 1 && allocations == 1);
    assert(af_v3_campsite_stop(&control_object, &lifecycle) == 1 && !keep && removals == 1);
    assert(af_v3_campsite_stop(&control_object, &lifecycle) == 2 && removals == 2);
    has_saved = 0; allocation_ok = 0; has_visitor = 0;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 1);
    assert(allocations == 2 && registrations == 2 && greeted == 1);
    has_saved = 1; save_data[0] = 0xE0; save_data[1] = 0xFF;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 2 && registrations == 2);
    save_data[1] = 218; enabled[218] = 0;
    assert(af_v3_campsite_start(&manager_object, &control_object, &lifecycle) == 2 && registrations == 2);
    puts("pass: donor calendar, month boundaries, selection, and event lifecycle");
    return 0;
}
