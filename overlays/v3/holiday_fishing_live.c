/* Native event storage remains its original size. The source controllers use
 * a checked normalized view; the extended save retains complete identities. */
#include "holiday_fishing_live.h"
typedef unsigned int u32;
_Static_assert(sizeof(AFHFLiveEvent)==32,"Normalized event record");
#ifdef __mips__
_Static_assert(sizeof(AFHFLive)<=768,"Live fishing context reservation");
#endif
static u32 half(const AFHFB *p) {return (u32)p[0]*256+p[1];}
static u32 word(const AFHFB *p) {return half(p)<<16|half(p+2);}
static void put16(AFHFB *p,u32 n) {p[0]=n>>8;p[1]=n;}
static void put32(AFHFB *p,u32 n) {put16(p,n>>16);put16(p+2,n);}
static int equal(const void *a,const void *b,u32 n) {
    for(u32 i=0;i<n;i++)if(((const AFHFB*)a)[i]!=((const AFHFB*)b)[i])return 0;
    return 1;
}
static float random_value(void *context) {(void)context;return af_hf_native_random();}
static int player_index(void *context,const AFHFPerson *p) {
    (void)context;
    if(!p)return -1;
    int empty=1;for(u32 i=0;i<8;i++)if(p->player_name[i]!=' ')empty=0;
    if(p->land_id==0xFFFF && empty)return -1;
    for(u32 i=0;i<4;i++) {
        AFHFPerson native;af_holiday_fish_native_person(&native,af_hf_native_players[i]);
        if(equal(&native,p,sizeof(native)))return (int)i;
    }
    return -1;
}
static int event_npc(void *context,AFHFH *id) {(void)context;return af_hf_native_event_npc(id);}
static void name(void *context,AFHFB *out,AFHFH id) {
    (void)context;
    af_hf_clear(out,8,32);
    if(!af_hf_native_name(out,8,id))af_hf_live.failed=1;
}
static void random_name(void *context,AFHFB *out) {
    u32 used=0,count=0;
    /* Same native fifteen-resident search and single random draw, followed by
       the installed full English name reader instead of the six-byte writer. */
    af_hf_clear(out,8,32);
    for(u32 i=0;i<15;i++) {
        const AFHFB *a=af_hf_native_animals[i];
        if(a[0x4E1]!=255 || a[0x4E2]!=255 || (half(a)&0xF000)==0xE000) {
            used|=1u<<i;++count;
        }
    }
    if(!count) {af_hf_live.failed=1;return;}
    float random=af_hf_native_random();
    if(!(random>=0.0f && random<1.0f)) {af_hf_live.failed=1;return;}
    u32 pick=(u32)(random*count);
    for(u32 i=0;i<15;i++)if(used&(1u<<i)) {
        if(!pick) {name(context,out,(AFHFH)half(af_hf_native_animals[i]));return;}
        --pick;
    }
    af_hf_live.failed=1;
}
static void native_person(AFHFB *out,const AFHFPerson *p) {
    /* This is the original native compatibility key, not displayed text.
       The complete name remains in AFHF and in the normalized event view. */
    af_hf_copy(out,p->player_name,6);af_hf_copy(out+6,p->land_name,6);
    put16(out+12,p->player_id);put16(out+14,p->land_id);
}
int af_hf_live_enter(void) {
    AFHFLive *s=&af_hf_live;
    if(s->active || !af_hf_native_player)return 0;
    af_hf_clear(s,sizeof(*s),0);
    s->wire=af_v3_fishing_data();
    if(!s->wire || !af_holiday_fish_load(&s->records,s->wire,AF_HF_BYTES,s->wire[5]) ||
       !af_holiday_fish_clock(&s->records,&af_hf_native_clock))return 0;
    s->records.services=(AFHFServices){random_value,player_index,event_npc,name,random_name};
    s->records.opaque=&s->records;
    s->native_event=af_hf_native_event_area(af_hf_native_clock.month==6?20:2,0);
    if(!s->native_event)return 0;
    const AFHFB *p=s->native_event;
    s->event.size=(int)word(p);
    if(s->event.size<0 || s->event.size>(s->records.units==AF_HF_INCHES?27:70))return 0;
    af_holiday_fish_native_person(&s->event.person,p+4);
    s->event.position[0]=(short)half(p+20);s->event.position[1]=(short)half(p+22);
    s->event.talk=p[24];s->event.flag=p[25];
    /* Recover the exact full winner for today's native event, not an ambiguous
       global name-prefix search or a cast over the native save allocation. */
    for(u32 i=0;i<5;i++) {
        const AFHFRecord *r=s->records.fishRecord+i;AFHFB key[16];
        if(r->size!=s->event.size || !r->size || r->time.year!=af_hf_native_clock.year ||
           r->time.month!=af_hf_native_clock.month || r->time.day!=af_hf_native_clock.day)continue;
        native_person(key,&r->pid);
        if(equal(key,p+4,16)) {s->event.person=r->pid;break;}
    }
    af_holiday_fish_native_person(&af_hf_controller_person,af_hf_native_player);
    s->active=1;return 1;
}
void af_hf_live_leave(void) {
    AFHFLive *s=&af_hf_live;
    if(!s->active)return;
    if(!s->failed && !s->records.error && af_holiday_fish_store(&s->records,s->wire,AF_HF_BYTES)) {
        AFHFB *p=s->native_event;put32(p,s->event.size);native_person(p+4,&s->event.person);
        put16(p+20,(unsigned short)s->event.position[0]);put16(p+22,(unsigned short)s->event.position[1]);
        p[24]=s->event.talk;p[25]=s->event.flag;
    }
    s->active=0;
}
AFHFLiveEvent *af_hf_live_event(int event,int id) {
    return af_hf_live.active && !id && event==(af_hf_native_clock.month==6?29:54)?&af_hf_live.event:0;
}
int af_hf_live_size(int rank) {
    return af_hf_live.active?af_holiday_fish_size(&af_hf_live.records,rank):-1;
}
int af_hf_live_npc_size(int hour) {
    return af_hf_live.active?af_holiday_fish_npc_size(&af_hf_live.records,(unsigned int)hour):-1;
}
int af_hf_live_event_npc(AFHFH *id) {return af_hf_live.active?event_npc(0,id):0;}
void af_hf_live_name(AFHFB *out,AFHFH id) {if(af_hf_live.active)name(&af_hf_live.records,out,id);}
void af_hf_live_random_name(AFHFB *out) {if(af_hf_live.active)random_name(&af_hf_live.records,out);}
void af_hf_live_record(const AFHFPerson *p,int size) {
    if(!af_hf_live.active || !af_holiday_fish_set(&af_hf_live.records,p,size))af_hf_live.failed=1;
}
int af_hf_live_message(int source) {
    if(af_hf_message_count!=74)return -1;
    for(u32 i=0;i<af_hf_message_count;i++)if(af_hf_message_map[i][0]==source)return af_hf_message_map[i][1];
    return -1;
}
int af_hf_live_number(AFHFB *out,int size,int unit) {
    if(!out || unit!=0x29E || !af_hf_live.active || size<0 ||
       size>(af_hf_live.records.units==AF_HF_INCHES?27:70))return 0;
    const AFHFB *suffix=af_hf_unit_text[af_hf_live.records.units];
    u32 n=0,length=0;
    while(length<16 && suffix[length])++length;
    if(!length || length+3+(size>=10)>16)return 0;
    if(size>=10)out[n++]=(AFHFB)('0'+size/10);
    out[n++]=(AFHFB)('0'+size%10);out[n++]=' ';
    for(u32 i=0;i<length;i++)out[n++]=suffix[i];
    return (int)n;
}
void af_hf_live_topname(void) {
    if(!af_hf_live.active)return;
    AFHFB number[16];int n=af_hf_live_number(number,af_hf_live.event.size,0x29E);
    void *window=af_hf_native_window();
    if(n && window) {
        af_hf_native_string(window,1,number,n);
        af_hf_native_string(window,0,af_hf_live.event.person.player_name,8);
    }
}
