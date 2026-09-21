#define AF_V3_ROOM_SCROLL_LIFECYCLE 1
#define AF_V3_ROOM_CONTACT 1
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_scroll.c"

RoomScrollTable af_v3_test_room_scroll;
RoomScrollLives af_v3_test_room_scroll_lives;
RoomContactClip *af_v3_test_contact_clip;
signed char af_v3_test_contact_floor;
u8 *af_v3_room_debug;
void *_Matrix_to_Mtx(void *p) { return p; }
void osWritebackDCache(void *p,int n) { (void)p;(void)n; }
void sAdo_OngenPos(u32 handle,u8 sound,float *position) {
    (void)handle;(void)sound;(void)position;assert(0);
}
void sAdo_OngenTrgStart(u32 sound,float *position) { (void)sound;(void)position;assert(0); }

/* The source and native helpers are independently pinned in the Python
   contract. This host implementation checks callback arguments and progression;
   it is not evidence of native MIPS execution. */
static unsigned steps;
float add_calc(float *value,float target,float fraction,float maximum,float minimum) {
    assert(target==0.0f || target==1.0f);
    assert(fraction==0.04f && maximum==0.1f && minimum==0.001f);
    ++steps;
    if (*value!=target) {
        float step=fraction*(target-*value);
        if (step<=-minimum || minimum<=step) {
            if (step>maximum) step=maximum;
            else if (step<-maximum) step=-maximum;
        } else step=step>0.0f ? minimum : -minimum;
        *value+=step;
        if (step>0.0f ? *value>target : *value<target) *value=target;
    }
    return target-*value;
}

int main(void) {
    RoomScrollLives *table=&af_v3_test_room_scroll_lives;
    *table=(RoomScrollLives){.magic=ROOM_SCROLL_LIFE_MAGIC,.count=1,.stride=12,
        .rows={{.index=1256,.mode=3,.on=48,.off=71}}};
    struct { u8 before[16];RoomScrollActor actor;u8 after[16]; } guarded;
    RoomContactOwner owner={0};RoomContactClip clip={&owner};
    RoomScrollActor *actor=&guarded.actor;
    /* Synthetic second floor 71 proves that the callback consumes record
       identities; it does not add this floor to any cartridge. */
    for (unsigned alias=0;alias<2;++alias) for (int floor=-1;floor<=72;++floor)
        for (int state=-1;state<=16;++state) for (int direction=0;direction<4;++direction) {
            memset(&guarded,0xAD,sizeof(guarded));
            actor->index=1256+1024*alias;actor->state=state;
            RoomScrollActor expected=*actor;expected.colour.f=0.0f;
            af_v3_room_scroll_ct(actor,NULL);
            assert(!memcmp(actor,&expected,sizeof(expected)));
            af_v3_test_contact_clip=&clip;af_v3_test_contact_floor=floor;owner.direction=direction;
            steps=0;af_v3_room_scroll_mv(actor,NULL,NULL,NULL);
            int active=(floor==48 || floor==71) && state>=1 && state<=4 && direction==0;
            float want=0.04f;want+=0.04f*(1.0f-want);
            expected.colour.f=active ? want : 0.0f;
            assert(steps==(active ? 2u : 0u) && !memcmp(actor,&expected,sizeof(expected)));
            af_v3_room_scroll_dt(actor,NULL);
            assert(!memcmp(actor,&expected,sizeof(expected)));
            for (unsigned i=0;i<16;++i)assert(guarded.before[i]==0xAD && guarded.after[i]==0xAD);
        }
    actor->index=1256;actor->state=4;af_v3_test_contact_floor=48;owner.direction=0;
    for (unsigned missing=0;missing<2;++missing) {
        af_v3_test_contact_clip=missing ? &clip : NULL;clip.owner=NULL;
        actor->colour.f=1.0f;steps=0;af_v3_room_scroll_mv(actor,NULL,NULL,NULL);
        float want=0.96f;want-=0.04f*want;
        assert(actor->colour.f==want && steps==2);
    }
    clip.owner=&owner;af_v3_test_contact_clip=&clip;
    actor->colour.f=0.9995f;steps=0;af_v3_room_scroll_mv(actor,NULL,NULL,NULL);
    assert(actor->colour.f==1.0f && steps==1);
    owner.direction=1;actor->colour.f=0.0005f;steps=0;af_v3_room_scroll_mv(actor,NULL,NULL,NULL);
    assert(actor->colour.f==0.0f && steps==1);
    for (unsigned bad=0;bad<13;++bad) {
        RoomScrollLives saved=*table;RoomScrollLife *r=table->rows;
        actor->colour.f=0.5f;
        if (bad==0)actor->colour.bits=0x7FC00000;
        if (bad==1)actor->colour.f=-0.1f;
        if (bad==2)actor->colour.f=1.1f;
        if (bad==3)r->flags=1;
        if (bad==4)r->sound=68;
        if (bad==5)r->maximum=1;
        if (bad==6)r->step=1;
        if (bad==7)r->on=128;
        if (bad==8)r->off=65535;
        if (bad==9)r->on=r->off;
        if (bad==10)table->count=65;
        if (bad==11)table->stride=13;
        if (bad==12)table->magic^=1;
        RoomScrollActor expected=*actor;steps=0;
        af_v3_room_scroll_mv(actor,NULL,NULL,NULL);
        assert(!steps && !memcmp(actor,&expected,sizeof(expected)));
        *table=saved;
    }
    af_v3_room_scroll_ct(NULL,NULL);af_v3_room_scroll_mv(NULL,NULL,NULL,NULL);af_v3_room_scroll_dt(NULL,NULL);
    puts("Contact/floor selectors, two source steps, null owners, bounded state, and untouched saves pass");
}
