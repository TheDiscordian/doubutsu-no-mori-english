/* Ev_Soncho2's shared conversation flow connected to diary and reward storage.
 * Native actor scheduling, message routing, and demo transport bind this core;
 * compiling it alone does not install Tortimer or enable diary imports. */
#include "holiday_talk.h"
typedef unsigned int u32;

static int valid(const AFHolidayWorld *w) {
    return w && w->player<=4 && af_diary_valid(w->diary) &&
        w->today.day && w->today.day<=af_diary_days(w->today.year,w->today.month);
}
static int bound(const AFHolidayTalk *t,const AFHolidayWorld *w) {
    return t && valid(w) && t->player==w->player && t->prepared==1 &&
        t->active<=1 && t->phase<=AF_HOLIDAY_WAIT && t->date.day &&
        t->date.day<=af_diary_days(t->date.year,t->date.month) &&
        ((t->event<28 && ((t->event==t->offer.event && t->offer.item) ||
          (t->phase==AF_HOLIDAY_WAIT && !t->offer.item && !t->offer.source_item))) ||
         t->event==101 || t->event==102);
}
static u32 message(u32 event,u32 index) {
    return (event==27?0x3391u:0x3280u+event*10u)+index;
}
static int offset_date(AFDiaryDate *d,u32 days) {
    while(days--) {
        if(++d->day>af_diary_days(d->year,d->month)) {
            d->day=1;
            if(++d->month>12) {
                d->month=1;
                if(d->year==65535)return 0;
                ++d->year;
            }
        }
    }
    return 1;
}
int af_holiday_talk_prepare(AFHolidayTalk *t,const AFHolidayWorld *w,u32 event,
        AFDiaryDate date,u32 gender,u32 variant,u32 repeat,AFHolidayAction *out) {
    if(!t || !out || t->active || !valid(w) || repeat>=3 || gender>1 || !date.day ||
       date.day>af_diary_days(date.year,date.month) ||
       (event>=28 && event!=101 && event!=102))return AF_DIARY_ARGUMENT;
    AFHolidayTalk next={0};AFHolidayAction a={0};
    next.event=event;next.date=date;next.player=w->player;next.prepared=1;
    next.phase=AF_HOLIDAY_WAIT;a.effects=AF_HOLIDAY_MESSAGE;a.event=event;
    if(event==101 || event==102) {
        if(!w->lighthouse_after || !w->lighthouse_start)return AF_DIARY_ARGUMENT;
        int after=w->lighthouse_after(w->context);
        if(after<0 || after>1)return AF_DIARY_ARGUMENT;
        a.message=event==101?0x33F4u:0x340Bu;
        if(after)a.message+=6+repeat;else next.phase=AF_HOLIDAY_LIGHTHOUSE;
    } else {
        if(!w->items.claimed || !w->items.give || !w->items.mark || !w->free_slots)
            return AF_DIARY_ARGUMENT;
        int available=af_v3_holiday_count(w->rewards,w->reward_bytes,event,gender,&w->items);
        if(available<0 || (available && !af_v3_holiday_select(w->rewards,w->reward_bytes,
                event,gender,variant,&w->items,&next.offer)))return AF_DIARY_ARGUMENT;
        if(!available) {
            /* Keep the actual-talk attendance call, but never invent an item,
             * claim a trophy, or enter a handover for an excluded reward. */
            if(variant)return AF_DIARY_ARGUMENT;
            a.message=af_v3_holiday_chat(event);
        } else if(w->player==4) {
            a.message=message(event,9);next.phase=AF_HOLIDAY_VISITOR;
        } else {
            int claimed=w->items.claimed(w->items.context,event);
            int attended=af_diary_calendar_event_check(w->diary,w->player,w->today,date,event);
            if(claimed<0 || claimed>1 || attended<0)return AF_DIARY_ARGUMENT;
            if(claimed) {
                a.message=message(event,attended?6+repeat:5);next.phase=AF_HOLIDAY_CLAIMED;
            } else {
                a.message=message(event,attended?1:0);next.phase=AF_HOLIDAY_BEFORE_GIVE;
            }
        }
    }
    *t=next;*out=a;return AF_DIARY_OK;
}
int af_holiday_talk_start(AFHolidayTalk *t,const AFHolidayWorld *w,AFHolidayAction *out) {
    if(!out || !bound(t,w))return AF_DIARY_ARGUMENT;
    if(t->active)return AF_DIARY_UNCHANGED;
    AFHolidayAction a={0};a.effects=AF_HOLIDAY_BEGIN;a.event=t->event;
    if(t->phase==AF_HOLIDAY_LIGHTHOUSE) {
        if(!w->lighthouse_start)return AF_DIARY_ARGUMENT;
        a.lighthouse_dates[0]=a.lighthouse_dates[1]=w->today;
        if(!offset_date(a.lighthouse_dates,7) || !offset_date(a.lighthouse_dates+1,8))
            return AF_DIARY_ARGUMENT;
        a.effects|=AF_HOLIDAY_LIGHTHOUSE_DATES;
    }
    if(t->phase==AF_HOLIDAY_CLAIMED || t->phase==AF_HOLIDAY_VISITOR) {
        a.item=t->offer.item;a.effects|=AF_HOLIDAY_ITEM_NAME;
        if(t->phase==AF_HOLIDAY_VISITOR)a.effects|=AF_HOLIDAY_EVENT_NAME;
    }
    if(w->player<4) {
        int result=af_diary_calendar_event(w->diary,w->player,t->date,w->dates,t->event);
        if(result<0)return result;
    }
    if(t->phase==AF_HOLIDAY_LIGHTHOUSE)w->lighthouse_start(w->context);
    t->active=1;*out=a;return AF_DIARY_OK;
}
int af_holiday_talk_step(AFHolidayTalk *t,const AFHolidayWorld *w,int continuation,
        int delivered,int ended,AFHolidayAction *out) {
    if(!out || !bound(t,w) || t->active!=1 ||
       (continuation!=0 && continuation!=1) || (delivered!=0 && delivered!=1) ||
       (ended!=0 && ended!=1))return AF_DIARY_ARGUMENT;
    AFHolidayAction a={0};a.event=t->event;
    if(t->phase==AF_HOLIDAY_BEFORE_GIVE && continuation) {
        if(!w->free_slots)return AF_DIARY_ARGUMENT;
        int free=w->free_slots(w->context);
        if(free<0)return AF_DIARY_ARGUMENT;
        a.effects=AF_HOLIDAY_MESSAGE|AF_HOLIDAY_CONTINUE;
        a.message=message(t->event,free?3:2);
        t->phase=free?AF_HOLIDAY_GIVE:AF_HOLIDAY_WAIT;
    } else if(t->phase==AF_HOLIDAY_GIVE && delivered) {
        if(!af_v3_holiday_commit(w->rewards,w->reward_bytes,&w->items,&t->offer)) {
            /* A stale/full-pocket handover cannot silently mark success. Keep
             * the prepared offer so the caller can recover or cancel safely. */
            return AF_DIARY_CHANGED;
        }
        a.effects=AF_HOLIDAY_ITEM_NAME|AF_HOLIDAY_HANDOVER;a.item=t->offer.item;
        t->phase=AF_HOLIDAY_WAIT;
    }
    if(ended) {t->active=0;t->prepared=0;a.effects|=AF_HOLIDAY_END;}
    *out=a;return AF_DIARY_OK;
}
int af_holiday_exercise_attend(const AFHolidayWorld *w,int is_tortimer,u32 event) {
    if(!valid(w) || (is_tortimer!=0 && is_tortimer!=1) || event>255)return AF_DIARY_ARGUMENT;
    if(!is_tortimer || w->player==4)return AF_DIARY_UNCHANGED;
    return af_diary_calendar_event(w->diary,w->player,w->today,w->dates,event);
}
