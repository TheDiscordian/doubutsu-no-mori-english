#ifndef AF_V3_HOLIDAY_REWARDS_H
#define AF_V3_HOLIDAY_REWARDS_H
typedef unsigned char af_holiday_u8;
typedef unsigned int af_holiday_u32;
/* Transient NPC offer, never part of the saved format. */
struct AfHolidayOffer { af_holiday_u32 event, variant, source_item, item, gender; };
struct AfHolidayOps {
    void *context;
    /* Pure checked mapping: zero means absent, unselected, or unfinished.
       Never cast donor IDs to native IDs without verified correspondence. */
    af_holiday_u32 (*resolve)(void *,af_holiday_u32);
    int (*claimed)(void *,af_holiday_u32);
    int (*give)(void *,af_holiday_u32);
    /* Bound to the validated active player's format-3 trophy flag. */
    void (*mark)(void *,af_holiday_u32);
};
int af_v3_holiday_valid(const af_holiday_u8 *,af_holiday_u32);
int af_v3_holiday_count(const af_holiday_u8 *,af_holiday_u32,af_holiday_u32,af_holiday_u32,const struct AfHolidayOps *);
/* roll is a bounded uniform index in count(), not an unchecked RNG word.
   Complete selections preserve donor variant order and distribution. */
int af_v3_holiday_offer(const af_holiday_u8 *,af_holiday_u32,af_holiday_u32,af_holiday_u32,
    af_holiday_u32,const struct AfHolidayOps *,struct AfHolidayOffer *);
/* Call only when the NPC handover reaches its ordinary delivery point.
   Full pockets/stale selection/duplicate receipt never mark the trophy. */
int af_v3_holiday_commit(const af_holiday_u8 *,af_holiday_u32,const struct AfHolidayOps *,const struct AfHolidayOffer *);
#endif
