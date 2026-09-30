#ifndef AF_V3_HOLIDAY_HIDING_H
#define AF_V3_HOLIDAY_HIDING_H
#include "holiday_placement.h"
/* A separate extension preserves all existing positional placement readers. */
typedef struct {
    AFHolidayPlacementOps placement;
    const unsigned short *(*foreground)(void *,int,int);
    const unsigned int *(*collision)(void *,int,int);
    int (*hard_allowed)(unsigned short,unsigned int);
    int (*ball)(void *,AFHolidayBlock *);
    int (*marine)(void *,AFHolidayBlock *);
    int (*occupied)(void *,const AFHolidayPlace *);
    int (*free)(void *,unsigned int,AFHolidayPlace *,int);
} AFHolidayHiding;
/* Full donor cover classifiers and masks are generated from the pinned source. */
unsigned short af_holiday_hide_source_item(unsigned short);
void af_holiday_hide_mask(unsigned short *,const unsigned short *);
int af_holiday_hide_unit(int *,int *,int,int,int,const AFHolidayHiding *);
int af_holiday_hide_search(const AFHolidayField *,const AFHolidayHiding *,
    unsigned int,AFHolidayPlace *,int);
int af_holiday_hide_make(const AFHolidayField *,const AFHolidayHiding *,
    unsigned int,unsigned int,unsigned int,int,AFHolidayPlace **);
int af_holiday_hide_walk(const AFHolidayField *,const AFHolidayHiding *,
    unsigned int,unsigned int,unsigned int,int,AFHolidayPlace **);
int af_holiday_hide_show(const AFHolidayField *,const AFHolidayHiding *,
    unsigned int,unsigned int,int,AFHolidayBlock *);
int af_holiday_hide_native_make(void *,unsigned int,unsigned int,unsigned int,int,AFHolidayPlace **);
int af_holiday_hide_native_walk(void *,unsigned int,unsigned int,unsigned int,int,AFHolidayPlace **);
int af_holiday_hide_native_show(void *,unsigned int,unsigned int,int,AFHolidayBlock *);
int af_holiday_hide_native_fluctuation(void *,int *);
#endif
