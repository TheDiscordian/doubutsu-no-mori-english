/* Shared dispatch boundary: native prompt/transition callback is stubbed. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/console_room.c"
static Table bindings;
static u32 profiles[1024][20];
static Clip clip;
static Clip *current_clip=&clip;
static RoomRig actor;
static u32 calls,last_game;
static u8 room,game;
void *af_console_room_memory(u32 address) {
    if(address==0x804FC000)return &bindings;
    if(address==0x80136F2C)return &current_clip;
    assert(address>=AF_V3_STATIC_IMPORT_RAM && address<AF_V3_STATIC_IMPORT_RAM+sizeof(profiles));
    return (u8 *)profiles+address-AF_V3_STATIC_IMPORT_RAM;
}
static void launch(RoomRig *a,void *r,void *g,u32 number) {
    assert(a==&actor && r==&room && g==&game);calls++;last_game=number;
}
static void invoke(void) {af_v3_console_room_move(&actor,&room,&game,0);}
int main(void) {
    bindings.magic=0x41464352;bindings.count=12;bindings.stride=8;
    clip.owner=&room;clip.move=launch;
    for(u32 i=0;i<12;i++) {
        u32 index=1811+i;Row *r=&bindings.rows[i];r->index=index;r->game=i+8;r->ready=r->game!=10;
        profiles[index-1024][0]=(index<<16)|(0x2000+index*4);
        profiles[index-1024][1]=1;profiles[index-1024][18]=0x804FC7E0;
        actor.index=index;actor.changed=1;u32 before=calls;invoke();
        assert(calls==before+r->ready);if(r->ready)assert(last_game==r->game);
        actor.index=index+1024;invoke();assert(calls==before+2*r->ready);
        actor.changed=0;invoke();assert(calls==before+2*r->ready);
        actor.changed=1;profiles[index-1024][1]=0;invoke();assert(calls==before+2*r->ready);
        profiles[index-1024][1]=1;profiles[index-1024][18]=0;invoke();assert(calls==before+2*r->ready);
        profiles[index-1024][18]=0x804FC7E0;
        profiles[index-1024][0]^=1;invoke();assert(calls==before+2*r->ready);profiles[index-1024][0]^=1;
    }
    assert(calls==22);u32 before=calls;actor.index=1811;
    current_clip=0;invoke();current_clip=&clip;clip.owner=&game;invoke();clip.owner=&room;
    clip.move=0;invoke();clip.move=launch;
    bindings.magic^=1;invoke();bindings.magic^=1;
    bindings.stride=4;invoke();bindings.stride=8;
    bindings.count=20;invoke();bindings.count=12;
    bindings.reserved=1;invoke();bindings.reserved=0;
    bindings.rows[0].reserved=1;invoke();bindings.rows[0].reserved=0;
    bindings.rows[0].game=20;invoke();bindings.rows[0].game=8;
    bindings.rows[0].ready=2;invoke();bindings.rows[0].ready=1;
    actor.index=0;invoke();actor.index=1023;invoke();actor.index=3072;invoke();
    actor.index=1811;af_v3_console_room_move(0,&room,&game,0);
    af_v3_console_room_move(&actor,0,&game,0);af_v3_console_room_move(&actor,&room,0,0);
    assert(calls==before);invoke();assert(calls==before+1);
    puts("console dispatch: twelve mappings, alias indices, selection/callback guards, and QD rejection pass; native room flow stubbed");
}
