#ifndef AF_V3_CARRIED_QUEST_H
#define AF_V3_CARRIED_QUEST_H
#include "holiday_cards.h"
#include "holiday_native.h"
enum {AF_CW_SOURCE=114,AF_CW_NATIVE=115,AF_CW_SAVED=54,AF_CW_COMMON=55};
typedef struct {
    unsigned char x[5],z[5];unsigned short flags;unsigned char reserved[32];
} AFCarriedQuestCommon;
_Static_assert(sizeof(AFCarriedQuestCommon)==44,"Complete source quest common state");
typedef struct {unsigned int present,keep;AFCarriedQuestCommon common;void *placement;} AFCarriedQuest;
/* One means eligible, zero means a future date, negative means invalid input.
 * Replanning only draws randomness when the stored date expires. */
int af_cw_plan(unsigned char *,AFDiaryDate,float (*)(void));
int af_cw_calendar_before_cleanup(void);
void af_cw_finish_hunt(void);
void *af_cw_get_save(int,int),*af_cw_reserve_save(int,int);
void *af_cw_get_common(int,int),*af_cw_reserve_common(int,int);
int af_cw_check_keep(int);
void af_cw_set_keep(int),af_cw_clear_keep(int);
void **af_cw_placement(void);
extern AFCarriedQuest af_cw_state;
#ifdef __mips__
extern const unsigned int af_cw_available;
#else
extern unsigned int af_cw_available;
#endif
#endif
