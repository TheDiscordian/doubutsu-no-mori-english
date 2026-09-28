/* Complete daily-directory bridge, sharing native status and cleanup rather
 * than maintaining a second live event state. Actor activation is separate. */
#include "holiday_native.h"
_Static_assert(sizeof(AFHolidayNativeDay)==16,"Changed native event stride");

int af_holiday_native_type(unsigned int donor) {
    if(donor>=128)return -1;
    unsigned int type=af_holiday_native_ids[donor];
    return type>=AF_HN_FIRST && type<AF_HN_END && af_holiday_source_ids[type]==donor?(int)type:-1;
}
static int directory(void) {
    unsigned int count=0;
    for(unsigned int i=0;i<AF_HN_DAYS;i++) {
        unsigned int type=af_holiday_native_days[i].type;
        if(type==~0u)continue;
        if(type>=128 || af_holiday_native_index[type]!=i)return 0;
        ++count;
    }
    for(unsigned int type=0;type<128;type++) {
        unsigned int i=af_holiday_native_index[type];
        if(i!=255 && (i>=AF_HN_DAYS || af_holiday_native_days[i].type!=type))return 0;
    }
    return count==af_holiday_native_count;
}
int af_holiday_native_merge(const AFHolidayDay *plan,unsigned int count) {
    unsigned char slots[AF_HE_CAPACITY];
    unsigned int next=0;
    if(!plan || count>AF_HE_CAPACITY || !directory())return -1;
    for(unsigned int i=0;i<count;i++) {
        int type=af_holiday_native_type(plan[i].type);
        if(type<0 || plan[i].hours>>24 || !(plan[i].status&AF_HE_EXIST) ||
           plan[i].status&~(AF_HE_EXIST|AF_HE_ACTIVE))return -1;
        for(unsigned int j=0;j<i;j++)if(plan[j].type==plan[i].type)return -1;
        unsigned int slot=af_holiday_native_index[type];
        if(slot==255) {
            while(next<AF_HN_DAYS && af_holiday_native_days[next].type!=~0u)++next;
            if(next==AF_HN_DAYS)return -2;
            slot=next++;
        }
        slots[i]=slot;
    }
    for(unsigned int i=0;i<count;i++) {
        unsigned int type=(unsigned int)af_holiday_native_type(plan[i].type);
        AFHolidayNativeDay *day=&af_holiday_native_days[slots[i]];
        if(day->type==~0u) {
            *day=(AFHolidayNativeDay){type,0,0,0,0,0};
            af_holiday_native_index[type]=slots[i];++af_holiday_native_count;
        }
        day->hours|=plan[i].hours;day->begin=plan[i].begin;day->end=plan[i].end;
        day->status|=AF_HE_EXIST;
    }
    return (int)count;
}
int af_holiday_native_schedule(const AFHolidayClock *clock) {
    AFHolidayDay plan[AF_HE_CAPACITY];
    int n=af_holiday_event_plan(af_holiday_event_data,812,clock,plan,AF_HE_CAPACITY);
    return n<0?n:af_holiday_native_merge(plan,(unsigned int)n);
}
int af_holiday_native_snapshot(AFHolidayDay *out,unsigned int capacity) {
    unsigned int count=0;
    if(!out || capacity>AF_HE_CAPACITY || !directory())return -1;
    for(unsigned int i=0;i<AF_HN_DAYS;i++) {
        unsigned int type=af_holiday_native_days[i].type;
        if(type>=AF_HN_FIRST && type<AF_HN_END)++count;
    }
    if(count>capacity)return -2;
    count=0;
    for(unsigned int i=0;i<AF_HN_DAYS;i++) {
        const AFHolidayNativeDay *d=&af_holiday_native_days[i];
        if(d->type>=AF_HN_FIRST && d->type<AF_HN_END) {
            unsigned int source=af_holiday_source_ids[d->type];
            /* Match native check_status: ERROR masks every other flag. */
            unsigned int status=d->status&AF_HE_ERROR?AF_HE_ERROR:d->status;
            out[count++]=(AFHolidayDay){d->hours,d->begin,d->end,source,status};
        }
    }
    return (int)count;
}
unsigned int af_holiday_native_current(void) {
    AFHolidayDay days[AF_HE_CAPACITY];
    int n=af_holiday_native_snapshot(days,AF_HE_CAPACITY);
    return n<0?255:af_holiday_event_current(af_holiday_event_data,812,days,(unsigned int)n);
}
unsigned int af_holiday_native_field(void) {
    AFHolidayDay days[AF_HE_CAPACITY];
    int n=af_holiday_native_snapshot(days,AF_HE_CAPACITY);
    return n<0?3:af_holiday_event_field(days,(unsigned int)n);
}
int af_holiday_native_cleanup(void) {
    AFHolidayDay days[AF_HE_CAPACITY];
    int n=af_holiday_native_snapshot(days,AF_HE_CAPACITY);
    return n<0?-1:af_holiday_event_cleanup(af_holiday_event_data,812,days,(unsigned int)n);
}
int af_holiday_native_notify(unsigned int donor,void *actor) {
    int type=af_holiday_native_type(donor);
    if(type<0 || !actor || !directory() || af_holiday_native_index[type]==255)return 0;
    af_holiday_native_death(type,actor);
    return 1;
}
