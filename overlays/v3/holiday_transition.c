/* Checked graph readers for all source event layouts. Search/fade algorithms
 * are compiled from the pinned donor source into ignored build output. */
#include "holiday_transition.h"
typedef unsigned int u32;
static u32 half(const unsigned char *p) {return (u32)p[0]*256+p[1];}
static int row(AFHolidayTransition *s,int donor,AFHolidayMap *m) {
    int result=af_holiday_map_get(s->maps,s->map_bytes,donor,s->pool_variant,0,m);
    if(result<0)s->failed=1;
    return result;
}
int af_holiday_transition_map(AFHolidayTransition *s) {
    AFHolidayMap m;
    /* This call validates the complete directory, including null records. */
    if(row(s,65535,&m)<0)return -1;
    int original=s->ops->original_rank?s->ops->original_rank(s->context):-1;
    if(original<-1 || original>=17 || (original>=0 && !s->ops->original_collision)) {
        s->failed=1;return -1;
    }
    for(u32 i=0;i<17;i++) {
        if(original==(int)i)return AF_HT_ORIGINAL_LAYOUT;
        u32 donor=half(s->maps+16+i*20);
        int active=s->ops->status(s->context,donor,AF_HE_ACTIVE);
        if(active<0) {s->failed=1;return -1;}
        if(active)return (int)donor;
    }
    return -1;
}
int af_holiday_transition_index(AFHolidayTransition *s,int donor) {
    AFHolidayMap m;
    if(row(s,donor,&m)!=1)return -1;
    for(u32 i=0;i<17;i++)if(half(s->maps+16+i*20)==(u32)donor)return (int)i;
    s->failed=1;return -1;
}
int af_holiday_transition_count(AFHolidayTransition *s,int index) {
    if(index<0 || index>=17) {s->failed=1;return 0;}
    AFHolidayMap m;int donor=half(s->maps+16+index*20);
    return row(s,donor,&m)==1?(int)m.count:0;
}
int af_holiday_transition_unit(AFHolidayTransition *s,unsigned short *name,int *x,int *z,int donor,int index) {
    AFHolidayMap m;
    if(index<0 || af_holiday_map_get(s->maps,s->map_bytes,donor,s->pool_variant,index,&m)!=1) {
        s->failed=1;*name=0;*x=*z=-100;return 0;
    }
    *name=m.source_name;*x=m.x;*z=m.z;return 1;
}
int af_holiday_transition_structure(AFHolidayTransition *s,int x,int z,unsigned short source,int ux,int uz) {
    int native=s->ops->resolve(s->context,source);
    if(native<=0 || native>65535) {s->failed=1;return 1;}
    return s->ops->structure(s->context,x,z,(unsigned short)native,ux,uz);
}
int af_holiday_transition_ready(AFHolidayTransition *s) {
    if(!s || !s->ops || !s->maps)return 0;
    const AFHolidayTransitionOps *o=s->ops;
    if(!o->status || !o->resolve || !o->structure || !o->landmark || !o->grid || !o->position ||
       !o->block_origin || !o->police || !o->npc_space || !o->near_gate || !o->go || !o->climate ||
       !o->tempo || !o->warp || !o->bgm || !o->correct)return 0;
    s->failed=0;
    int donor=af_holiday_transition_map(s);AFHolidayMap m;
    if(s->failed)return 0;
    if(donor==AF_HT_ORIGINAL_LAYOUT)return 1;
    if(donor<0 || row(s,donor,&m)==0)return 1;
    if(s->failed)return 0;
    for(u32 i=0;i<m.count;i++) {
        unsigned short name;int x,z;
        if(!af_holiday_transition_unit(s,&name,&x,&z,donor,i))return 0;
        if((name>>12)==AF_HT_SOURCE_STRUCTURE) {
            int native=o->resolve(s->context,name);
            if(native<=0 || native>65535) {s->failed=1;return 0;}
        }
    }
    return 1;
}
int af_holiday_transition_original(AFHolidayTransition *s,int x,int z) {
    if(!s->ops->original_collision) {s->failed=1;return 0;}
    int result=s->ops->original_collision(s->context,x,z);
    if(result<0 || result>2) {s->failed=1;return 0;}
    return result;
}
