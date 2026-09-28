#ifndef AF_V3_HOLIDAY_FISHING_H
#define AF_V3_HOLIDAY_FISHING_H
#include "diary.h"
typedef unsigned char AFHFB;
typedef unsigned short AFHFH;
typedef struct { AFHFB player_name[8],land_name[8];AFHFH player_id,land_id; } AFHFPerson;
typedef struct { AFHFB sec,min,hour,day,weekday,month;AFHFH year; } AFHFTime;
typedef struct { AFHFPerson pid;AFHFTime time;int size; } AFHFRecord;
enum { AF_HF_RECORDS=5,AF_HF_BYTES=176,AF_HF_CM=0,AF_HF_INCHES=1 };
typedef struct {
    float (*random)(void *);
    int (*player_index)(void *,const AFHFPerson *);
    int (*event_npc)(void *,AFHFH *);
    void (*npc_name)(void *,AFHFB *,AFHFH);
    void (*random_name)(void *,AFHFB *);
} AFHFServices;
typedef struct {
    AFHFRecord fishRecord[AF_HF_RECORDS];
    struct { AFHFTime rtc_time; } time;
    AFDiaryDate scratch_day;
    AFHFServices services;void *opaque;
    unsigned int units,error;
} AFHolidayFish;
/* Complete donor record logic, with explicit caller-owned storage and native
 * services. Serialized records never contain pointers or native short IDs. */
int af_holiday_fish_reset(AFHolidayFish *,unsigned int units);
int af_holiday_fish_clock(AFHolidayFish *,const AFHFTime *);
int af_holiday_fish_units(AFHolidayFish *,unsigned int units);
int af_holiday_fish_store(const AFHolidayFish *,AFHFB *,unsigned int capacity);
int af_holiday_fish_load(AFHolidayFish *,const AFHFB *,unsigned int size,unsigned int units);
int af_holiday_fish_wire_valid(const AFHFB *);
void af_holiday_fish_wire_reset(AFHFB *);
int af_holiday_fish_wire_clear_person(AFHFB *,const AFHFB native[16]);
int af_holiday_fish_set(AFHolidayFish *,const AFHFPerson *,int size);
int af_holiday_fish_size(AFHolidayFish *,int rank);
int af_holiday_fish_npc_size(AFHolidayFish *,unsigned int hour);
int af_holiday_fish_holder(AFHolidayFish *,AFHFPerson *,unsigned int *,AFDiaryDate);
int af_holiday_fish_dates(AFHolidayFish *,AFDiaryDate dates[5]);
/* Finalize all dated records and return a delivery mask. Delivery clears a
 * record only through acknowledge after the actual mail route succeeds. */
int af_holiday_fish_finalize(AFHolidayFish *);
int af_holiday_fish_acknowledge(AFHolidayFish *,unsigned int,const AFHFRecord *);
void af_holiday_fish_native_person(AFHFPerson *,const AFHFB native[16]);
int af_holiday_fish_native_export(AFHFB native[16],const AFHFPerson *);

/* Used by the complete generated donor functions, not substitute algorithms. */
float af_hf_random(AFHolidayFish *);
void af_hf_clear(void *,unsigned int,unsigned int);
void af_hf_copy(void *,const void *,unsigned int);
void af_hf_person_clear(AFHFPerson *);
int af_hf_date_compare(unsigned int,unsigned int,unsigned int,unsigned int,unsigned int,unsigned int);
int af_hf_time_compare(const AFHFTime *,const AFHFTime *);
void af_hf_add_minutes(AFHFTime *,int);
void af_hf_sub_year(AFHFTime *,int);
void af_hf_source_set(AFHolidayFish *,AFHFPerson *,int);
int af_hf_source_size(AFHolidayFish *,int);
int af_hf_source_npc_size(AFHolidayFish *,unsigned char);
void af_hf_source_holder(AFHolidayFish *,AFHFPerson *,unsigned int *,const AFDiaryDate *);
int af_hf_source_dates(AFHolidayFish *,AFDiaryDate *,AFHFTime *);
void af_hf_source_delete_after(AFHolidayFish *,AFDiaryDate *);
void af_hf_source_delete_npc(AFHolidayFish *,AFDiaryDate *);
void af_hf_source_finalize(AFHolidayFish *);
void af_hf_source_sort(AFHolidayFish *);
#endif
