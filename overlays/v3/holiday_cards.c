#include "holiday_cards.h"
typedef unsigned char u8;
static int valid(const AFHolidayCard *c) {
    AFDiaryDate d=c->last_date;
    if(!d.year && !d.month && !d.day)return !c->days;
    return d.year>=2000 && d.year<=2099 && d.day &&
        d.day<=af_diary_days(d.year,d.month) && c->days<=AF_HC_STAMPS;
}
static AFHolidayCard decode(const u8 *p) {
    return (AFHolidayCard){{(unsigned short)((unsigned int)p[0]*256+p[1]),p[2],p[3]},p[4]};
}
int af_holiday_cards_valid(const u8 *data) {
    static const u8 header[16]={'A','F','H','C',1,4,8,0,0,0,0,0,0,0,0,0};
    if(!data)return 0;
    if(data[4]!=1 && data[4]!=2)return 0;
    if(data[7] & ~(data[4]==2?3u:0u))return 0;
    for(unsigned int i=0;i<16;i++)if(i!=4 && i!=7 && data[i]!=header[i])return 0;
    for(unsigned int i=0;i<4;i++) {
        const u8 *p=data+16+i*8;AFHolidayCard c=decode(p);
        if(!valid(&c) || p[5] || p[6] || p[7])return 0;
    }
    return 1;
}
void af_holiday_cards_reset(u8 *data) {
    if(!data)return;
    for(unsigned int i=0;i<AF_HC_BYTES;i++)data[i]=0;
    data[0]='A';data[1]='F';data[2]='H';data[3]='C';data[4]=1;data[5]=4;data[6]=8;
}
int af_holiday_cards_get(const u8 *data,unsigned int slot,AFHolidayCard *out) {
    if(slot>=4 || !out || !af_holiday_cards_valid(data))return 0;
    *out=decode(data+16+slot*8);return 1;
}
int af_holiday_cards_set(u8 *data,unsigned int slot,const AFHolidayCard *card) {
    if(slot>=4 || !card || !valid(card) || !af_holiday_cards_valid(data))return 0;
    u8 *p=data+16+slot*8;AFHolidayCard c=*card;
    p[0]=c.last_date.year>>8;p[1]=c.last_date.year;p[2]=c.last_date.month;
    p[3]=c.last_date.day;p[4]=c.days;p[5]=p[6]=p[7]=0;return 1;
}
int af_holiday_cards_clear(u8 *data,unsigned int slot) {
    const AFHolidayCard empty={{0,0,0},0};return af_holiday_cards_set(data,slot,&empty);
}
int af_holiday_cards_profile(const u8 *data,unsigned int enabled) {
    return enabled<=3 && af_holiday_cards_valid(data) && !(data[7]&~enabled);
}
int af_holiday_cards_bind(u8 *data,unsigned int enabled) {
    if(!af_holiday_cards_profile(data,enabled))return 0;
    data[4]=2;data[7]=(u8)enabled;return 1;
}
#ifdef AF_V3_EVENT_ITEM_PROFILE
unsigned int af_holiday_cards_enabled(void) {
#ifdef __mips__
    const volatile unsigned int *h=(const volatile unsigned int *)0x80705E00u;
    return h[0]==0x41464849u && h[1]==2 && h[2]==14 && h[3]<=3?h[3]:~0u;
#else
    extern unsigned int af_test_event_item_profile;
    return af_test_event_item_profile;
#endif
}
#endif
