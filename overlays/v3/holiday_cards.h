#ifndef AF_V3_HOLIDAY_CARDS_H
#define AF_V3_HOLIDAY_CARDS_H
#include "diary.h"
/* Independent, endian-neutral records. No native Private padding or diary
 * offsets are repurposed. Slot ownership follows the existing town/player
 * save transaction and player-clear hook. */
enum { AF_HC_BYTES=48,AF_HC_PLAYERS=4,AF_HC_STAMPS=12 };
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
#endif
