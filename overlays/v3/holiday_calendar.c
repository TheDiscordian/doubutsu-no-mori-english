/* A shared calendar choice for original and imported event owners. This does
 * not enable actors or write attendance. Native hourly/acre dispatch still
 * owns ACTIVE, RUN, SHOW, cancellation, and cleanup. */
#include "holiday_calendar.h"
#include "holiday_state.h"
#include "npc_registry.h"
extern const unsigned int af_hp_available;
extern const unsigned char af_holiday_rtc[8];
extern AFDiary *af_v3_diary_data(void);

static int imported_owner(int native) {
    switch(native) {
    case 1:return 41;case 3:return 1;case 6:return 64;
    case 7:return 12;case 8:return 13;case 9:return 14;case 10:return 15;
    case 12:return 20;case 16:return 35;case 18:return 11;case 22:return 43;
    default:return -1;
    }
}

unsigned int af_holiday_calendar_mode(void) {
    const AFNpcExtras *t=&af_v3_npc_extras;
    if(!af_hp_available || af_holiday_calendar_choice>1 ||
       t->magic!=AF_NPC_EXTRA_MAGIC || t->version!=1 || t->stride!=44 ||
       !t->count || t->count>AF_NPC_EXTRA_MAX)return AF_HCAL_ORIGINAL;
    for(unsigned int i=0;i<t->count;i++)
        if(t->rows[i].name==0xD090 && t->rows[i].profile==0xCC && t->rows[i].flags==3)
            return af_holiday_calendar_choice?AF_HCAL_GC:AF_HCAL_N64;
    return AF_HCAL_ORIGINAL;
}
int af_holiday_calendar_dates(const AFDiary *s,unsigned int year,AFDiaryDates *out) {
    if(!out)return 0;
    if(af_holiday_calendar_mode()==AF_HCAL_ORIGINAL) {*out=(AFDiaryDates){0,0,0};return 1;}
    /* The diary can browse eleven months across either end of the native
     * lunar table. Keep its Gregorian holidays without indexing outside that
     * table or inventing a moon-viewing date. Live clocks remain table-bound. */
    if(year==1999 || year==2033) {
        if(!af_diary_valid(s) || s->bytes[5]!=2 || !s->bytes[6])return 0;
        *out=(AFDiaryDates){s->bytes[6],0,0};return 1;
    }
    AFDiaryDates d;
    if(!af_holiday_state_dates(s,year,&d))return 0;
    if(af_holiday_calendar_mode()==AF_HCAL_N64) {
        AFDiaryDate moon;
        if(!af_diary_event_endpoint(&moon,af_diary_event_master[50][0],
                (AFDiaryDate){year,1,1}))return 0;
        d.harvest_month=moon.month;d.harvest_day=moon.day;
    }
    *out=d;return 1;
}
int af_holiday_calendar_clock(AFDiaryDate date,AFHolidayClock *out) {
    if(!out || !date.day || date.day>af_diary_days(date.year,date.month))return 0;
    AFDiaryDates special;AFDiary *live=af_v3_diary_data();
    if(!live || !af_diary_valid(live))return 0;
    if(!live->bytes[6] && !af_holiday_state_init(live,(unsigned int)(af_holiday_random_native()*30.0f)))return 0;
    if(!af_holiday_calendar_dates(live,date.year,&special) || !special.town_day)return 0;
    int y=(int)date.year-1980;
    *out=(AFHolidayClock){date,special,12,0,
        (unsigned int)((int)(20.8431f+0.242194f*(float)y)-y/4),
        (unsigned int)((int)(23.2488f+0.242194f*(float)y)-y/4),1};
    return 1;
}
void *af_holiday_calendar_copy(void *destination,const void *source,unsigned int bytes) {
    unsigned char *d=destination;const unsigned char *s=source;
    for(unsigned int i=0;i<bytes;i++)d[i]=s[i];
    /* This replaces only the scheduler's exact twelve-byte row copy. Never
     * change the master table, the live RTC, or an unrelated memcpy caller. */
    unsigned int mode=af_holiday_calendar_mode();
    if(bytes!=12 || mode==AF_HCAL_ORIGINAL)return destination;
    const unsigned int (*master)[3]=af_diary_event_master;
    unsigned int index=81;
    for(unsigned int i=0;i<81;i++)if(source==master+i) {index=i;break;}
    if(index==81)return destination;
    if(imported_owner(master[index][2])>=0) {
        /* The complete imported owner is scheduled below. Suppress only this
         * original directory entry, so two controllers cannot spawn for it. */
        ((unsigned int *)destination)[0]=((unsigned int *)destination)[1]=0;return destination;
    }
    if(mode!=AF_HCAL_GC || !af_holiday_calendar_native_sources[index][0])return destination;
    if(af_holiday_calendar_native_sources[index][0]==255) {
        ((unsigned int *)destination)[0]=((unsigned int *)destination)[1]=0;return destination;
    }
    AFDiaryDate date={(unsigned int)af_holiday_rtc[6]*256+af_holiday_rtc[7],
        af_holiday_rtc[5],af_holiday_rtc[3]};
    AFHolidayClock clock;unsigned int dates[2];
    if(!af_holiday_calendar_clock(date,&clock) ||
       af_holiday_event_dates(&clock,af_holiday_calendar_native_sources[index],dates)!=1)
        return destination;
    ((unsigned int *)destination)[0]=dates[0];
    ((unsigned int *)destination)[1]=dates[1];
    return destination;
}
int af_holiday_calendar_schedule(const AFHolidayClock *clock) {
    unsigned int mode=af_holiday_calendar_mode();
    if(mode==AF_HCAL_ORIGINAL)return 0;
    if(!clock)return -1;
    AFHolidayDay plan[AF_HE_CAPACITY];unsigned int dates[49][2]={{0}};
    AFHolidayClock selected=*clock;
    if(!af_holiday_calendar_dates(af_v3_diary_data(),clock->date.year,&selected.special))return -1;
    if(mode==AF_HCAL_N64)for(unsigned int i=0;i<49;i++) {
        unsigned int row=af_holiday_calendar_donor_rows[i];
        if(row==255)continue;
        if(row>=81)return -1;
        for(unsigned int end=0;end<2;end++) {
            AFDiaryDate date;unsigned int word=af_diary_event_master[row][end];
            if(!af_diary_event_endpoint(&date,word,clock->date)) {
                /* A current-week weekday outside this month cannot match.
                 * Day zero retains that native sentinel without indexing a
                 * calendar array or turning it into another holiday. */
                dates[i][end]=(clock->date.month<<24)|(word&255);
            } else dates[i][end]=(unsigned int)date.month<<24|(unsigned int)date.day<<16|(word&255);
        }
    }
    int n=af_holiday_event_plan_dates(af_holiday_event_data,812,&selected,plan,
        AF_HE_CAPACITY,mode==AF_HCAL_N64?dates:0);
    return n<0?n:af_holiday_native_merge(plan,(unsigned int)n);
}
static const AFHolidayNativeDay *observation(int type) {
    if(type<0 || type>=128)return 0;
    if(af_holiday_calendar_mode()!=AF_HCAL_ORIGINAL) {
        int source=imported_owner(type);
        if(source>=0) {type=af_holiday_native_type(source);if(type<0)return 0;}
    }
    unsigned int slot=af_holiday_native_index[type];
    if(slot>=AF_HN_DAYS || af_holiday_native_days[slot].type!=(unsigned int)type)return 0;
    return af_holiday_native_days+slot;
}
int af_holiday_calendar_status(int type,int mask) {
    const AFHolidayNativeDay *d=observation(type);
    if(!d)return 0;
    mask=(short)mask;
    if(mask!=AF_HE_ERROR && d->status&AF_HE_ERROR)return 0;
    return (d->status&mask)!=0;
}
int af_holiday_calendar_today(int type) {
    const AFHolidayNativeDay *d=observation(type);
    return d && !(d->status&AF_HE_STOP) && !(d->hours&0x40000000u) &&
        (d->hours&(1u<<(af_holiday_rtc[2]&31)))!=0;
}
int af_holiday_calendar_run_today(int type) {
    const AFHolidayNativeDay *d=observation(type);
    return d && !(d->status&AF_HE_STOP) && d->hours!=0;
}
int af_holiday_calendar_owner_today(int type) {
    /* Only the manager's control-list builder uses this unaliased admission.
     * Ordinary native readers observe imported status, but original callbacks
     * must never read an imported actor's differently laid-out save area. */
    if(af_holiday_calendar_mode()!=AF_HCAL_ORIGINAL && imported_owner(type)>=0)return 0;
    return af_holiday_calendar_run_today(type);
}
