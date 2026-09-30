/* Complete source hide placement, relocation retries, and ordinary arrival.
 * Seeds use source identities; event areas and spawning use additive identities. */
#include "holiday_hiding.h"
static int equal(AFHolidayBlock a,AFHolidayBlock b) {return a.x==b.x && a.z==b.z;}
static int block_valid(const AFHolidayField *f,AFHolidayBlock b) {
    return b.x>=0 && b.x<f->maximum.x && b.z>=0 && b.z<f->maximum.z;
}
static int place_valid(const AFHolidayField *f,const AFHolidayPlace *p) {
    return block_valid(f,p->block) && p->unit.x>=0 && p->unit.x<16 && p->unit.z>=0 && p->unit.z<16;
}
static int valid(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,unsigned int id) {
    if(!f || !h || type>=128 || id>=256 || f->maximum.x<3 || f->maximum.x>32 ||
       f->maximum.z<4 || f->maximum.z>32 || f->exclusions>5 || f->month<1 || f->month>12 ||
       f->day<1 || f->day>31 || f->hour>=24 || f->second>=60)return 0;
    const AFHolidayPlacementOps *o=&h->placement;
    return o->outdoors && o->busy && o->other && o->unit && o->get && o->reserve &&
        o->forward && o->flatten && o->spawn && o->error && h->foreground && h->collision &&
        h->hard_allowed && h->ball && h->marine && h->occupied && h->free;
}
/* The native field has four physical landmarks and no island dock. The fixed
 * fallback excludes pool/station/shrine, but deliberately permits home. */
static int available(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        AFHolidayBlock b,int fixed) {
    const AFHolidayPlacementOps *o=&h->placement;
    if(!block_valid(f,b) || o->busy(o->context,b.x,b.z))return 0;
    for(unsigned int i=0;i<f->exclusions;i++)
        if(!(fixed && i==3) && equal(b,f->excluded[i]))return 0;
    if(o->other(o->context,type,b))return 0;
    AFHolidayBlock ball;
    return !h->ball(o->context,&ball) || !equal(b,ball);
}
static int fixed(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        AFHolidayPlace *p,AFHolidayBlock b) {
    AFHolidayBlock u;
    if(!available(f,h,type,b,1) || !af_holiday_hide_unit(&u.x,&u.z,b.x,b.z,2,h))return 0;
    p->block=b;p->unit=u;return 1;
}
int af_holiday_hide_search(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        AFHolidayPlace *p,int seed) {
    if(!p || !valid(f,h,type,0))return 0;
    int width=f->maximum.x-2,area=width*(f->maximum.z-3);
    for(int cur=area;cur>0;--cur) {
        unsigned int raw=f->month*f->day+f->second+(f->hour+(unsigned int)cur)*7u-(unsigned int)seed;
        if(raw&0x80000000u)raw=0u-raw;
        int n=(int)(raw%(unsigned int)area);
        AFHolidayBlock b={2+n/width,1+n%width},u;
        if(available(f,h,type,b,0) && af_holiday_hide_unit(&u.x,&u.z,b.x,b.z,2,h)) {
            p->block=b;p->unit=u;return cur;
        }
    }
    return 0;
}
static int search_all(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        AFHolidayPlace *p,int seed) {
    if(af_holiday_hide_search(f,h,type,p,seed) || fixed(f,h,type,p,(AFHolidayBlock){2,3}))return 1;
    AFHolidayBlock b;
    return h->marine(h->placement.context,&b) && fixed(f,h,type,p,b);
}
int af_holiday_hide_make(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        unsigned int name,unsigned int id,int seed,AFHolidayPlace **out) {
    if(!out)return -1;
    *out=0;
    if(!valid(f,h,type,id) || name>65535 || seed<0 || seed>0x20000)return -1;
    const AFHolidayPlacementOps *o=&h->placement;
    if(!o->outdoors(o->context))return 0;
    AFHolidayPlace *p=o->get(o->context,type,id);
    if(!p) {
        AFHolidayPlace candidate={{0,0},{0,0},(unsigned short)name,1};
        if(!search_all(f,h,type,&candidate,seed) || !(p=o->reserve(o->context,type,id))) {
            o->error(o->context,type);return -1;
        }
        *p=candidate;
    }
    if(!place_valid(f,p) || p->name!=name) {o->error(o->context,type);return -1;}
    *out=p;return 1;
}
int af_holiday_hide_walk(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        unsigned int source_name,unsigned int id,int seed,AFHolidayPlace **out) {
    if(!out)return -1;
    *out=0;
    if(!valid(f,h,type,id) || source_name>65535)return -1;
    const AFHolidayPlacementOps *o=&h->placement;
    if(!o->outdoors(o->context))return 0;
    AFHolidayPlace *p=o->get(o->context,type,id);
    if(!p)return 0;
    if(!place_valid(f,p)) {o->error(o->context,type);return -1;}
    AFHolidayPlace candidate=*p;
    /* Source first prefers another acre, then another unit, then any valid
     * cover. Copy only after success; a failed relocation retains the record. */
    for(int i=3;i>0;--i) {
        int next_seed=(int)((unsigned int)i+(unsigned int)seed+source_name+id);
        if(!search_all(f,h,type,&candidate,next_seed)) {
            o->error(o->context,type);return -1;
        }
        if(!equal(candidate.block,p->block) || (i<3 && (!equal(candidate.unit,p->unit) || i<2)))break;
    }
    *p=candidate;*out=p;return 1;
}
int af_holiday_hide_show(const AFHolidayField *f,const AFHolidayHiding *h,unsigned int type,
        unsigned int id,int seed,AFHolidayBlock *forward) {
    if(!forward || !valid(f,h,type,id))return 0;
    const AFHolidayPlacementOps *o=&h->placement;
    if(!o->outdoors(o->context))return 2;
    AFHolidayPlace *p=o->get(o->context,type,id);
    if(!p)return 2;
    if(!place_valid(f,p)) {o->error(o->context,type);return 0;}
    if(equal(f->next,p->block) || !o->forward(o->context,&forward->x,&forward->z) ||
       !equal(*forward,p->block))return 2;
    if(h->occupied(o->context,p)) {
        AFHolidayPlace candidate=*p;
        if(!o->unit(o->context,&candidate.unit.x,&candidate.unit.z,p->block.x,p->block.z) &&
           !h->free(o->context,type,&candidate,seed)) {o->error(o->context,type);return 0;}
        /* Correct the donor's discarded-search-result bug. */
        if(!place_valid(f,&candidate)) {o->error(o->context,type);return 0;}
        *p=candidate;
        /* A changed-acre fallback is for the next wade, not a remote spawn. */
        if(!equal(*forward,p->block))return 2;
    }
    o->flatten(o->context,p);
    return o->spawn(o->context,p)?1:0;
}
