/* One actual N64 primitive adapter for every generated dedicated owner. */
#include "holiday_dedicated_native.h"
#include "holiday_reserved.h"
#include "holiday_native.h"
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
typedef __INTPTR_TYPE__ iptr;
extern const u32 af_holiday_manager_descriptor[8];
extern u32 af_holiday_owner_keep[2];
extern u16 af_holiday_native_field_id(void);
extern int af_holiday_native_check_field(void);
extern int af_holiday_native_pool_variant(void);
extern int af_holiday_native_landmark(int *,int *,u32);
extern AFHolidayPlace *af_holiday_native_get_place(int,u8);
extern AFHolidayPlace *af_holiday_native_reserve_place(int,u8);
extern void af_holiday_native_clear_place(int,u8);
extern int af_holiday_native_structure(u16,int,int,int,int,int);
extern int af_holiday_native_check_status(int,int);
extern void af_holiday_native_set_status(int,int);
extern void af_holiday_native_clear_status(int,int);
extern void af_holiday_native_unable_wade(int);
#ifndef FN
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
#endif
typedef struct {
    void *manager;
    u32 owner;
    AFHolidayControl *control;
    const AFHolidayDedicatedServices *services;
} Native;
static int outdoors(void *c) {(void)c;return !(af_holiday_native_field_id()&0xF000);}
static int landmark(void *c,u32 kind,AFHolidayBlock *b) {
    Native *n=c;const int *w=n->manager;
    u32 offset=kind==32768?0x214:kind==4?0x22C:kind==32?0x220:kind==1?0x238:0;
    if(offset) {
        if(!w[(offset+8)/4])return 0;
        *b=(AFHolidayBlock){w[offset/4],w[offset/4+1]};return 1;
    }
    return af_holiday_native_landmark(&b->x,&b->z,kind);
}
static u32 resolve(void *c,u32 source) {
    Native *n=c;int name=n->services->resolve(n->services->context,AF_HD_NAME,source);
    return name>0 && name<=65535?(u32)name:0;
}
static AFHolidayPlace *get(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_get_place(t,id);}
static AFHolidayPlace *reserve(void *c,u32 t,u32 id) {(void)c;return af_holiday_native_reserve_place(t,id);}
static int foreground(void *c,const AFHolidayPlace *p) {
    (void)c;return af_holiday_native_structure(p->name,p->block.x,p->block.z,p->unit.x,p->unit.z,0);
}
static void error(void *c,u32 t) {(void)c;af_holiday_native_set_status(t,AF_HE_ERROR);}
static iptr operation(void *c,u32 op,int donor,int a,int b,int id) {
    Native *n=c;const AFHolidayDedicatedServices *s=n->services;
    int type=af_holiday_native_type(donor);
    if(type<AF_HN_FIRST || type>=AF_HN_END)return 0;
    u32 index=(u32)type-AF_HN_FIRST,mask=1u<<(index&31),*keep=&af_holiday_owner_keep[index>>5];
    switch(op) {
    case AF_HD_KEEP:return !!(*keep&mask);
    case AF_HD_SET_KEEP:*keep|=mask;return 0;
    case AF_HD_CLEAR_KEEP:*keep&=~mask;return 0;
    case AF_HD_STATUS:return af_holiday_native_check_status(type,a);
    case AF_HD_SET_STATUS:af_holiday_native_set_status(type,a);return 0;
    case AF_HD_CLEAR_STATUS:af_holiday_native_clear_status(type,a);return 0;
    case AF_HD_FADE:return s->fade(s->context,n->manager,donor,type,a,b);
    case AF_HD_CLEAN:
        FN(n->owner+0x19D0,void,void *,u32)(n->manager,a);return 0;
    case AF_HD_FOREGROUND:case AF_HD_ACTOR: {
        if(!outdoors(c))return 0;
        AFHolidayMap row;int variant=b==32768?af_holiday_native_pool_variant():0;
        /* The source callback and source map must identify the same landmark.
         * Never silently relocate a mismatched layout to a different acre. */
        if(a<0 || id<0 || id>255 || variant<0 ||
           af_holiday_map_get(s->maps,s->map_bytes,donor,variant,a,&row)!=1 || row.kind!=(u32)b) {
            error(c,type);return 0;
        }
        AFHolidayReservedOps ops={n,outdoors,landmark,resolve,get,reserve,foreground,error};
        return (iptr)af_holiday_reserved_make(s->maps,s->map_bytes,&ops,donor,type,variant,a,id,
            op==AF_HD_FOREGROUND);
    }
    case AF_HD_DELETE_FOREGROUND:case AF_HD_DELETE_FOREGROUND_UNCHECKED: {
        if(a<0 || a>255 || af_holiday_native_check_field()!=1)return 0;
        AFHolidayPlace *p=get(c,type,a);
        if(p) {
            int ok=af_holiday_native_structure(p->name,p->block.x,p->block.z,p->unit.x,p->unit.z,1);
            if(!ok && op==AF_HD_DELETE_FOREGROUND) {error(c,type);return 0;}
            af_holiday_native_clear_place(type,a);
        }
        return 1;
    }
    case AF_HD_CLEAR_PLACE:
        if(a<0 || a>255) {error(c,type);return 0;}
        af_holiday_native_clear_place(type,a);return 0;
    case AF_HD_SHOW:
        if(a<0 || a>255 || (b!=0 && b!=1)) {error(c,type);return 0;}
        if(b) {
            int result=af_holiday_placement_native_show_id(n->manager,donor,a,&n->control->block);
            return result==2?-1:result==1?(iptr)get(c,type,a):0;
        }
        return (iptr)FN(n->owner+0x2740,AFHolidayPlace *,void *,AFHolidayControl *,u8)(
            n->manager,n->control,a);
    case AF_HD_CONTROL:case AF_HD_EFFECT:case AF_HD_DELETE_EFFECT: {
        int native=s->resolve(s->context,op==AF_HD_CONTROL?AF_HD_PROFILE:AF_HD_EFFECT_ID,a);
        if(native<0 || native>32767) {error(c,type);return 0;}
        if(op==AF_HD_CONTROL)return FN(n->owner+0x2170,int,void *,AFHolidayControl *,short)(
            n->manager,n->control,native);
        FN(n->owner+(op==AF_HD_EFFECT?0x2B54:0x2BEC),void,int)(native);return 0;
    }
    case AF_HD_UNABLE_WADE:af_holiday_native_unable_wade(a);return 0;
    default:error(c,type);return 0;
    }
}
int af_holiday_dedicated_native(void *manager,AFHolidayControl *control,AFHolidayDedicatedCommon *common,
        const AFHolidayDedicatedServices *services,u32 phase) {
    const u32 *d=af_holiday_manager_descriptor;
    if(!manager || !control || !common || !services || !services->resolve || !services->fade ||
       !services->maps || services->map_bytes<356 || phase>=5 ||
       control->type<AF_HN_FIRST || control->type>=AF_HN_END ||
       d[0]!=0x03800000 || d[2]!=0x8095B8B0 || d[3]-d[2]!=d[1]-d[0] ||
       d[1]-d[0]<42384 || d[1]-d[0]>65536 || d[4]<0x80000000 || d[4]>=0x80800000 ||
       d[1]-d[0]>0x80800000-d[4])return -1;
    u32 donor=af_holiday_source_ids[control->type];AFHolidayOwner row;
    if(af_holiday_native_type(donor)!=(int)control->type ||
       af_holiday_event_owner(af_holiday_event_data,812,donor,&row)!=1 || row.kind!=4)return -1;
    Native n={manager,d[4],control,services};const int *w=manager;
    AFHolidayDedicated ctx={&n,operation,common,w[0x21C/4],w[0x234/4]};
    return af_holiday_dedicated(&ctx,donor,phase);
}
