#ifndef AF_V3_HARVEST_STATE_H
#define AF_V3_HARVEST_STATE_H
#include "holiday_native.h"
enum {AF_HR_SOURCE=108,AF_HR_NATIVE=116,AF_HR_HARVEST_NATIVE=85,
    AF_HR_REWARDS=12,AF_HR_ALL=4095,AF_HR_NATIVE_AREA_BYTES=40};
typedef struct {
    unsigned char player_name[8],land_name[8];
    unsigned short player_id,land_id;
} AFHarvestPersonalID;
typedef struct {AFHarvestPersonalID pid;unsigned short given_present_bitfield;} AFHarvestSaved;
_Static_assert(sizeof(AFHarvestPersonalID)==20,"Complete source Harvest identity");
_Static_assert(sizeof(AFHarvestSaved)==22,"Complete source Harvest saved record");
_Static_assert(sizeof(AFHarvestSaved)<=AF_HR_NATIVE_AREA_BYTES,"Native event area capacity");
unsigned int af_hr_enabled_mask(void);
unsigned short af_hr_reward(unsigned int);
int af_hr_insert(void *,unsigned short,int);
void af_hr_report(unsigned int,unsigned short);
void af_hr_clear_personal_id(AFHarvestPersonalID *);
int af_hr_calendar_before_cleanup(void);
void *af_hr_get_save(int,int),*af_hr_reserve_save(int,int);
void *af_hr_get_common(int,int),*af_hr_reserve_common(int,int);
void af_hr_set_status(int,int),af_hr_dying(int,void *);
extern const unsigned short af_hr_reward_items[AF_HR_REWARDS];
#endif
