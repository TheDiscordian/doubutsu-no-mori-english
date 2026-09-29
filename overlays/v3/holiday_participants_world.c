/* Shared town-placement readers. Imported map indices never index the original
 * fifteen-entry native table. Existing events retain their original readers. */
#include "holiday_participants.h"
#include "holiday_reserved.h"
enum {FIRST_MAP=15,MAP_COUNT=17,MAP_BYTES=1496};
extern const u8 af_holiday_transition_maps[MAP_BYTES];
extern int af_holiday_native_type(unsigned int);
extern int af_hp_native_event_status(int,int),af_hp_native_pool_variant(void);
extern void af_hp_native_event_error(int,int);
extern void af_hp_native_joint_initial(u8 *,int),af_hp_native_joint_removed(u8 *,int),af_hp_native_joint_refill(u8 *,int);
extern int af_hp_native_resident_valid(int,u16),af_hp_native_resident_index(u16);
extern u8 af_hp_native_animals[15][0x528];
extern int af_hp_native_sex(int),af_hp_uniform(unsigned int);
extern int af_hp_world_previous_active(void),af_hp_world_previous_index(int);
extern unsigned int af_hp_world_previous_kind(int);
extern int af_hp_world_previous_count(int),af_hp_world_previous_all(int);
extern int af_hp_world_previous_position(int *,int *,int,int);
extern int af_hp_world_previous_named_position(u16 *,int *,int *,int,int);
extern void af_hp_world_previous_initial(u8 *,int),af_hp_world_previous_refill(u8 *,int);
extern void af_hp_world_previous_name(u16 *,int,int,int);
extern int af_hp_world_previous_random(u16 *);
extern int af_hp_world_previous_lap(int,int);
extern int af_hp_native_structure(int,int,u16,int,int);
extern int af_decor_actor_resolve(u16);
static unsigned int source_at(int index) {
    if(index<FIRST_MAP || index>=FIRST_MAP+MAP_COUNT)return 0;
    const u8 *p=af_holiday_transition_maps+16+(index-FIRST_MAP)*20;
    return (unsigned int)p[0]*256+p[1];
}
static int native_index(int event) {
    if(event<0)return -1;
    for(int i=FIRST_MAP;i<FIRST_MAP+MAP_COUNT;i++) {
        unsigned int source=source_at(i);
        if(source && af_holiday_native_type(source)==event)return i;
    }
    return -1;
}
static int enabled(unsigned int event) {
    if(!af_hp_available)return 0;
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(r->part==7 && r->event==event)return 1;
        if((r->kind&AF_HP_NO_SAVE) && (r->event==event || r->save==event))return 1;
    }
    return 0;
}
static int layout(int index,int slot,AFHolidayMap *out) {
    unsigned int source=source_at(index);
    if(!source || slot<0 || !enabled(source))return 0;
    if(af_holiday_map_get(af_holiday_transition_maps,MAP_BYTES,source,0,slot,out)!=1 ||
            out->normal_npcs>5)return 0;
    if(out->kind!=32768)return 1;
    int variant=af_hp_native_pool_variant();
    return variant>=0 && af_holiday_map_get(af_holiday_transition_maps,MAP_BYTES,
        source,variant,slot,out)==1;
}
int af_hp_world_active(void) {
    /* Source directory order supplies event precedence. Calendar mode must
     * admit imported owners before this reader is enabled. */
    for(int i=FIRST_MAP;i<FIRST_MAP+MAP_COUNT;i++) {
        unsigned int source=source_at(i);AFHolidayMap row;
        if(!enabled(source) || !layout(i,0,&row))continue;
        int native=af_holiday_native_type(source);
        if(native>=0 && af_hp_native_event_status(native,AF_HE_ACTIVE))return native;
    }
    return af_hp_world_previous_active();
}
int af_hp_world_index(int event) {
    int index=native_index(event);AFHolidayMap row;
    return index<0?af_hp_world_previous_index(event):layout(index,0,&row)?index:-1;
}
unsigned int af_hp_world_kind(int index) {
    if(index<0)return 0;
    if(index<FIRST_MAP)return af_hp_world_previous_kind(index);
    AFHolidayMap row;return layout(index,0,&row)?row.kind:0;
}
int af_hp_world_count(int index) {
    if(index<0)return 0;
    if(index<FIRST_MAP)return af_hp_world_previous_count(index);
    AFHolidayMap row;return layout(index,0,&row)?(int)row.normal_npcs:0;
}
int af_hp_world_all(int index) {
    if(index<0)return 0;
    if(index<FIRST_MAP)return af_hp_world_previous_all(index);
    AFHolidayMap row;return layout(index,0,&row)?(int)row.count:0;
}
int af_hp_world_position(int *x,int *z,int index,int slot) {
    if(index<0 || !x || !z || slot<0)return 0;
    if(index<FIRST_MAP)return af_hp_world_previous_position(x,z,index,slot);
    AFHolidayMap row;if(!x || !z || !layout(index,slot,&row))return 0;
    *x=(int)row.x;*z=(int)row.z;return 1;
}
static int role_name(u16 source) {
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(r->count && source>=r->source_name && source-r->source_name<r->count)
            return r->name+source-r->source_name;
    }
    return -1;
}
int af_hp_world_named_position(u16 *name,int *x,int *z,int event,int slot) {
    int index=native_index(event);
    if(index<0)return af_hp_world_previous_named_position(name,x,z,event,slot);
    AFHolidayMap row;if(!name || !x || !z || !layout(index,slot,&row))return 0;
    int target=role_name((u16)row.source_name);
    if(target<0)target=af_decor_actor_resolve((u16)row.source_name);
    /* Tortimer/Miko are separately registered special actors, not residents. */
    if(target<0 && row.source_name==0xD074)target=0xD090;
    if(target<0 && row.source_name==0xD03D)target=0xD091;
    if(target<=0 || target>65534)return 0;
    *name=(u16)target;*x=(int)row.x;*z=(int)row.z;return 1;
}
static int joint(u8 *area,int event,int refresh) {
    int index=native_index(event);AFHolidayMap row;
    if(index<0)return -1;
    if(!area || !layout(index,0,&row) || area!=mEv_get_save_area(row.event,15) ||
            !af_hp_private())return 0;
    unsigned int seen=0;
    for(unsigned int i=0;i<5;i++) {
        unsigned int id=area[i];
        if(!refresh || i>=row.normal_npcs || id>=15 || (seen&(1u<<id)))area[i]=255;
        else seen|=1u<<id;
    }
    if(refresh) {
        af_hp_native_joint_removed(area,(int)row.normal_npcs);
        af_hp_native_joint_refill(area,(int)row.normal_npcs);
    } else af_hp_native_joint_initial(area,(int)row.normal_npcs);
    return 1;
}
void af_hp_world_initial(u8 *area,int event) {
    if(joint(area,event,0)<0)af_hp_world_previous_initial(area,event);
}
void af_hp_world_refill(u8 *area,int event) {
    if(joint(area,event,1)<0)af_hp_world_previous_refill(area,event);
}
void af_hp_world_name(u16 *name,int event,int animal,int slot) {
    int index=native_index(event);
    if(index<0) {af_hp_world_previous_name(name,event,animal,slot);return;}
    AFHolidayMap row;
    if(!name || slot<0 || !layout(index,slot,&row) || (unsigned int)slot>=row.normal_npcs)return;
    int target=role_name((u16)row.source_name);
    if(target<0)return;
    const u8 *area=mEv_get_save_area(row.event,15);
    int valid=area && area[slot]==animal && af_hp_native_resident_valid(animal,*name);
    if(valid && (row.npc_flags&(1u<<slot))) {
        unsigned int cloth=row.source_cloth;
        if(cloth && af_hp_native_sex(af_hp_native_animals[animal][11])==0)++cloth;
        int uniform=af_hp_uniform(cloth);
        valid=uniform>=0 && af_hp_resident_bind((u16)row.source_name,*name,(u16)uniform)==target;
    } else valid=0;
    /* A failed registration still resolves to the guarded role descriptor;
     * it cannot create an ordinary villager in a special actor's place. */
    *name=(u16)target;
    if(!valid)af_hp_native_event_error(event,AF_HE_ERROR);
}
int af_hp_world_random(u16 *name) {
    int event=af_hp_world_active(),index=native_index(event);
    if(index<0)return af_hp_world_previous_random(name);
    AFHolidayMap row;if(!name || !layout(index,0,&row))return 0;
    const u8 *area=mEv_get_save_area(row.event,15);if(!area)return 0;
    u16 candidates[5];unsigned int count=0;
    for(unsigned int i=0;i<row.normal_npcs;i++)if(area[i]<15) {
        u16 npc=*(u16 *)af_hp_native_animals[area[i]];
        if(af_hp_native_resident_valid(area[i],npc))candidates[count++]=npc;
    }
    if(!count)return 0;
    unsigned int selected=(unsigned int)(fqrand()*count);
    if(selected>=count)return 0;
    *name=candidates[selected];return 1;
}
int af_hp_world_lap(int x,int z) {
    int event=af_hp_world_active(),index=native_index(event);
    if(index<0)return af_hp_world_previous_lap(x,z);
    AFHolidayMap row;if(!layout(index,0,&row))return 0;
    unsigned int count=row.count;
    for(unsigned int i=0;i<count;i++) {
        if(!layout(index,(int)i,&row)) {af_hp_native_event_error(event,AF_HE_ERROR);return 2;}
        if(row.source_name>>12==5) {
            int name=af_decor_actor_resolve((u16)row.source_name);
            if(name<=0 || name>65534) {af_hp_native_event_error(event,AF_HE_ERROR);return 2;}
            if(af_hp_native_structure(x,z,(u16)name,(int)row.x,(int)row.z)==1)return 2;
        } else if(x>=(int)row.x-1 && x<=(int)row.x+1 &&
                z>=(int)row.z-1 && z<=(int)row.z+1)return 1;
    }
    /* Use all source layout positions, including the unspawned fifth New Year
     * queue position. Collision does not invent an actor identity for it. */
    return 0;
}
