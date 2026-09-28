/* Shared GAFE01 selected/free-acre placement and checkfgcol appearance. */
#include "holiday_placement.h"
_Static_assert(sizeof(AFHolidayPlace)==20,"Native placement size");
int af_holiday_placement_field(const void *manager,const unsigned char rtc[8],AFHolidayField *f) {
    if(!manager || !rtc || !f)return 0;
    const int *words=manager;
    f->maximum=(AFHolidayBlock){words[0x1E8/4],words[0x1EC/4]};
    f->next=(AFHolidayBlock){words[0x20C/4],words[0x210/4]};
    /* 214/218 is the pool (kind 8000), not the shrine (kind 4). */
    f->shrine=(AFHolidayBlock){words[0x22C/4],words[0x230/4]};
    f->exclusions=4;
    for(unsigned int i=0;i<4;i++)f->excluded[i]=(AFHolidayBlock){words[0x214/4+i*3],words[0x218/4+i*3]};
    f->month=rtc[5];f->day=rtc[3];f->hour=rtc[2];f->second=rtc[0];return 1;
}
static int equal(AFHolidayBlock a,AFHolidayBlock b) {return a.x==b.x && a.z==b.z;}
static int block_valid(const AFHolidayField *f,AFHolidayBlock b) {
    return b.x>=0 && b.x<f->maximum.x && b.z>=0 && b.z<f->maximum.z;
}
static int place_valid(const AFHolidayField *f,const AFHolidayPlace *p) {
    return block_valid(f,p->block) && p->unit.x>=0 && p->unit.x<16 && p->unit.z>=0 && p->unit.z<16;
}
static int valid(const AFHolidayField *f,const AFHolidayPlacementOps *o,unsigned int type,unsigned int id) {
    return f && o && type<128 && id<256 && f->maximum.x>=3 && f->maximum.x<=32 &&
        f->maximum.z>=4 && f->maximum.z<=32 && f->exclusions<=5 &&
        f->month>=1 && f->month<=12 && f->day>=1 && f->day<=31 && f->hour<24 && f->second<60 &&
        o->outdoors && o->busy && o->other && o->unit && o->height && o->get &&
        o->reserve && o->forward && o->flatten && o->spawn && o->error;
}
static int search(const AFHolidayField *f,const AFHolidayPlacementOps *o,unsigned int type,
        AFHolidayPlace *p,int wandering,int adjust,int seed) {
    int width=f->maximum.x-2,area=width*(f->maximum.z-3);
    for(int phase=3;phase>0;--phase)for(int cur=area;cur>0;--cur) {
        AFHolidayBlock b=p->block,u;
        if(wandering) {
            int n=(int)(f->month*f->day+f->second)+(f->hour+cur)*3+seed*9;
            if(n<0)n=-n;
            n%=area;b.x=1+n%width;b.z=2+n/width;
        }
        if(phase>=2 && o->busy(o->context,b.x,b.z))continue;
        int excluded=0;
        if(wandering)for(unsigned int i=0;i<f->exclusions;i++)if(equal(b,f->excluded[i]))excluded=1;
        if(excluded || (phase>=3 && o->other(o->context,type,b)))continue;
        if(!o->unit(o->context,&u.x,&u.z,b.x,b.z))continue;
        if(u.x<adjust || u.x>=16-adjust || u.z<adjust || u.z>=16-adjust)continue;
        p->block=b;p->unit=u;return 1;
    }
    return 0;
}
int af_holiday_placement_make(const AFHolidayField *f,const AFHolidayPlacementOps *o,
        unsigned int type,unsigned int name,unsigned int id,unsigned int kind,int seed,AFHolidayPlace **out) {
    if(!out || !valid(f,o,type,id) || name>65535 || seed<0 || seed>0x20000 ||
       (kind!=AF_HE_SHRINE && kind!=AF_HE_WANDER && kind!=AF_HE_HALLOWEEN))return -1;
    *out=0;
    if(!o->outdoors(o->context))return 0;
    AFHolidayPlace *place=o->get(o->context,type,id);
    if(!place) {
        AFHolidayPlace candidate={f->shrine,{0,0},name,1};
        if((kind!=AF_HE_WANDER && !block_valid(f,candidate.block)) ||
           !search(f,o,type,&candidate,kind==AF_HE_WANDER,kind==AF_HE_WANDER?1:2,seed)) {
            o->error(o->context,type);return -1;
        }
        place=o->reserve(o->context,type,id);
        if(!place) {o->error(o->context,type);return -1;}
        *place=candidate;
    }
    if(!place_valid(f,place) || place->name!=name) {o->error(o->context,type);return -1;}
    *out=place;return 1;
}
static int nearby(const AFHolidayPlacementOps *o,const AFHolidayPlace *p,AFHolidayBlock *out) {
    static const signed char x[9]={0,1,-1,0,1,-1,0,1,-1};
    static const signed char z[9]={0,0,0,1,1,1,-1,-1,-1};
    for(unsigned int i=0;i<9;i++) {
        int ux=p->unit.x+x[i],uz=p->unit.z+z[i];
        if(ux>=1 && ux<15 && uz>=1 && uz<15 &&
           o->height(o->context,p->block.x,p->block.z,ux,uz)) {
            out->x=ux;out->z=uz;return 1;
        }
    }
    return 0;
}
int af_holiday_placement_show(const AFHolidayField *f,const AFHolidayPlacementOps *o,
        unsigned int type,unsigned int id,AFHolidayBlock *forward) {
    if(!forward || !valid(f,o,type,id))return 0;
    if(!o->outdoors(o->context))return 2;
    AFHolidayPlace *p=o->get(o->context,type,id);
    if(!p)return 2;
    if(!place_valid(f,p)) {o->error(o->context,type);return 0;}
    if(equal(f->next,p->block) || !o->forward(o->context,&forward->x,&forward->z) ||
       !equal(*forward,p->block))return 2;
    AFHolidayBlock u=p->unit;
    if(!nearby(o,p,&u) && !o->unit(o->context,&u.x,&u.z,p->block.x,p->block.z))return 2;
    if(u.x<1 || u.x>=15 || u.z<1 || u.z>=15) {o->error(o->context,type);return 0;}
    p->unit=u;o->flatten(o->context,p);
    return o->spawn(o->context,p)?1:0;
}
