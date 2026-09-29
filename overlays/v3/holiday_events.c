/* GAFE01 event scheduling and owner lifecycle. The native adapter must provide
 * actual special dates, event-specific owners, placement, and culling services.
 * These routines never substitute an ordinary NPC for an unported owner. */
#include "holiday_events.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
static u32 be16(const u8 *p) {return (u32)p[0]<<8|p[1];}
static int packet(const u8 *p,u32 n) {
    return p && n>=48 && p[0]=='A' && p[1]=='F' && p[2]=='H' && p[3]=='E' &&
        be16(p+4)==1 && be16(p+6)==49 && be16(p+8)==44 && be16(p+10)==12 &&
        be16(p+12)==4 && !be16(p+14) && n==48+49*12+44*4;
}
static int clock_valid(const AFHolidayClock *c) {
    return c && c->date.year && c->date.day && c->hour<24 && c->working<=1 &&
        c->date.day<=af_diary_days(c->date.year,c->date.month) &&
        c->special.town_day>=1 && c->special.town_day<=31 &&
        c->special.harvest_month>=1 && c->special.harvest_month<=12 &&
        c->special.harvest_day>=1 &&
        c->special.harvest_day<=af_diary_days(c->date.year,c->special.harvest_month) &&
        c->vernal_day>=19 && c->vernal_day<=21 && c->autumnal_day>=21 &&
        c->autumnal_day<=23 && c->vacation_available<=1;
}
static int browsing_clock_valid(const AFHolidayClock *c) {
    if(clock_valid(c))return 1;
    if(!c || (c->date.year!=1999 && c->date.year!=2033) ||
       c->special.harvest_month || c->special.harvest_day)return 0;
    AFHolidayClock checked=*c;
    checked.special.harvest_month=9;checked.special.harvest_day=1;
    return clock_valid(&checked);
}
static u32 weekday(const AFHolidayClock *c,u32 month,u32 encoded) {
    u32 week=(encoded>>3)&7,target=encoded&7,day=0,last=af_diary_days(c->date.year,month);
    int first=af_diary_weekday((AFDiaryDate){c->date.year,month,1});
    if(!last || target>6 || first<0)return 0;
    if(week==7) {
        if(month>c->date.month)week=1;
        else if(month<c->date.month)week=6;
        else {
            /* The source stores this subtraction in an unsigned byte. */
            day=(u8)(c->date.day-(af_diary_weekday(c->date)-(int)target));
            week=day>last?6:0;
        }
    }
    if(week==6) {
        int end=(last-1+first)%7;
        day=target<=(u32)end?last-(end-target):last-(end-target)-7;
    } else if(week)day=target>=(u32)first?1+(week-1)*7+target-first:1+week*7+target-first;
    return day;
}
static u32 decode(const AFHolidayClock *c,const u8 *raw,u32 equinox,u32 *hour) {
    u32 month=raw[0],day=equinox?equinox:raw[1];
    *hour=raw[3];
    /* All selected source rows use literal, current, or lunar months. Save-slot
     * dates/hours are deliberately rejected rather than reading invented data. */
    if(raw[2] || month&0x10 || *hour&0x20)return 0;
    if(month&0x20)month=c->date.month;
    else if(month&0x40) {month=c->special.harvest_month;day=c->special.harvest_day;}
    if(month<1 || month>12)return 0;
    if(day&0x80) {
        u32 encoded=day;day=weekday(c,month,day&~0x40u);
        if(encoded&0x40) {
            ++day;
            if(day>af_diary_days(c->date.year,month)) {day-=af_diary_days(c->date.year,month);month=month==12?1:month+1;}
        }
    } else if(day&0x20)day=af_diary_days(c->date.year,month);
    else if(day&0x40)day=(day&~0x40u)|c->special.town_day;
    /* Preserve a source current-week day zero: it cannot match today's date,
     * but is not an invalid entire calendar. */
    return month<<8|day;
}
static int range(u32 now,u32 start,u32 end) {
    return start>end?(now>=start || now<=end):(now>=start && now<=end);
}
int af_holiday_event_dates(const AFHolidayClock *c,const u8 row[12],u32 dates[2]) {
    if(!browsing_clock_valid(c) || !row || !dates || be16(row+8))return -1;
    u32 type=be16(row+10),adjust=0,h1,h2;
    if(!c->special.harvest_month && (type==42 || (row[0]|row[4])&0x40))return 0;
    if(type==11 || type==82 || type==41 || type==96 || (type>=12 && type<=16) || type==111)
        adjust=row[0]==3?c->vernal_day:row[0]==9?c->autumnal_day:0;
    u8 changed[12];for(u32 i=0;i<12;i++)changed[i]=row[i];
    if(type==10 || type==40) {
        u32 day=type==10?c->vernal_day:c->autumnal_day;
        changed[1]=day-10;changed[5]=day-1;
    } else if(type==42) {
        AFDiaryDate end={c->date.year,c->special.harvest_month,c->special.harvest_day};
        for(u32 i=1;i<=7;i++) {
            if(!--end.day) {
                if(!--end.month) {--end.year;end.month=12;}
                end.day=af_diary_days(end.year,end.month);
            }
            if(i==1) {changed[4]=end.month;changed[5]=end.day;}
        }
        changed[0]=end.month;changed[1]=end.day;
    }
    u32 a=decode(c,changed,adjust,&h1),b=decode(c,changed+4,adjust,&h2);
    if(!a || !b || (h1&31)>23 || (h2&31)>23)return -1;
    dates[0]=(a<<16)|h1;dates[1]=(b<<16)|h2;return 1;
}
int af_holiday_event_plan_dates(const u8 *p,u32 n,const AFHolidayClock *c,AFHolidayDay *out,
        u32 capacity,const u32 dates[49][2]) {
    if(!packet(p,n) || !clock_valid(c) || !out || capacity>AF_HE_CAPACITY)return -1;
    if(c->working)return 0;
    AFHolidayDay days[AF_HE_CAPACITY];u32 count=0,equinox=0,preferred=255;
    u32 today=(u32)c->date.month<<8|c->date.day;
    for(u32 i=0;i<49;i++) {
        const u8 *r=p+48+i*12;u32 type=be16(r+10),adjust=0,h1,h2;
        if(be16(r+8) || type>=128)return -1;
        if((type==4 || type==5) && !c->vacation_available)continue;
        if((type==90 || type==102) && preferred!=255)continue;
        int mapped=dates && (dates[i][0] || dates[i][1]);
        if(!mapped && (type==11 || type==82 || type==41 || type==96)) {
            u32 month=(type==11 || type==82)?3:9;
            u32 day=month==3?c->vernal_day:c->autumnal_day;
            if(c->date.month!=month || c->date.day!=day)continue;
            equinox=adjust=day;
        } else if(!mapped && type>=12 && type<=16) {if(!equinox)continue;adjust=equinox;}
        u32 start,end;
        if(mapped) {
            start=dates[i][0]>>16;end=dates[i][1]>>16;
            h1=dates[i][0]&255;h2=dates[i][1]&255;
            if((dates[i][0]|dates[i][1])&0xFF00u || (h1|h2)&0x20u ||
               (start>>8)<1 || (start>>8)>12 || (end>>8)<1 || (end>>8)>12 ||
               (start&255)>af_diary_days(c->date.year,start>>8) ||
               (end&255)>af_diary_days(c->date.year,end>>8))return -1;
        } else {start=decode(c,r,adjust,&h1);end=decode(c,r+4,adjust,&h2);}
        if(!start || !end)return -1;
        if(!range(today,start,end))continue;
        if(type==89 || type==101)preferred=type;
        u32 begin=start,finish=end;
        if(h1&0x80) {begin=finish=today;h1&=~0x80u;h2&=~0x80u;}
        if(h1&0x40) {
            h1&=~0x40u;h2&=~0x40u;
            if(today!=start)h1=0;
            if(today!=end)h2=23;
        }
        if(h1>23 || h2>23)return -1;
        u32 index=0,hours=0;
        for(u32 h=0;h<24;h++)if(h1<=h && h<=h2)hours|=1u<<h;
        while(index<count && days[index].type!=type)++index;
        if(index==count) {
            if(count==capacity)return -2;
            days[count++]=(AFHolidayDay){0,0,0,type,0};
        }
        days[index].hours|=hours;days[index].begin=begin;days[index].end=finish;
        days[index].status=AF_HE_EXIST;
        if(hours&(1u<<c->hour))days[index].status|=AF_HE_ACTIVE;
    }
    for(u32 i=0;i<count;i++)out[i]=days[i];
    return (int)count;
}
int af_holiday_event_plan(const u8 *p,u32 n,const AFHolidayClock *c,AFHolidayDay *out,u32 capacity) {
    return af_holiday_event_plan_dates(p,n,c,out,capacity,0);
}
int af_holiday_event_owner(const u8 *p,u32 n,u32 type,AFHolidayOwner *out) {
    if(!packet(p,n) || !out)return -1;
    for(u32 i=0;i<44;i++) {
        const u8 *r=p+48+49*12+i*4;
        if(r[0]==type) {
            if(r[1]>AF_HE_DEDICATED || r[2]>31 || r[3])return -1;
            *out=(AFHolidayOwner){type,r[1],r[2]};return 1;
        }
    }
    return 0;
}
static int status(const AFHolidayDay *d,u32 n,u32 type,u32 mask) {
    if(!d || n>AF_HE_CAPACITY)return 0;
    for(u32 i=0;i<n;i++)if(d[i].type==type)return (d[i].status&mask)!=0;
    return 0;
}
u32 af_holiday_event_current(const u8 *p,u32 n,const AFHolidayDay *d,u32 count) {
    if(!packet(p,n))return 255;
    for(u32 i=0;i<28;i++)if(i!=22 && status(d,count,p[16+i],AF_HE_RUN))return i;
    if(status(d,count,p[16+22],AF_HE_RUN))return 22;
    if(status(d,count,4,AF_HE_RUN))return 101;
    if(status(d,count,5,AF_HE_RUN))return 102;
    return status(d,count,35,AF_HE_RUN)?103:255;
}
u32 af_holiday_event_field(const AFHolidayDay *d,u32 n) {
    static const u8 types[]={15,12,14};
    for(u32 i=0;i<3;i++)if(status(d,n,types[i],AF_HE_RUN))return i;
    return 3;
}
int af_holiday_event_cleanup(const u8 *p,u32 n,const AFHolidayDay *d,u32 count) {
    u32 event=af_holiday_event_current(p,n,d,count);
    if(event==0)return -2;
    if(event==8 || event==20) {
        static const u8 types[]={12,15,14};
        for(u32 i=0;i<3;i++)if(status(d,count,types[i],AF_HE_SHOW))return types[i];
        return -1;
    }
    if(event<28)return p[16+event];
    if(event==101 || event==102)return event-97;
    return -1;
}
static int valid(const AFHolidayDay *d,const AFHolidayOwner *o,const AFHolidayOwnerOps *ops) {
    return d && o && ops && d->type==o->type && o->kind<=AF_HE_DEDICATED &&
        ops->dispatch && ops->keep && ops->set_keep && ops->place && ops->show &&
        ops->cull && ops->wandering_place;
}
static int call(AFHolidayDay *d,const AFHolidayOwner *o,const AFHolidayOwnerOps *ops,u32 phase) {
    if(!(o->callbacks&(1u<<phase)))return phase==AF_HE_ENTER?2:1;
    void *ctx=ops->context;
    if(o->kind==AF_HE_DEDICATED)return ops->dispatch(ctx,o->type,phase);
    if(o->kind==AF_HE_NONE)return 0;
    if(phase==AF_HE_START) {
        int kept=ops->keep(ctx,o->type);
        if(!kept)ops->set_keep(ctx,o->type,1);
        int placed=ops->place(ctx,o->type,o->kind,0x51,o->kind==AF_HE_WANDER?1:2);
        if(placed<0)d->status|=AF_HE_ERROR;
        if(o->kind==AF_HE_WANDER)ops->wandering_place(ctx,placed>0);
        return kept?2:1;
    }
    if(phase==AF_HE_END) {
        int kept=ops->keep(ctx,o->type);
        if(kept)ops->set_keep(ctx,o->type,0);
        if(o->kind==AF_HE_WANDER)ops->wandering_place(ctx,0);
        return kept?1:2;
    }
    if(phase==AF_HE_ENTER)return ops->show(ctx,o->type,0x51);
    if(phase==AF_HE_LEAVE)return ops->cull(ctx,o->type);
    return 0;
}
int af_holiday_event_clock(AFHolidayDay *d,const AFHolidayOwner *o,const AFHolidayOwnerOps *ops) {
    if(!valid(d,o,ops))return -1;
    if((d->status&AF_HE_ACTIVE) && !(d->status&AF_HE_RUN)) {
        if(!call(d,o,ops,AF_HE_START))return 0;
        if(!(d->status&AF_HE_ERROR))d->status|=AF_HE_RUN;
    } else if(!(d->status&AF_HE_ACTIVE) && (d->status&AF_HE_RUN)) {
        if(!call(d,o,ops,AF_HE_END))return 0;
        d->status&=~AF_HE_RUN;
    }
    return 1;
}
int af_holiday_event_wade(AFHolidayDay *d,const AFHolidayOwner *o,const AFHolidayOwnerOps *ops,
        int skip,int player_wading,int fading) {
    if(!valid(d,o,ops))return -1;
    if(skip)return 0;
    if(!(d->status&AF_HE_ACTIVE) || (d->status&AF_HE_STOP)) {
        if(d->status&AF_HE_SHOW) {
            if(!call(d,o,ops,AF_HE_LEAVE))return 0;
            d->status&=~(AF_HE_SHOW|AF_HE_STOP);
            if(o->callbacks&(1u<<AF_HE_BEHIND))call(d,o,ops,AF_HE_BEHIND);
        }
    } else {
        if(!player_wading && !fading)return 0;
        if(!(d->status&AF_HE_SHOW)) {
            int result=call(d,o,ops,AF_HE_ENTER);
            if(!result)return 0;
            if(result==1 && !(d->status&AF_HE_ERROR))d->status|=AF_HE_SHOW;
        }
    }
    return 1;
}
