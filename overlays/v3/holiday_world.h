#ifndef AF_V3_HOLIDAY_WORLD_H
#define AF_V3_HOLIDAY_WORLD_H
#include "holiday_npc.h"
#include "npc_registry.h"

/* The event owner supplies its actual special dates. This adapter supplies the
 * native player, inventory, calendar, and saved trophy state, without inventing
 * a Town Day or substituting a different event's attendance. */
int af_holiday_world_bind(AFHolidayNpc *,AFDiaryDates,unsigned int *gender);
int af_holiday_world_variant(void *,unsigned int,unsigned int,unsigned int *);
unsigned int af_holiday_world_resolve(void *,unsigned int);
int af_holiday_world_resources(AFHolidayNpc *);

extern const unsigned char af_holiday_reward_data[];
extern const unsigned char af_holiday_destination_data[];
#ifdef __mips__
#define AFHW_READONLY const
#else
#define AFHW_READONLY
#endif
extern AFHW_READONLY unsigned char af_holiday_players[4][0xBD0],af_holiday_visitor[0xBD0];
extern const unsigned char *volatile af_holiday_active;
extern AFHW_READONLY volatile unsigned char af_holiday_player,af_holiday_rtc[8];
extern AFHW_READONLY unsigned char af_holiday_profiles[1024][80];
extern AFHW_READONLY unsigned char af_holiday_metadata[1024][32];
#undef AFHW_READONLY
extern AFDiary *af_v3_diary_data(void);
extern int af_v3_reward_flag(unsigned int,unsigned int,unsigned int,unsigned int);
extern int af_holiday_native_free(const void *,unsigned short,unsigned int);
extern int af_holiday_native_give(void *,unsigned short,unsigned int);
#endif
