/* Complete shared event-layout and reserved-acre readers. */
#include "holiday_reserved.h"
typedef unsigned int u32;
typedef unsigned char u8;
static u32 half(const u8 *p) {return (u32)p[0]*256+p[1];}
static u32 word(const u8 *p) {return half(p)*65536u+half(p+2);}
int af_holiday_map_get(const u8 *p,u32 bytes,u32 donor,u32 variant,u32 index,AFHolidayMap *out) {
    if(!p || !out || bytes<16 || word(p)!=0x4146484Du || half(p+4)!=1 ||
       half(p+6)!=17 || word(p+8)!=20 || word(p+12)!=bytes || bytes<356)return -1;
    const u8 *found=0;
    for(u32 i=0;i<17;i++) {
        const u8 *r=p+16+i*20;
        if(half(r)==donor) {if(found)return -1;found=r;}
        u32 count=r[5],variants=r[4],offset=word(r+16),kind=word(r+12);
        if(!variants) {for(u32 j=2;j<20;j++)if(r[j])return -1;continue;}
        if(r[2] || variants>7 || !count || count>16 || r[3]>count || half(r+6)>>count ||
           half(r+10) || (kind!=0 && kind!=4 && kind!=32768) ||
           (kind!=32768 && variants!=1) || offset<356 || offset>bytes ||
           variants*count*4>bytes-offset)return -1;
    }
    if(!found || !found[4])return 0;
    /* Shrine/single layouts ignore the live pool shape. Pool layouts do not
     * clamp a wrong shape to another acre's arrangement. */
    if(word(found+12)!=32768)variant=0;
    if(variant>=found[4] || index>=found[5])return -1;
    const u8 *a=p+word(found+16)+(variant*found[5]+index)*4;
    if(a[2]>=16 || a[3]>=16)return -1;
    *out=(AFHolidayMap){donor,found[2],found[3],found[4],found[5],half(found+6),half(found+8),
        word(found+12),half(a),a[2],a[3]};return 1;
}
AFHolidayPlace *af_holiday_reserved_make(const u8 *p,u32 bytes,const AFHolidayReservedOps *ops,
    u32 donor,u32 native,u32 variant,u32 index,u32 id,int foreground) {
    if(!ops || !ops->outdoors || !ops->landmark || !ops->resolve || !ops->get ||
       !ops->reserve || !ops->error || (foreground && !ops->set_foreground) ||
       native>=128 || id>255 || (foreground!=0 && foreground!=1))return 0;
    void *c=ops->context;
    if(!ops->outdoors(c))return 0;
    AFHolidayPlace *stored=ops->get(c,native,id);
    if(!stored) {
        AFHolidayMap row;AFHolidayPlace place={0};
        if(af_holiday_map_get(p,bytes,donor,variant,index,&row)!=1 ||
           !ops->landmark(c,row.kind,&place.block)) {ops->error(c,native);return 0;}
        u32 name=ops->resolve(c,row.source_name);
        if(!name || name>65535) {ops->error(c,native);return 0;}
        place.unit=(AFHolidayBlock){(int)row.z,(int)row.x};place.name=name;place.flags=foreground?0:1;
        stored=ops->reserve(c,native,id);
        if(!stored) {ops->error(c,native);return 0;}
        *stored=place;
    }
    if(foreground && !ops->set_foreground(c,stored)) {ops->error(c,native);return 0;}
    return stored;
}
