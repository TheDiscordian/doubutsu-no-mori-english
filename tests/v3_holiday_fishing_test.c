#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/holiday_fishing.h"
typedef struct {float value;unsigned int calls;} Device;
static float random_value(void *opaque) {Device *d=opaque;++d->calls;return d->value;}
static int player(void *opaque,const AFHFPerson *pid) {
    (void)opaque;return pid->land_id==8 && pid->player_id<4?(int)pid->player_id:-1;
}
static int event_npc(void *opaque,unsigned short *npc) {(void)opaque;*npc=0xD001;return 1;}
static void npc_name(void *opaque,unsigned char *out,unsigned short npc) {
    (void)opaque;assert(npc==0xD001);memcpy(out,"Robin   ",8);
}
static void random_name(void *opaque,unsigned char *out) {(void)opaque;memcpy(out,"Maple   ",8);}
static AFHFPerson identity(unsigned int n) {
    AFHFPerson p;memcpy(p.player_name,"Player  ",8);memcpy(p.land_name,"Town    ",8);
    p.player_id=n;p.land_id=8;return p;
}
static void clock_set(AFHolidayFish *f,unsigned int year,unsigned int month,unsigned int day,unsigned int hour) {
    AFHFTime t={0,0,hour,day,af_diary_weekday((AFDiaryDate){year,month,day}),month,year};
    assert(af_holiday_fish_clock(f,&t));
}
static void init(AFHolidayFish *f,Device *d,unsigned int mode) {
    assert(af_holiday_fish_reset(f,mode));
    f->services=(AFHFServices){random_value,player,event_npc,npc_name,random_name};f->opaque=d;
    clock_set(f,2026,6,7,12);
}
int main(void) {
    Device d={0.5f,0};AFHolidayFish f,other,before;AFHFPerson p=identity(0);
    init(&f,&d,AF_HF_CM);
    assert(af_holiday_fish_size(&f,0)==25);
    assert(af_holiday_fish_size(&f,1)==40);
    assert(af_holiday_fish_size(&f,2)==55);
    assert(af_holiday_fish_units(&f,AF_HF_INCHES));
    assert(af_holiday_fish_size(&f,0)==9);
    assert(af_holiday_fish_size(&f,1)==15);
    assert(af_holiday_fish_size(&f,2)==21);
    for(unsigned int hour=0;hour<24;hour++) {
        int size=af_holiday_fish_npc_size(&f,hour);assert(size>=3 && size<=27);
    }
    /* Every slot, all four owners, duplicate-date replacement, and recycling. */
    for(unsigned int i=0;i<5;i++) {
        clock_set(&f,2026,6,7+i,12);p=identity(i&3);
        assert(af_holiday_fish_set(&f,&p,20+i));
    }
    for(unsigned int i=0;i<5;i++)assert(f.fishRecord[i].size==20+(int)i);
    p=identity(3);assert(af_holiday_fish_set(&f,&p,26));assert(f.fishRecord[4].size==26);
    clock_set(&f,2026,6,12,12);assert(af_holiday_fish_set(&f,&p,27));
    assert(f.fishRecord[0].time.day==12 && f.fishRecord[0].size==27);
    before=f;assert(!af_holiday_fish_units(&f,AF_HF_CM));assert(!memcmp(&f,&before,sizeof(f)));
    unsigned char bytes[AF_HF_BYTES],copy[AF_HF_BYTES];
    memset(bytes,0xCC,sizeof(bytes));assert(!af_holiday_fish_store(&f,bytes,sizeof(bytes)-1));
    for(unsigned int i=0;i<sizeof(bytes);i++)assert(bytes[i]==0xCC);
    assert(af_holiday_fish_store(&f,bytes,sizeof(bytes)));
    assert(!memcmp(bytes,"AFHF\1\1\5\40",8));
    init(&other,&d,AF_HF_INCHES);
    assert(af_holiday_fish_load(&other,bytes,sizeof(bytes),AF_HF_INCHES));
    assert(!memcmp(f.fishRecord,other.fishRecord,sizeof(f.fishRecord)));
    assert(af_holiday_fish_store(&other,copy,sizeof(copy)));assert(!memcmp(copy,bytes,sizeof(copy)));
    before=other;assert(!af_holiday_fish_load(&other,bytes,sizeof(bytes),AF_HF_CM));
    assert(!memcmp(&other,&before,sizeof(other)));
    memcpy(copy,bytes,sizeof(copy));copy[16+25]=13;
    assert(!af_holiday_fish_load(&other,copy,sizeof(copy),AF_HF_INCHES));
    assert(!memcmp(&other,&before,sizeof(other)));
    /* Source time travel drops future records; invalid callbacks don't commit. */
    clock_set(&f,2026,6,6,12);p=identity(0);assert(af_holiday_fish_set(&f,&p,27));
    for(unsigned int i=1;i<5;i++)assert(!f.fishRecord[i].size);
    before=f;d.value=2.0f;AFHFPerson winner;unsigned int size;
    assert(!af_holiday_fish_holder(&f,&winner,&size,(AFDiaryDate){2026,6,6}));
    assert(!memcmp(&f,&before,sizeof(f)));d.value=0.0f;
    clock_set(&f,2026,6,7,12);int mask=af_holiday_fish_finalize(&f);assert(mask>0);
    unsigned int slot=0;while(!(mask&(1u<<slot)))++slot;
    AFHFRecord sent=f.fishRecord[slot];before=f;
    sent.size--;assert(!af_holiday_fish_acknowledge(&f,slot,&sent));assert(!memcmp(&f,&before,sizeof(f)));
    sent=f.fishRecord[slot];assert(af_holiday_fish_acknowledge(&f,slot,&sent));
    assert(!f.fishRecord[slot].size);assert(af_holiday_fish_units(&f,AF_HF_CM));
    /* Native 16-byte IDs expand explicitly; long donor names never truncate. */
    unsigned char native[16]={'A','l','e','x',32,32,'T','o','w','n',32,32,0,3,0,8},native_copy[16];
    af_holiday_fish_native_person(&p,native);assert(p.player_id==3 && p.land_id==8);
    assert(af_holiday_fish_native_export(native_copy,&p));assert(!memcmp(native,native_copy,16));
    p.player_name[7]='s';memset(native_copy,0xA5,16);
    assert(!af_holiday_fish_native_export(native_copy,&p));for(unsigned int i=0;i<16;i++)assert(native_copy[i]==0xA5);
    AFDiaryDate dates[5];clock_set(&f,2026,12,1,12);assert(af_holiday_fish_dates(&f,dates));
    for(unsigned int i=0;i<5;i++) {
        assert(dates[i].year==2026 && dates[i].month==11 && dates[i].day==1+7*i);
    }
    assert(af_hf_time_compare(&f.time.rtc_time,&f.time.rtc_time)==1);
    puts("Fishing records: five-slot lifecycle, both units, owner identity, serialization, clock changes, and delivery acknowledgement pass");
    return 0;
}
