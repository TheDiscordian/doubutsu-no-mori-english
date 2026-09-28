/* Complete native hourly path, with donor sports gates on additive identities.
 * Native/camper cancellation, too-short retention, acre cleanup, and rumours
 * keep their original semantics. Scheduling is never event attendance. */
#include "holiday_active.h"
#include "holiday_native.h"
extern const unsigned char af_holiday_active_hour;
extern short af_holiday_active_too_short;
extern int af_holiday_active_delete;
extern const int af_holiday_active_rumour_count;
extern const unsigned int af_holiday_active_rumours[];
extern int af_holiday_active_set(int);
extern int af_holiday_active_clear(int);
extern int af_holiday_native_check_status(int,int);
extern AFHolidayPlace *af_holiday_native_get_place(int,unsigned char);
extern void af_holiday_active_clear_rumours(void);
extern void af_holiday_active_spread_rumour(int);
_Static_assert(__builtin_offsetof(AFHolidayActiveEvent,changed_num)==6,"Native event changes");
_Static_assert(__builtin_offsetof(AFHolidayActiveEvent,block_x)==12,"Native event acre");
_Static_assert(sizeof(AFHolidayDedicatedCommon)==4,"Imported transient event state");
static void changed(AFHolidayActiveEvent *event,int result) {
    if(result)event->changed_num=(short)((unsigned short)event->changed_num+1u);
}
void af_holiday_active_update(AFHolidayActiveEvent *event) {
    unsigned int hour_mask=1u<<(af_holiday_active_hour&31);
    for(unsigned int i=0;i<AF_HN_DAYS;i++) {
        AFHolidayNativeDay *day=&af_holiday_native_days[i];
        unsigned int type=day->type;
        if(type<128 && af_holiday_native_index[type]!=255) {
            if(af_holiday_native_check_status(type,AF_HE_ERROR))continue;
            unsigned int donor=type>=AF_HN_FIRST && type<AF_HN_END?af_holiday_source_ids[type]:255;
            int over=af_holiday_dedicated_common.fieldday_event_over_status;
            if(donor==16 && over!=16) {
                changed(event,af_holiday_active_clear(type));continue;
            }
            if(day->hours&0x10000000u) {
                changed(event,af_holiday_active_set(type));day->hours&=~0x10000000u;
            } else if(type<AF_HN_FIRST && af_holiday_active_delete==(int)type) {
                /* Native cancellation remains native. None of the imported
                 * owners is in the donor artist..carpet-peddler interval. */
                changed(event,af_holiday_active_clear(type));
                af_holiday_active_delete=0;day->hours=0x20000000u;
            } else if(day->hours&hour_mask) {
                if(over!=-1 && (donor==12 || donor==14 || donor==15)) {
                    changed(event,af_holiday_active_clear(type));continue;
                }
                if(af_holiday_active_too_short==(int)type)day->hours|=0x40000000u;
                else changed(event,af_holiday_active_set(type));
            } else {
                AFHolidayPlace *place=af_holiday_native_get_place(type,81);
                if(af_holiday_active_too_short==(int)type)af_holiday_active_too_short=0;
                else if(!place || place->block.x!=event->block_x || place->block.z!=event->block_z)
                    changed(event,af_holiday_active_clear(type));
            }
        }
        /* Invalid empty rows cannot call the native unchecked index reader. */
        if(day->hours&0x20000000u &&
           (type>=128 || !af_holiday_native_check_status(type,AF_HE_RUN)))day->hours=0;
    }
    af_holiday_active_clear_rumours();
    for(int i=0;i<af_holiday_active_rumour_count;i++)
        if(af_holiday_native_check_status(af_holiday_active_rumours[i],AF_HE_ACTIVE))
            af_holiday_active_spread_rumour(i);
}
int af_holiday_dedicated_current(void *manager,AFHolidayControl *control,
        const AFHolidayDedicatedServices *services,unsigned int phase) {
    return af_holiday_dedicated_native(manager,control,&af_holiday_dedicated_common,services,phase);
}
