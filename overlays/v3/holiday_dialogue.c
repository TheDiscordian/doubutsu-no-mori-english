/* One transport for the complete holiday/vacation/card message group. */
#include "holiday_dialogue.h"
typedef unsigned int u32;
static int valid(const AFHolidayDialogue *d) {
    if(!d || d->magic!=0x41464844 || d->version!=1 || d->count!=3)return 0;
    for(u32 i=0;i<3;i++) {
        if(d->ranges[i].first>=d->ranges[i].end || d->ranges[i].end>65536 ||
                d->ranges[i].target>=32768 ||
                d->ranges[i].target+d->ranges[i].end-d->ranges[i].first>32768 ||
                (i && (d->ranges[i-1].end>d->ranges[i].first ||
                    d->ranges[i-1].target+d->ranges[i-1].end-d->ranges[i-1].first!=d->ranges[i].target)))return 0;
    }
    return 1;
}
int af_holiday_message(const AFHolidayDialogue *d,u32 donor) {
    if(!valid(d))return -1;
    for(u32 i=0;i<3;i++)
        if(donor>=d->ranges[i].first && donor<d->ranges[i].end)
            return d->ranges[i].target+donor-d->ranges[i].first;
    return -1;
}
int af_holiday_transport(const AFHolidayDialogue *d,const AFHolidayTransport *o,const AFHolidayAction *a) {
    if(!valid(d) || !o || !a || !o->actor || !o->window || !o->item_name ||
            !o->town_name || !o->item || !o->free_string || !o->turn || !o->camera ||
            !o->message || !o->continuation || !o->listen || !o->start || !o->order ||
            a->effects>255 || ((a->effects&AF_HOLIDAY_CONTINUE) && !(a->effects&AF_HOLIDAY_MESSAGE)) ||
            ((a->effects&AF_HOLIDAY_HANDOVER) && !(a->effects&AF_HOLIDAY_ITEM_NAME)))return 0;
    u32 flags=a->effects;int msg=-1;
    unsigned char item[16],event[16];
    /* Resolve and validate every field before making the first demo mutation. */
    if(flags&AF_HOLIDAY_MESSAGE) {
        msg=af_holiday_message(d,a->message);if(msg<0)return 0;
    }
    if(flags&AF_HOLIDAY_ITEM_NAME)
        if(!a->item || a->item>65535 || !o->item_name(item,sizeof(item),a->item))return 0;
    if(flags&AF_HOLIDAY_EVENT_NAME) {
        if(a->event>=28)return 0;
        u32 used=0;
        if(a->event==4) {
            const unsigned char *town=o->town_name();if(!town)return 0;
            /* Preserve the actual six-character N64 town identity. */
            used=6;while(used && town[used-1]==' ')--used;
            for(u32 i=0;i<used;i++)event[i]=town[i];
        }
        u32 n=16;while(n && d->events[a->event][n-1]==' ')--n;
        if(n+used>sizeof(event))return 0;
        for(u32 i=0;i<n;i++)event[used++]=d->events[a->event][i];
        while(used<sizeof(event))event[used++]=' ';
    }
    if(flags&AF_HOLIDAY_LIGHTHOUSE_DATES)
        for(u32 i=0;i<2;i++)if(!a->lighthouse_dates[i].day || a->lighthouse_dates[i].day>31)return 0;
    if(flags&AF_HOLIDAY_MESSAGE) {
        if(flags&AF_HOLIDAY_CONTINUE)o->continuation(o->window,msg);
        else {o->turn(1);o->camera(3);o->message(msg);}
    }
    if(flags&AF_HOLIDAY_BEGIN) {o->listen();o->start(o->actor);}
    if(flags&AF_HOLIDAY_LIGHTHOUSE_DATES)
        for(u32 i=0;i<2;i++)o->free_string(o->window,i,d->days[a->lighthouse_dates[i].day-1],4);
    if(flags&AF_HOLIDAY_ITEM_NAME)o->item(o->window,0,item,16);
    /* The event uses ITEM_STR1, not free string zero. */
    if(flags&AF_HOLIDAY_EVENT_NAME)o->item(o->window,1,event,16);
    if(flags&AF_HOLIDAY_HANDOVER) {
        o->order(5,0,a->item);o->order(5,1,7);o->order(5,2,0);
    }
    /* END's think/melody restoration belongs to the existing actor controller.
     * No inventory insertion or trophy mutation is repeated by this transport. */
    return 1;
}
