#include "holiday_cards.h"
#ifdef AF_V3_PAPER_PACKS
#include "carried_paper.h"
#endif
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
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
static int good_field_valid(const AFRewardGoodField *s) {
    const u8 *t=s->rtc;unsigned year=(unsigned)t[6]*256+t[7],any=0;
    for(unsigned i=0;i<8;i++)any|=t[i];
    return !any?!s->days:year>=2000 && year<=2099 && t[5]>=1 && t[5]<=12 &&
        t[3]>=1 && t[3]<=af_diary_days(year,t[5]) && t[2]<24 && t[1]<60 && t[0]<60 &&
        t[4]<7 && s->days<=15;
}
#endif
int af_holiday_cards_valid(const u8 *data) {
    static const u8 header[16]={'A','F','H','C',1,4,8,0,0,0,0,0,0,0,0,0};
    if(!data)return 0;
    if(data[4]!=1 && data[4]!=2
#ifdef AF_V3_CARRIED_PROFILE
        && data[4]!=3
#ifdef AF_V3_CARRIED_QUEST
        && data[4]!=4
#ifdef AF_V3_PAPER_PACKS
        && data[4]!=5
#ifdef AF_V3_CARRIED_NPC
        && data[4]!=6
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        && data[4]!=7
#endif
#endif
#endif
#endif
#endif
        )return 0;
    if(data[7] & ~(data[4]>=2?3u:0u))return 0;
    for(unsigned int i=0;i<16;i++) {
        if(i==4 || i==7)continue;
#ifdef AF_V3_CARRIED_PROFILE
        if(data[4]>=3 && i>=8 && i<=12)continue;
#ifdef AF_V3_CARRIED_QUEST
        if(data[4]>=4 && (i==13 || i==14))continue;
#ifdef AF_V3_PAPER_PACKS
        if(data[4]>=5 && i==15)continue;
#endif
#endif
#endif
        if(data[i]!=header[i])return 0;
    }
#ifdef AF_V3_CARRIED_PROFILE
    if(data[4]>=3) {
        if(data[8]>127 || ((data[8]>>2)&3)!=data[7])return 0;
        for(unsigned int i=9;i<13;i++)if(data[i] & ~(data[8]&1u))return 0;
#ifdef AF_V3_CARRIED_QUEST
        if(data[4]>=4 && (data[13] || data[14]) &&
           (!(data[8]&64) || !data[14] || data[14]>af_diary_days(2000,data[13])))return 0;
#ifdef AF_V3_PAPER_PACKS
        if(data[4]==5 && data[15]>1)return 0;
#ifdef AF_V3_CARRIED_NPC
        if(data[4]>=6 && (data[15]>3 || ((data[15]&2) && !(data[8]&64))))return 0;
#endif
#endif
#endif
    }
#endif
    for(unsigned int i=0;i<4;i++) {
        const u8 *p=data+16+i*8;AFHolidayCard c=decode(p);
        if(!valid(&c))return 0;
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        if(data[4]==7) {
            unsigned year=p[5]&127u,giver=(unsigned)p[6]*256+p[7];
            if(year>100 || (i>=2 && (p[5]&128u)) ||
               (giver && (!year || giver>>12!=14 || giver==0xEFFF)))return 0;
        } else
#endif
        if(p[5] || p[6] || p[7])return 0;
    }
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    if(data[4]==7) {
        AFRewardGoodField s;
        for(unsigned i=0;i<8;i++)s.rtc[i]=data[48+i];
        s.days=(unsigned)data[56]<<24|(unsigned)data[57]<<16|(unsigned)data[58]<<8|data[59];
        if(!good_field_valid(&s) || data[60] || data[61] || data[62] || data[63])return 0;
    }
#endif
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
    p[3]=c.last_date.day;p[4]=c.days;
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    if(data[4]!=7)
#endif
    p[5]=p[6]=p[7]=0;
    return 1;
}
int af_holiday_cards_clear(u8 *data,unsigned int slot) {
    const AFHolidayCard empty={{0,0,0},0};
    if(!af_holiday_cards_set(data,slot,&empty))return 0;
#ifdef AF_V3_CARRIED_PROFILE
    if(data[4]>=3)data[9+slot]=0;
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    if(data[4]==7) {
        u8 *p=data+16+slot*8;
        p[5]&=128u;p[6]=p[7]=0;
    }
#endif
#endif
    return 1;
}
int af_holiday_cards_profile(const u8 *data,unsigned int enabled) {
    return enabled<=3 && af_holiday_cards_valid(data) && !(data[7]&~enabled);
}
int af_holiday_cards_bind(u8 *data,unsigned int enabled) {
    if(!af_holiday_cards_profile(data,enabled))return 0;
#ifdef AF_V3_CARRIED_PROFILE
    if(data[4]>=3)return data[7]==enabled;
#endif
    data[4]=2;data[7]=(u8)enabled;return 1;
}
#ifdef AF_V3_CARRIED_PROFILE
unsigned int af_carried_save_enabled(void) {
#ifdef __mips__
    const volatile unsigned int *h=(const volatile unsigned int *)0x80773800u;
#else
    extern unsigned int af_test_carried_profile[8];
    const unsigned int *h=af_test_carried_profile;
#endif
    if(h[0]!=0x41464350u || h[1]!=1 || h[2]!=26 || h[3]!=32 ||
       h[4]>127 || h[5]>127 || (h[5]&~h[4]) || h[6] || h[7] ||
       ((h[5]>>2)&3)!=af_holiday_cards_enabled())return ~0u;
    return h[5];
}
int af_carried_save_profile(const u8 *data,unsigned int events,unsigned int enabled) {
    if(enabled>127 || ((enabled>>2)&3)!=events || !af_holiday_cards_profile(data,events))return 0;
#ifdef AF_V3_PAPER_PACKS
    unsigned mode=*(const volatile AFCarryWord *)&af_carried_paper_mode;
    if(mode>1 || (data[4]>=5 && (data[15]&1) && !mode))return 0;
#endif
    return data[4]<3 || !(data[8]&~enabled);
}
int af_carried_save_bind(u8 *data,unsigned int events,unsigned int enabled) {
    if(!af_carried_save_profile(data,events,enabled))return 0;
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    if(data[4]<7)for(unsigned i=AF_HC_LEGACY_BYTES;i<AF_HC_BYTES;i++)data[i]=0;
#endif
#ifdef AF_V3_PAPER_PACKS
    data[15]=(u8)((data[15]&2u)|*(const volatile AFCarryWord *)&af_carried_paper_mode);
#endif
    data[4]=AF_HC_CARRIED_WIRE;data[7]=(u8)events;data[8]=(u8)enabled;return 1;
}
int af_carried_paper_collect(u8 *data,unsigned int slot,unsigned int mark) {
    if(slot>=4 || mark>1 || !af_holiday_cards_valid(data) || data[4]<3 || !(data[8]&1))return -1;
    if(mark)data[9+slot]=1;
    return data[9+slot];
}
#ifdef AF_V3_CARRIED_QUEST
int af_carried_quest_day(const u8 *data) {
    if(!af_holiday_cards_valid(data) || data[4]<4 || !(data[8]&64))return -1;
    return (unsigned int)data[13]*256u+data[14];
}
int af_carried_quest_set_day(u8 *data,unsigned int day) {
    if(af_carried_quest_day(data)<0 || day>65535 ||
       (day && (!(day&255) || (day&255)>af_diary_days(2000,day>>8))))return 0;
    data[13]=day>>8;data[14]=day;return 1;
}
#ifdef AF_V3_CARRIED_NPC
int af_carried_quest_weeds(const u8 *data) {
    if(!af_holiday_cards_valid(data) || data[4]<6 || !(data[8]&64))return -1;
    return (data[15]>>1)&1;
}
int af_carried_quest_set_weeds(u8 *data,unsigned int pending) {
    if(pending>1 || af_carried_quest_weeds(data)<0)return 0;
    data[15]=(u8)((data[15]&1u)|(pending<<1));return 1;
}
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
int af_reward_first_present(const u8 *data,unsigned int mask) {
    if(mask>3 || !af_holiday_cards_valid(data) || data[4]!=7)return -1;
    unsigned flags=(data[21]>>7)|((unsigned)(data[29]>>7)<<1);
    return flags&mask;
}
int af_reward_mark_first_present(u8 *data,unsigned int mask) {
    if(af_reward_first_present(data,mask)<0)return 0;
    if(mask&1)data[21]|=128u;
    if(mask&2)data[29]|=128u;
    return 1;
}
int af_reward_birthday_get(const u8 *data,unsigned int slot,AFRewardBirthday *out) {
    if(slot>=4 || !out || !af_holiday_cards_valid(data) || data[4]!=7)return 0;
    const u8 *p=data+16+slot*8;
    out->giver=(unsigned)p[6]*256+p[7];
    out->year=(p[5]&127u)?1999u+(p[5]&127u):0;
    return 1;
}
int af_reward_birthday_set(u8 *data,unsigned int slot,const AFRewardBirthday *gift) {
    if(!gift || slot>=4 || !af_holiday_cards_valid(data) || data[4]!=7 ||
       (gift->year && (gift->year<2000 || gift->year>2099)) ||
       (gift->giver && (!gift->year || gift->giver>>12!=14 || gift->giver==0xEFFF)))return 0;
    u8 *p=data+16+slot*8;
    p[5]=(u8)((p[5]&128u)|(gift->year?gift->year-1999u:0));
    p[6]=gift->giver>>8;p[7]=gift->giver;
    return 1;
}
int af_reward_good_field_get(const u8 *data,AFRewardGoodField *out) {
    if(!out || !af_holiday_cards_valid(data) || data[4]!=7)return 0;
    for(unsigned i=0;i<8;i++)out->rtc[i]=data[48+i];
    out->days=(unsigned)data[56]<<24|(unsigned)data[57]<<16|(unsigned)data[58]<<8|data[59];
    return 1;
}
int af_reward_good_field_set(u8 *data,const AFRewardGoodField *value) {
    if(!value || !good_field_valid(value) || !af_holiday_cards_valid(data) || data[4]!=7)return 0;
    AFRewardGoodField s=*value;
    for(unsigned i=0;i<8;i++)data[48+i]=s.rtc[i];
    data[56]=s.days>>24;data[57]=s.days>>16;data[58]=s.days>>8;data[59]=s.days;
    return 1;
}
#endif
#endif
#endif
#endif
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
