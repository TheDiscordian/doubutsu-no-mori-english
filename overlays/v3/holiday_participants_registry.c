/* Shared descriptors, admission, and temporary resident identities. Native
 * villagers retain their own pools, resource loader, clothing, voice, and saves.
 * This is not the static special-character/artwork registry. */
#include "holiday_participants.h"
#ifdef AF_HP_EXERCISE_REGISTRY
#include "npc_registry.h"
extern int af_holiday_native_type(unsigned int),af_hp_native_event_status(int,int);
#endif
typedef struct {u32 vrom,end,ram,ram_end,loaded;ACTOR_PROFILE *profile;u32 filename;u16 allocation;u8 count,pad;} Descriptor;
typedef struct {ACTOR_PROFILE profile;Descriptor descriptor;} Owner;
static Owner owners[AF_HP_OWNER_COUNT];
static AFHPResident residents[AF_HP_RESIDENT_COUNT];
static u8 retiring[AF_HP_RESIDENT_COUNT];
typedef struct {ACTOR *actor;u8 constructed;mActor_proc move,draw;} Live;
static Live live[AF_HP_LIVE_COUNT];
extern void *af_hp_previous_descriptor(int);
extern AFHPResident *af_hp_previous_event(u16);
extern void af_hp_previous_unregister(u16),af_hp_previous_clear(void);
extern AFHPResident af_hp_native_events[5];
extern void af_hp_previous_free(ACTOR *);
extern int af_hp_native_resident_index(u16);
extern int af_hp_native_resident_valid(int,u16);
extern volatile const u8 af_hp_native_ticks;
#ifdef __mips__
_Static_assert(sizeof(ACTOR_PROFILE)==36,"Complete native profile");
_Static_assert(sizeof(Descriptor)==32,"Complete native descriptor");
#endif
_Static_assert(sizeof(AFHPResident)==12,"Native temporary resident record");
static int name_index(u16 name) {
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=&af_hp_records[i];
        if(r->count && name>=r->name && name-r->name<r->count)return (int)i;
    }
    return -1;
}
static int profile_index(int profile) {
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++)if(profile==af_hp_records[i].profile)return (int)i;
    return -1;
}
static int identity(const ACTOR *actor) {
    if(!actor)return -1;
    int index=profile_index(*(const s16 *)actor);
    if(index<0)return -1;
    const AFHPRecord *r=&af_hp_records[index];
    if(r->count?name_index(actor->npc_id)!=index:actor->npc_id!=0)return -1;
#ifdef AF_HP_EXERCISE_REGISTRY
    if(r->kind&AF_HP_SPECIAL) {
        const AFNpcExtra *extra=af_v3_npc_extra_owned(actor);
        return extra && extra->flags==3 && extra->profile==r->profile &&
            *(const void *const *)((const u8 *)actor+0x170)==extra->descriptor?index:-1;
    }
#endif
    /* The native actor owns this exact resident descriptor. */
    if(*(const void *const *)((const u8 *)actor+0x170)!=&owners[index].descriptor)return -1;
    return index;
}
int af_hp_owned(const ACTOR *actor) {return identity(actor)>=0;}
void af_hp_constructed(ACTOR *actor) {
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor==actor)live[i].constructed=1;
}
static void npc_move(ACTOR *a,GAME *g) {
    if(!af_hp_admit(a,g)) {Actor_delete(a);return;}
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor==a && live[i].constructed && live[i].move) {
        live[i].move(a,g);return;
    }
    Actor_delete(a);
}
static void npc_draw(ACTOR *a,GAME *g) {
    if(!af_hp_admit(a,g))return;
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor==a && live[i].constructed && live[i].draw) {
        live[i].draw(a,g);return;
    }
}
int af_hp_npc_callbacks(ACTOR *a,aNPC_ct_data_c *data) {
    if(!data || !data->move || !data->draw)return 0;
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor==a && !live[i].constructed) {
        live[i].move=data->move;live[i].draw=data->draw;
        data->move=npc_move;data->draw=npc_draw;return 1;
    }
    return 0;
}
static AFHPResident *resident(u16 name) {
    for(unsigned int i=0;i<AF_HP_RESIDENT_COUNT;i++)if(residents[i].used && residents[i].event_name==name)return residents+i;
    return 0;
}
AFHPResident *af_hp_event_lookup(u16 name) {
    return name_index(name)>=0?resident(name):af_hp_previous_event(name);
}
void af_hp_event_unregister(u16 name) {
    if(name_index(name)<0) {af_hp_previous_unregister(name);return;}
    AFHPResident *r=resident(name);
    if(!r)return;
    int busy=0;
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor && live[i].actor->npc_id==name) {
        Actor_delete(live[i].actor);busy=1;
    }
    /* Keep the identity available until the ordinary NPC destructor has
     * released its clothes, texture, and resident references. */
    retiring[r-residents]=(u8)busy;
    if(!busy)*r=(AFHPResident){0};
}
void af_hp_events_clear(void) {
    for(unsigned int i=0;i<AF_HP_RESIDENT_COUNT;i++)if(residents[i].used)
        af_hp_event_unregister(residents[i].event_name);
    af_hp_previous_clear();
}
int af_hp_resident_bind(u16 source,u16 npc,u16 cloth) {
    const AFHPRecord *r=0;unsigned int role=0;
    if(!af_hp_available)return -1;
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *p=af_hp_records+i;
        if(p->count && !(p->kind&AF_HP_SPECIAL) && source>=p->source_name && source-p->source_name<p->count) {
            r=p;role=source-p->source_name;break;
        }
    }
    int index=af_hp_native_resident_index(npc);
    if(!r || index<0 || !af_hp_native_resident_valid(index,npc))return -1;
    for(unsigned int i=0;i<5;i++)if(af_hp_native_events[i].used && af_hp_native_events[i].resident==npc)return -1;
    u16 name=r->name+role;
    AFHPResident *empty=0;
    for(unsigned int i=0;i<AF_HP_RESIDENT_COUNT;i++) {
        AFHPResident *p=residents+i;
        if(!p->used) {if(!empty)empty=p;continue;}
        if(p->event_name==name)
            return !retiring[i] && p->resident==npc && p->texture==npc && p->cloth==cloth?name:-1;
        if(p->resident==npc)return -1;
    }
    if(!empty)return -1;
    *empty=(AFHPResident){name,npc,npc,cloth,0,1,0};return name;
}
int af_hp_name_profile(u16 name) {
    int index=name_index(name);return index>=0?af_hp_records[index].profile:-1;
}
static int ready(const AFHPRecord *r) {
    if(!r->source || !r->source->ctor || !r->source->dtor ||
       !r->source->move || !r->source->draw || (r->kind&~3u) || !r->event ||
       r->source->actor_bytes<sizeof(ACTOR) || r->source->actor_bytes>2400)return 0;
    return r->count?(r->part==3 && r->source->actor_bytes>=sizeof(NPC_ACTOR)):
        r->part==7 || (r->part==4 && r->source->actor_bytes==sizeof(ACTOR));
}
int af_hp_identity(unsigned int kind,unsigned int source) {
    /* Event preflight runs before resident selection or actor construction.
     * Resolve the installed identity, not a currently spawned instance. The
     * category selection/dependency gate still rejects unfinished admission. */
    if(!af_hp_available)return -1;
    if(kind==2)return source==118?119:-1;
    if(kind>1 || source>65535)return -1;
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(!ready(r))continue;
        if(kind==1 && r->source->source_profile==(int)source)return r->profile;
        if(kind==0 && r->count && source>=r->source_name && source-r->source_name<r->count)
            return r->name+source-r->source_name;
    }
    return -1;
}
void *af_hp_descriptor(int profile) {
    int index=profile_index(profile);
    if(index<0)return af_hp_previous_descriptor(profile);
    const AFHPRecord *r=af_hp_records+index;Owner *o=owners+index;
    if(!ready(r))return 0;
    if(r->kind&AF_HP_SPECIAL)return af_hp_previous_descriptor(profile);
    if(!o->descriptor.profile) {
        o->profile=(ACTOR_PROFILE){r->profile,r->part,r->native_flags,r->name,3,
            r->source->actor_bytes,af_hp_ctor,af_hp_dtor,af_hp_step,af_hp_draw,af_hp_save};
        o->descriptor.profile=&o->profile;
    }
    return &o->descriptor;
}
int af_hp_admit(ACTOR *a,GAME *g) {
    int index=identity(a);
    if(!af_hp_available || !g || index<0 || !ready(af_hp_records+index))return 0;
    const AFHPRecord *r=af_hp_records+index;
    if(r->kind&AF_HP_NO_SAVE) {
#ifdef AF_HP_EXERCISE_REGISTRY
        int a=af_holiday_native_type(r->event),b=af_holiday_native_type(r->save);
        if(!((a>=0 && af_hp_native_event_status(a,16)) ||
                (b>=0 && af_hp_native_event_status(b,16))))return 0;
#else
        return 0;
#endif
    } else if(!mEv_get_save_area(r->event,r->save))return 0;
    if(r->count && !(r->kind&AF_HP_SPECIAL)) {
        AFHPResident *e=resident(a->npc_id);
        if(!e || retiring[e-residents] ||
                !af_hp_native_resident_valid(af_hp_native_resident_index(e->resident),e->resident))return 0;
    }
    return 1;
}
void af_hp_ctor(ACTOR *a,GAME *g) {
    int index=identity(a);
    if(index<0) {Actor_delete(a);return;}
    const AFHPRecord *r=af_hp_records+index;
    if(!af_hp_available || !g || !ready(r)) {Actor_delete(a);return;}
    Live *slot=0;
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(!live[i].actor) {slot=live+i;break;}
    if(!slot) {Actor_delete(a);return;}
    *slot=(Live){.actor=a};
    /* Some complete source constructors dereference a failed reservation. Admit
     * only after the actual native save area exists, before any source call. */
    if(!(r->kind&AF_HP_NO_SAVE)) {
        void *area=mEv_get_save_area(r->event,r->save);
        if(!area)area=mEv_reserve_save_area(r->event,r->save);
        if(!area) {Actor_delete(a);return;}
    }
    if(!af_hp_admit(a,g)) {Actor_delete(a);return;}
    r->source->ctor(a,g);
    if(!r->count)slot->constructed=1;
    else if(!slot->constructed)Actor_delete(a);
}
void af_hp_dtor(ACTOR *a,GAME *g) {
    int index=identity(a);
    if(index<0)return;
    const AFHPRecord *r=af_hp_records+index;
    for(unsigned int i=0;i<AF_HP_LIVE_COUNT;i++)if(live[i].actor==a) {
        if(live[i].constructed)r->source->dtor(a,g);
        live[i]=(Live){0};break;
    }
    if(!r->count && owners[index].descriptor.count)--owners[index].descriptor.count;
    AFHPResident *e=r->count && !(r->kind&AF_HP_SPECIAL)?resident(a->npc_id):0;
    if(e && retiring[e-residents]) {retiring[e-residents]=0;*e=(AFHPResident){0};}
    /* Failed admission never entered the NPC constructor. Native deletion
     * still releases the allocation and object references through its caller. */
}
void af_hp_step(ACTOR *a,GAME *g) {
    int i=identity(a);
    if(i>=0 && af_hp_admit(a,g))af_hp_records[i].source->move(a,g);
    else Actor_delete(a);
}
void af_hp_draw(ACTOR *a,GAME *g) {
    int i=identity(a);if(i>=0 && af_hp_admit(a,g))af_hp_records[i].source->draw(a,g);
}
void af_hp_save(ACTOR *a,GAME *g) {
    int i=identity(a);
    if(i>=0 && af_hp_admit(a,g) && af_hp_records[i].source->save)af_hp_records[i].source->save(a,g);
}
void af_hp_free(ACTOR *a) {
    int i=identity(a);
    if(i>=0 && af_hp_records[i].count && !(af_hp_records[i].kind&AF_HP_SPECIAL) &&
            owners[i].descriptor.count)--owners[i].descriptor.count;
    af_hp_previous_free(a);
}
int af_hp_countdown(int value) {
    unsigned int ticks=af_hp_native_ticks;
    return value>0 && (unsigned int)value>ticks?value-(int)ticks:0;
}
unsigned int af_hp_elapsed(void) {return af_hp_native_ticks;}
