#include "holiday_fishing.h"
typedef unsigned int u32;
_Static_assert(sizeof(AFHFPerson)==20,"Normalized fishing identity");
_Static_assert(sizeof(AFHFRecord)==32,"Complete donor fishing record");
static u32 word(const AFHFB *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static unsigned int half(const AFHFB *p) {return (unsigned int)p[0]*256+p[1];}
void af_hf_clear(void *p,unsigned int n,unsigned int v) {for(u32 i=0;i<n;i++)((AFHFB*)p)[i]=(AFHFB)v;}
void af_hf_copy(void *p,const void *q,unsigned int n) {for(u32 i=0;i<n;i++)((AFHFB*)p)[i]=((const AFHFB*)q)[i];}
#ifdef __mips__
/* GCC emits this freestanding helper for complete context/record assignments. */
void *memcpy(void *p,const void *q,__SIZE_TYPE__ n) {af_hf_copy(p,q,n);return p;}
#endif
static void put32(AFHFB *p,u32 n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
static void put16(AFHFB *p,u32 n) {p[0]=n>>8;p[1]=n;}
static int date_valid(AFDiaryDate d) {return d.year>=2000 && d.year<=2099 && d.day && d.day<=af_diary_days(d.year,d.month);}
static AFDiaryDate date(AFHFTime t) {return (AFDiaryDate){t.year,t.month,t.day};}
static int time_valid(AFHFTime t) {return date_valid(date(t)) && t.sec<60 && t.min<60 && t.hour<24 && t.weekday<7;}
static int record_valid(const AFHFRecord *r,unsigned int units) {
    if(!r->size) {
        const AFHFB *p=(const AFHFB*)r;for(u32 i=0;i<sizeof(*r);i++)if(p[i])return 0;
        return 1;
    }
    return r->size>0 && r->size<=(units==AF_HF_INCHES?27:70) && time_valid(r->time);
}
static int valid(const AFHolidayFish *f) {
    if(!f || f->units>AF_HF_INCHES)return 0;
    for(u32 i=0;i<5;i++)if(!record_valid(f->fishRecord+i,f->units))return 0;
    return 1;
}
static int ready(const AFHolidayFish *f) {
    return valid(f) && time_valid(f->time.rtc_time) && f->services.random &&
        f->services.player_index && f->services.event_npc && f->services.npc_name && f->services.random_name;
}
float af_hf_random(AFHolidayFish *f) {
    float n=f->services.random(f->opaque);
    if(!(n>=0.0f && n<1.0f)) {f->error=1;return 0.0f;}return n;
}
int af_holiday_fish_reset(AFHolidayFish *f,unsigned int units) {
    if(!f || units>AF_HF_INCHES)return 0;
    af_hf_clear(f,sizeof(*f),0);f->units=units;return 1;
}
int af_holiday_fish_clock(AFHolidayFish *f,const AFHFTime *t) {
    if(!f || !t || !time_valid(*t))return 0;
    f->time.rtc_time=*t;return 1;
}
int af_holiday_fish_units(AFHolidayFish *f,unsigned int units) {
    if(!valid(f) || units>AF_HF_INCHES)return 0;
    if(f->units==units)return 1;
    for(u32 i=0;i<5;i++)if(f->fishRecord[i].size)return 0;
    f->units=units;return 1;
}
int af_holiday_fish_store(const AFHolidayFish *f,AFHFB *out,unsigned int capacity) {
    if(!valid(f) || !out || capacity<AF_HF_BYTES)return 0;
    AFHFB data[AF_HF_BYTES];af_hf_clear(data,sizeof(data),0);
    put32(data,0x41464846);data[4]=1;data[5]=f->units;data[6]=5;data[7]=32;
    for(u32 i=0;i<5;i++) {
        const AFHFRecord *r=f->fishRecord+i;AFHFB *p=data+16+i*32;
        af_hf_copy(p,r->pid.player_name,8);af_hf_copy(p+8,r->pid.land_name,8);
        put16(p+16,r->pid.player_id);put16(p+18,r->pid.land_id);
        const AFHFTime *t=&r->time;p[20]=t->sec;p[21]=t->min;p[22]=t->hour;
        p[23]=t->day;p[24]=t->weekday;p[25]=t->month;put16(p+26,t->year);put32(p+28,r->size);
    }
    af_hf_copy(out,data,sizeof(data));return 1;
}
int af_holiday_fish_load(AFHolidayFish *f,const AFHFB *data,unsigned int size,unsigned int units) {
    if(!f || !data || size!=AF_HF_BYTES || units>1 || word(data)!=0x41464846 ||
       data[4]!=1 || data[5]!=units || data[6]!=5 || data[7]!=32)return 0;
    for(u32 i=8;i<16;i++)if(data[i])return 0;
    AFHolidayFish next=*f;next.units=units;next.error=0;
    for(u32 i=0;i<5;i++) {
        AFHFRecord *r=next.fishRecord+i;const AFHFB *p=data+16+i*32;
        af_hf_copy(r->pid.player_name,p,8);af_hf_copy(r->pid.land_name,p+8,8);
        r->pid.player_id=half(p+16);r->pid.land_id=half(p+18);
        r->time=(AFHFTime){p[20],p[21],p[22],p[23],p[24],p[25],half(p+26)};r->size=(int)word(p+28);
    }
    if(!valid(&next))return 0;
    *f=next;return 1;
}
int af_holiday_fish_wire_valid(const AFHFB *data) {
    AFHolidayFish f;
    af_holiday_fish_reset(&f,AF_HF_CM);
    return data && af_holiday_fish_load(&f,data,AF_HF_BYTES,data[5]);
}
void af_holiday_fish_wire_reset(AFHFB *data) {
    AFHolidayFish f;
    af_holiday_fish_reset(&f,AF_HF_CM);
    (void)af_holiday_fish_store(&f,data,AF_HF_BYTES);
}
int af_holiday_fish_wire_clear_person(AFHFB *data,const AFHFB native[16]) {
    AFHolidayFish f;AFHFPerson person;
    af_holiday_fish_reset(&f,AF_HF_CM);
    if(!data || !native || !af_holiday_fish_load(&f,data,AF_HF_BYTES,data[5]))return 0;
    af_holiday_fish_native_person(&person,native);
    for(u32 i=0;i<5;i++) {
        AFHFRecord *r=f.fishRecord+i;
        const AFHFB *a=(const AFHFB*)&r->pid,*b=(const AFHFB*)&person;
        u32 n=0;while(n<sizeof(person) && a[n]==b[n])n++;
        if(n==sizeof(person))af_hf_clear(r,sizeof(*r),0);
    }
    return af_holiday_fish_store(&f,data,AF_HF_BYTES);
}
void af_holiday_fish_native_person(AFHFPerson *p,const AFHFB native[16]) {
    if(!p || !native)return;
    af_hf_clear(p,sizeof(*p),32);af_hf_copy(p->player_name,native,6);af_hf_copy(p->land_name,native+6,6);
    p->player_id=half(native+12);p->land_id=half(native+14);
}
int af_holiday_fish_native_export(AFHFB native[16],const AFHFPerson *p) {
    if(!native || !p || p->player_name[6]!=32 || p->player_name[7]!=32 ||
       p->land_name[6]!=32 || p->land_name[7]!=32)return 0;
    af_hf_copy(native,p->player_name,6);af_hf_copy(native+6,p->land_name,6);
    put16(native+12,p->player_id);put16(native+14,p->land_id);return 1;
}
void af_hf_person_clear(AFHFPerson *p) {
    af_hf_clear(p,sizeof(*p),32);p->player_id=p->land_id=0xFFFF;
}
int af_hf_date_compare(unsigned int y,unsigned int m,unsigned int d,unsigned int yy,unsigned int mm,unsigned int dd) {
    u32 a=(y<<16)|(m<<8)|d,b=(yy<<16)|(mm<<8)|dd;return (a>b)-(a<b);
}
int af_hf_time_compare(const AFHFTime *a,const AFHFTime *b) {
    int n=af_hf_date_compare(b->year,b->month,b->day,a->year,a->month,a->day);
    if(n)return n;
    unsigned int x=b->hour*3600+b->min*60+b->sec,y=a->hour*3600+a->min*60+a->sec;
    return x>=y?1:-1; /* Donor comparison treats equal timestamps as OVER. */
}
void af_hf_add_minutes(AFHFTime *t,int minutes) {
    /* Source consumers add thirty minutes or six hours, never negative time. */
    unsigned int n=t->hour*60+t->min+(unsigned int)minutes;t->min=n%60;t->hour=(n/60)%24;
    for(n/=1440;n;n--) {
        if(++t->day>af_diary_days(t->year,t->month)) {
            t->day=1;if(++t->month>12) {t->month=1;++t->year;}
        }
        t->weekday=(t->weekday+1)%7;
    }
}
void af_hf_sub_year(AFHFTime *t,int years) {
    t->year-=years;unsigned int days=af_diary_days(t->year,t->month);
    if(t->day>days)t->day=days;
    t->weekday=(unsigned char)af_diary_weekday(date(*t));
}
int af_holiday_fish_set(AFHolidayFish *f,const AFHFPerson *pid,int size) {
    if(!ready(f) || !pid || size<=0 || size>(f->units==AF_HF_INCHES?27:70))return 0;
    AFHolidayFish next=*f;AFHFPerson copy=*pid;next.error=0;af_hf_source_set(&next,&copy,size);
    if(next.error || !valid(&next))return 0;
    *f=next;return 1;
}
int af_holiday_fish_size(AFHolidayFish *f,int rank) {
    if(!ready(f) || rank<0 || rank>2)return -1;
    f->error=0;int size=af_hf_source_size(f,rank);return f->error?-1:size;
}
int af_holiday_fish_npc_size(AFHolidayFish *f,unsigned int hour) {
    if(!ready(f) || hour>=24)return -1;
    f->error=0;
    int size=af_hf_source_npc_size(f,(unsigned char)hour);return f->error?-1:size;
}
int af_holiday_fish_holder(AFHolidayFish *f,AFHFPerson *pid,unsigned int *size,AFDiaryDate day) {
    if(!ready(f) || !pid || !size || !date_valid(day))return 0;
    AFHolidayFish next=*f;AFHFPerson result;unsigned int n;next.error=0;
    af_hf_source_holder(&next,&result,&n,&day);
    if(next.error || !valid(&next))return 0;
    *f=next;*pid=result;*size=n;return 1;
}
int af_holiday_fish_dates(AFHolidayFish *f,AFDiaryDate days[5]) {
    if(!ready(f) || !days)return 0;
    AFDiaryDate result[5];AFHFTime time=f->time.rtc_time;
    if(!af_hf_source_dates(f,result,&time))return 0;
    af_hf_copy(days,result,sizeof(result));return 1;
}
int af_holiday_fish_finalize(AFHolidayFish *f) {
    if(!ready(f))return -1;
    AFHolidayFish next=*f;next.error=0;AFDiaryDate day=date(next.time.rtc_time);
    af_hf_source_delete_after(&next,&day);af_hf_source_finalize(&next);
    af_hf_source_delete_npc(&next,&day);af_hf_source_sort(&next);
    if(next.error || !valid(&next))return -1;
    unsigned int mask=0;
    for(u32 i=0;i<5;i++) {
        AFHFRecord *r=next.fishRecord+i;
        if(r->size && next.services.player_index(next.opaque,&r->pid)>=0 &&
           af_hf_time_compare(&r->time,&next.time.rtc_time)>0)mask|=1u<<i;
    }
    *f=next;return (int)mask;
}
int af_holiday_fish_acknowledge(AFHolidayFish *f,unsigned int slot,const AFHFRecord *sent) {
    if(!ready(f) || !sent || slot>=5 || !sent->size)return 0;
    const AFHFB *a=(const AFHFB*)sent,*b=(const AFHFB*)(f->fishRecord+slot);
    for(u32 i=0;i<sizeof(*sent);i++)if(a[i]!=b[i])return 0;
    if(f->services.player_index(f->opaque,&sent->pid)<0 ||
       af_hf_time_compare(&sent->time,&f->time.rtc_time)<=0)return 0;
    af_hf_clear(f->fishRecord+slot,sizeof(*sent),0);return 1;
}
