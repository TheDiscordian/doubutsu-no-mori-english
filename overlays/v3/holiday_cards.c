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
    for(unsigned int i=0;i<16;i++)if(data[i]!=header[i])return 0;
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
