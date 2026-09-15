#ifndef AF_V3_CAMPSITE_EVENT_H
#define AF_V3_CAMPSITE_EVENT_H

typedef unsigned char af_camp_u8;
typedef unsigned short af_camp_u16;
typedef unsigned int af_camp_u32;

/* Schedule bytes retain the engine's big-endian, twelve-byte representation.
 * The caller owns the extended event directory; passing event 70 to the
 * unmodified N64 directory is NOT supported by this module. */
typedef struct {
    af_camp_u16 year;
    af_camp_u8 month, day, weekday, hour;
    int scene, last_scene;
    af_camp_u32 frame;
    int enabled, working;
} AfCampClock;

typedef struct {
    af_camp_u32 (*decode_date)(af_camp_u32);
    int (*date_range)(af_camp_u16, af_camp_u16, af_camp_u16);
    void (*add_today)(af_camp_u16, const af_camp_u8 *);
    void (*one_time_active)(int);
    const af_camp_u8 *donor_schedule;
    int event;
} AfCampCalendar;

typedef struct {
    void (*reset_appeared)(void);
    void (*shuffle)(int *, int, int);
    int (*unseen)(af_camp_u32);
    int (*grow)(af_camp_u32);
    int (*eligible)(int);
    void (*mark_appeared)(af_camp_u32);
} AfCampSelection;

/* Native adapters must supply a real visitor Animal record, not a town slot.
 * These operations are intentionally unbound until that adapter is installed. */
typedef struct {
    int (*check_keep)(int);
    void (*set_keep)(int);
    void (*clear_keep)(int);
    af_camp_u8 *(*get_save)(int, int);
    af_camp_u8 *(*reserve_save)(int, int);
    int (*has_mask)(af_camp_u32);
    int (*register_mask)(af_camp_u32, af_camp_u32, af_camp_u32);
    void (*place_tent)(void *, void *, af_camp_u32, af_camp_u8);
    void (*remove_tent)(void *, af_camp_u8);
    af_camp_u8 *greeted;
    const AfCampSelection *selection;
    int event;
} AfCampLifecycle;

af_camp_u16 af_v3_campsite_after_day(af_camp_u16, int, af_camp_u16);
int af_v3_campsite_schedule(const AfCampClock *, const AfCampCalendar *);
int af_v3_campsite_choose(af_camp_u8 *, const AfCampSelection *);
int af_v3_campsite_start(void *, void *, const AfCampLifecycle *);
int af_v3_campsite_stop(void *, const AfCampLifecycle *);
#endif
