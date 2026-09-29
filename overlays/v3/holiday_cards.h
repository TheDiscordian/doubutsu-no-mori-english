#ifndef AF_V3_HOLIDAY_CARDS_H
#define AF_V3_HOLIDAY_CARDS_H
#include "diary.h"
/* Independent, endian-neutral records. No native Private padding or diary
 * offsets are repurposed. Slot ownership follows the existing town/player
 * save transaction and player-clear hook. */
enum { AF_HC_BYTES=48,AF_HC_PLAYERS=4,AF_HC_STAMPS=12 };
#ifdef AF_V3_CARRIED_NPC
#if !defined(AF_V3_PAPER_PACKS) || !defined(AF_V3_CARRIED_QUEST)
#error Carried NPC storage requires the shared stationery and hunt formats
#endif
enum { AF_HC_CARRIED_WIRE=6 };
#elif defined(AF_V3_PAPER_PACKS)
enum { AF_HC_CARRIED_WIRE=5 };
#elif defined(AF_V3_CARRIED_QUEST)
enum { AF_HC_CARRIED_WIRE=4 };
#else
enum { AF_HC_CARRIED_WIRE=3 };
#endif
typedef struct {AFDiaryDate last_date;unsigned char days;} AFHolidayCard;
int af_holiday_cards_valid(const unsigned char *);
void af_holiday_cards_reset(unsigned char *);
int af_holiday_cards_get(const unsigned char *,unsigned int,AFHolidayCard *);
int af_holiday_cards_set(unsigned char *,unsigned int,const AFHolidayCard *);
int af_holiday_cards_clear(unsigned char *,unsigned int);
/* Version two records the required carried-event families. This is independent
 * of the current stamp count: throwing a card away cannot remove save support. */
int af_holiday_cards_profile(const unsigned char *,unsigned int);
int af_holiday_cards_bind(unsigned char *,unsigned int);
#ifdef AF_V3_EVENT_ITEM_PROFILE
unsigned int af_holiday_cards_enabled(void);
#endif
#ifdef AF_V3_CARRIED_PROFILE
/* Version three keeps the same 48-byte owned allocation. Header byte 8 holds
 * all seven required families; bytes 9..12 hold independent paper ownership.
 * Card stamps remain at their original offsets. */
unsigned int af_carried_save_enabled(void);
int af_carried_save_profile(const unsigned char *,unsigned int,unsigned int);
int af_carried_save_bind(unsigned char *,unsigned int,unsigned int);
int af_carried_paper_collect(unsigned char *,unsigned int,unsigned int);
#ifdef AF_V3_CARRIED_QUEST
/* The town-wide hunt date has no year in the donor. It survives player clear
 * and belongs to the selected spirit family, not an exercise-card slot. */
int af_carried_quest_day(const unsigned char *);
int af_carried_quest_set_day(unsigned char *,unsigned int);
#ifdef AF_V3_CARRIED_NPC
/* Town reward state outlives calendar/event-slot cleanup and player deletion.
 * Wire six keeps the paper mode in bit zero and pending weed clearing in bit
 * one of header byte 15. The actual field renewal consumes the reward. */
int af_carried_quest_weeds(const unsigned char *);
int af_carried_quest_set_weeds(unsigned char *,unsigned int);
#endif
#endif
#endif
#endif
