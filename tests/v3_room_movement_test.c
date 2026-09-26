#define AF_V3_ROOM_SCROLL_LIFECYCLE 1
#define AF_V3_ROOM_CONTACT 1
#define AF_V3_ROOM_MOVEMENT 1
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_scroll.c"

RoomScrollTable af_v3_test_room_scroll;
RoomScrollLives af_v3_test_room_scroll_lives;
RoomMoveTable af_v3_test_room_moves;
RoomContactClip *af_v3_test_contact_clip;
signed char af_v3_test_contact_floor;
u8 *af_v3_room_debug;
static unsigned calls,kind,id;
static float *where;
void *_Matrix_to_Mtx(void *p) { return p; }
void osWritebackDCache(void *p,int n) { (void)p;(void)n; }
float add_calc(float *p,float a,float b,float c,float d) { (void)p;(void)a;(void)b;(void)c;(void)d;assert(0);return 0; }
void sAdo_OngenPos(u32 h,u8 s,float *p) { (void)h;(void)s;(void)p;assert(0); }
void sAdo_OngenTrgStart(u32 s,float *p) { ++calls;kind=1;id=s;where=p; }
void sAdo_FloorTrgStart(u8 s,float *p) { ++calls;kind=2;id=s;where=p; }
static unsigned read16(FILE *f) { int a=fgetc(f),b=fgetc(f);assert(a>=0 && b>=0);return (unsigned)a*256u+(unsigned)b; }

int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    unsigned header[4];for (unsigned i=0;i<4;++i) { unsigned high=read16(f);header[i]=(high<<16)|read16(f); }
    RoomMoveTable *table=&af_v3_test_room_moves;
    assert(header[0]==ROOM_MOVE_MAGIC && header[1]==2 && header[2]==12 && !header[3]);
    *table=(RoomMoveTable){.magic=header[0],.count=header[1],.stride=header[2]};
    for (unsigned i=0;i<2;++i) {
        RoomMoveRecord *r=table->rows+i;
        r->index=read16(f);r->mode=read16(f);r->sound_a=read16(f);r->sound_b=read16(f);
        r->floor_a=read16(f);r->floor_b=read16(f);
        assert(r->mode==i+1);
    }
    assert(fgetc(f)==EOF);fclose(f);
    RoomContactOwner owner={0};RoomContactClip clip={&owner};
    struct { u8 before[16];RoomScrollActor actor;u8 after[16]; } guarded;
    memset(&guarded,0xA7,sizeof(guarded));RoomScrollActor *actor=&guarded.actor;
    for (unsigned record=0;record<3;++record) for (unsigned alias=0;alias<2;++alias)
        for (int floor=-1;floor<79;++floor) for (int state=0;state<17;++state)
            for (int direction=0;direction<4;++direction) for (unsigned connected=0;connected<3;++connected) {
                RoomMoveRecord *r=table->rows+(record<2 ? record : 0);
                actor->index=record<2 ? r->index+1024*alias : 37;
                actor->state=state;owner.direction=direction;
                af_v3_test_contact_floor=floor;af_v3_test_contact_clip=connected ? &clip : NULL;
                clip.owner=connected==2 ? &owner : NULL;
                RoomScrollActor original=*actor;
                unsigned want=2,sound=26;
                if (record==0) {
                    want=connected==2 && (state==1 || state==2 || state==9 || state==10 || state==11 || state==12 || state==14);
                    sound=direction==1 || direction==3 ? r->sound_a : r->sound_b;
                } else if (record==1 && (floor==r->floor_a || floor==r->floor_b)) {
                    want=connected==2 && (state==1 || state==9 || state==11 || state==14) && !direction;sound=r->sound_a;
                }
                calls=0;af_v3_room_scroll_move_sound(26,actor->position);
                assert(calls==(want ? 1u : 0u));
                if (want)assert(kind==want && id==sound && where==actor->position);
                assert(!memcmp(&original,actor,sizeof(original)));
            }
    for (unsigned i=0;i<16;++i)assert(guarded.before[i]==0xA7 && guarded.after[i]==0xA7);
    calls=0;af_v3_room_scroll_move_sound(26,NULL);assert(!calls);
    table->count=9;calls=0;af_v3_room_scroll_move_sound(27,actor->position);
    assert(calls==1 && kind==2 && id==27);
    puts("Complete installed movement records, source conditions, aliases, null owners, and unchanged actors pass");
}
