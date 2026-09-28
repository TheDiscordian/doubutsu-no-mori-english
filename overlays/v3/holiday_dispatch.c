/* One dispatch path for every dedicated event, using the installed common
 * state and transition services. Missing identities cannot partly start it. */
#include "holiday_dispatch.h"
#include "holiday_active.h"
#include "holiday_native.h"
extern void af_holiday_native_set_status(int,int);
static const AFHolidayNeeds *needs(unsigned int donor) {
    for(unsigned int i=0;i<14;i++)
        if(af_holiday_owner_needs[i].donor==donor)return &af_holiday_owner_needs[i];
    return 0;
}
int af_holiday_dedicated_ready(unsigned int donor,const AFHolidayDedicatedServices *s) {
    const AFHolidayNeeds *r=needs(donor);
    if(!r || !s || !s->resolve || !s->fade || !s->maps || s->map_bytes!=1496 ||
       r->first>af_holiday_identity_need_count ||
       r->count>af_holiday_identity_need_count-r->first)return 0;
    for(unsigned int i=0;i<r->count;i++) {
        const AFHolidayNeed *n=&af_holiday_identity_needs[r->first+i];
        if(n->kind>AF_HD_EFFECT_ID)return 0;
        int value=s->resolve(s->context,n->kind,n->source);
        if(value<0 || value>(n->kind==AF_HD_NAME?65534:32767) ||
           (n->kind==AF_HD_NAME && !value))return 0;
    }
    return 1;
}
int af_holiday_dedicated_dispatch(void *manager,AFHolidayControl *control,
        const AFHolidayDedicatedServices *s,unsigned int phase) {
    if(!manager || !control || phase>AF_HE_BEHIND ||
       control->type<AF_HN_FIRST || control->type>=AF_HN_END)return 0;
    unsigned int donor=af_holiday_source_ids[control->type];
    const AFHolidayNeeds *r=needs(donor);
    if(!r || af_holiday_native_type(donor)!=(int)control->type)return 0;
    if(!(r->phases&(1u<<phase)))return 0; /* Actual null source callback. */
    if(!af_holiday_dedicated_ready(donor,s)) {
        af_holiday_native_set_status(control->type,AF_HE_ERROR);return 0;
    }
    int result=af_holiday_dedicated_current(manager,control,s,phase);
    if(result<0 || result>2) {
        af_holiday_native_set_status(control->type,AF_HE_ERROR);return 0;
    }
    return result;
}
static int call(void *manager,AFHolidayControl *control,unsigned int phase) {
    AFHolidayDedicatedServices services;
    if(!af_holiday_dedicated_bind(&services))return 0;
    return af_holiday_dedicated_dispatch(manager,control,&services,phase);
}
#define ENTRY(name,phase) int af_holiday_dedicated_##name(void *m,AFHolidayControl *c) {return call(m,c,phase);}
ENTRY(start,AF_HE_START)
ENTRY(stop,AF_HE_END)
ENTRY(in,AF_HE_ENTER)
ENTRY(out,AF_HE_LEAVE)
ENTRY(behind,AF_HE_BEHIND)
