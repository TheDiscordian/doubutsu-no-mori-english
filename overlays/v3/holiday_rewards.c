/* Shared donor holiday selectors and no-loss handover, independent of actors. */
#include "holiday_rewards.h"
typedef af_holiday_u8 u8;
typedef af_holiday_u32 u32;
static u32 half(const u8 *p) { return (u32)p[0]*256u+p[1]; }

int af_v3_holiday_valid(const u8 *data,u32 bytes) {
    if (!data || bytes<16u || data[0]!='A' || data[1]!='F' || data[2]!='H' || data[3]!='G' ||
            half(data+4)!=1 || half(data+6)!=28 || half(data+8)>128 || !half(data+8) ||
            half(data+10)!=8 || half(data+12)!=2 || half(data+14) || bytes!=240u+half(data+8)*2u) return 0;
    u32 end=0;
    for (u32 i=0;i<28u;++i) {
        const u8 *r=data+16u+i*8u;u32 first=half(r),count=half(r+2),mode=r[4];
        if (first!=end || !count || count>16u || mode>2u || r[5] || half(r+6)>255u ||
                (mode==0 && count!=1) || (mode==2 && count!=2) || first+count>half(data+8)) return 0;
        end+=count;
    }
    if (end!=half(data+8)) return 0;
    for (u32 i=0;i<end;++i) if (!half(data+240u+i*2u)) return 0;
    return 1;
}

static int range(const u8 *data,u32 bytes,u32 event,u32 gender,u32 *first,u32 *count) {
    if (event>=28u || gender>1u || !af_v3_holiday_valid(data,bytes)) return 0;
    const u8 *r=data+16u+event*8u;
    *first=half(r);*count=half(r+2);
    if (r[4]==2) { *first+=gender;*count=1; }
    return 1;
}

int af_v3_holiday_count(const u8 *data,u32 bytes,u32 event,u32 gender,const struct AfHolidayOps *ops) {
    u32 first,count;int available=0;
    if (!ops || !ops->resolve || !range(data,bytes,event,gender,&first,&count)) return -1;
    for (u32 i=0;i<count;++i) {
        u32 item=ops->resolve(ops->context,half(data+240u+(first+i)*2u));
        if (item>65535u) return -1;
        available+=item!=0;
    }
    return available;
}

int af_v3_holiday_offer(const u8 *data,u32 bytes,u32 event,u32 gender,u32 roll,
        const struct AfHolidayOps *ops,struct AfHolidayOffer *out) {
    u32 first,count;
    if (!out || !ops || !ops->resolve || !ops->claimed ||
            !range(data,bytes,event,gender,&first,&count) || ops->claimed(ops->context,event)!=0) return 0;
    for (u32 i=0;i<count;++i) {
        u32 donor=half(data+240u+(first+i)*2u),item=ops->resolve(ops->context,donor);
        if (item>65535u) return 0;
        if (item && roll--==0) {
            out->event=event;out->variant=first+i;out->source_item=donor;out->item=item;out->gender=gender;
            return 1;
        }
    }
    return 0;
}

int af_v3_holiday_commit(const u8 *data,u32 bytes,const struct AfHolidayOps *ops,const struct AfHolidayOffer *offer) {
    u32 first,count;
    if (!offer || !ops || !ops->resolve || !ops->claimed || !ops->give || !ops->mark ||
            !range(data,bytes,offer->event,offer->gender,&first,&count) ||
            offer->variant<first || offer->variant-first>=count || !offer->item || offer->item>65535u ||
            half(data+240u+offer->variant*2u)!=offer->source_item ||
            ops->resolve(ops->context,offer->source_item)!=offer->item || ops->claimed(ops->context,offer->event)!=0) return 0;
    if (ops->give(ops->context,offer->item)!=1) return 0;
    ops->mark(ops->context,offer->event);
    return 1;
}
