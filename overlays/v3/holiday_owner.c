/* Shared shrine/wandering owners called by the actual native event manager.
 * Native clock/acre dispatch owns RUN/SHOW; these callbacks do not invent them. */
#include "holiday_owner.h"
#include "holiday_native.h"
#include "npc_registry.h"
typedef unsigned int u32;
extern u32 af_holiday_owner_keep[2];
/* Source D074, D079 respectively. Zero means the actor is still unbound. */
extern const unsigned short af_holiday_owner_names[2];
extern void af_holiday_native_set_status(int,int);
_Static_assert(sizeof(AFHolidayControl)==32,"Native event control size");
static int identify(const AFHolidayControl *c,AFHolidayOwner *owner) {
    if(!c || c->type<AF_HN_FIRST || c->type>=AF_HN_END)return -1;
    u32 donor=af_holiday_source_ids[c->type];
    if(af_holiday_native_type(donor)!=(int)c->type ||
       af_holiday_event_owner(af_holiday_event_data,812,donor,owner)!=1)return -1;
    return donor;
}
static int available(u32 name) {
    const AFNpcExtras *t=&af_v3_npc_extras;
    if(!name || t->magic!=AF_NPC_EXTRA_MAGIC || t->version!=1 || t->count>AF_NPC_EXTRA_MAX || t->stride!=44)return 0;
    for(u32 i=0;i<t->count;i++)if(t->rows[i].name==name)return t->rows[i].flags==3;
    return 0;
}
int af_holiday_owner_unbound(void *manager,AFHolidayControl *c) {
    (void)manager;AFHolidayOwner owner;
    if(identify(c,&owner)>=0)af_holiday_native_set_status(c->type,AF_HE_ERROR);
    return 0;
}
int af_holiday_owner_start(void *manager,AFHolidayControl *c) {
    AFHolidayOwner owner;int donor=identify(c,&owner);
    if(donor<0)return 0;
    if(owner.kind<AF_HE_SHRINE || owner.kind>AF_HE_HALLOWEEN)return af_holiday_owner_unbound(manager,c);
    u32 costume=owner.kind==AF_HE_HALLOWEEN,name=af_holiday_owner_names[costume];
    if(!available(name))return af_holiday_owner_unbound(manager,c);
    u32 index=c->type-AF_HN_FIRST,mask=1u<<(index&31),*word=&af_holiday_owner_keep[index>>5];
    int result=(*word&mask)?2:1;*word|=mask;
    AFHolidayPlace *place=0;
    if(af_holiday_placement_native_make(manager,donor,name,costume?0xD079:0xD074,&place)<0)
        af_holiday_native_set_status(c->type,AF_HE_ERROR);
    /* The donor's dpppp pointer is only read by its developer arrow display.
     * Actual actor placement lives in mEv common storage, not that debug alias. */
    return result;
}
int af_holiday_owner_stop(void *manager,AFHolidayControl *c) {
    (void)manager;AFHolidayOwner owner;
    if(identify(c,&owner)<0)return 0;
    u32 index=c->type-AF_HN_FIRST,mask=1u<<(index&31),*word=&af_holiday_owner_keep[index>>5];
    int result=(*word&mask)?1:2;*word&=~mask;return result;
}
int af_holiday_owner_in(void *manager,AFHolidayControl *c) {
    AFHolidayOwner owner;int donor=identify(c,&owner);
    if(donor<0)return 0;
    if(owner.kind<AF_HE_SHRINE || owner.kind>AF_HE_HALLOWEEN ||
       !available(af_holiday_owner_names[owner.kind==AF_HE_HALLOWEEN]))return af_holiday_owner_unbound(manager,c);
    return af_holiday_placement_native_show(manager,donor,&c->block);
}
int af_holiday_owner_out(void *manager,AFHolidayControl *c) {
    (void)manager;AFHolidayOwner owner;int donor=identify(c,&owner);
    return donor<0?0:af_holiday_placement_native_cull(donor);
}
