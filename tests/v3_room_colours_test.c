#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_colours.c"
#define AF_V3_ROOM_COLOURS
#include "../overlays/v3/room_materials.c"
RoomColourState af_v3_test_room_colour;
RoomMaterialTable af_v3_test_room_materials;
static union { uptr align;u8 bytes[0x2000]; } game_storage,player_storage,owner_storage;
static union { uptr align;u8 bytes[0x11000]; } overlay_storage;
static void *player=player_storage.bytes;
static unsigned sounds,updates,draws,fogs;
static RoomRig *sound_actor;
static int colours[2][6],allocate_tail,consume_commands;
static void *draw_args[6];
u8 *af_reaction_player(void *game) { assert(game==game_storage.bytes);return player; }
void sAdo_OngenPos(u32 id,u8 sound,float *position) {
    assert(id==(u32)(uptr)sound_actor && sound==95 && position==sound_actor->position);++sounds;
}
void *_Matrix_to_Mtx_new(void *gfx) { (void)gfx;assert(0);return 0; }
static void original(void *actor,RoomRigGame *game) {
    assert(actor==player && (void *)game==game_storage.bytes);++updates;
}
RoomCommand *gfx_set_fog_nosync(RoomCommand *commands,int r,int g,int b,int a,int near,int far) {
    assert(fogs<2);int row[6]={r,g,b,a,near,far};memcpy(colours[fogs++],row,sizeof(row));
    commands[0]=(RoomCommand){0xF8000000u,(u32)r<<24|(u32)g<<16|(u32)b<<8|(u32)a};
    commands[1]=(RoomCommand){0xDB000008u,(u32)near<<16|(u16)far};return commands+2;
}
void cKF_Si3_draw_R_SV(void *game,RoomKeyframe *key,void *matrix,void *before,void *after,void *actor) {
    void *args[]={game,key,matrix,before,after,actor};
    assert(!memcmp(args,draw_args,sizeof(args)));++draws;
    RoomRigGraphics *gfx=((RoomRigGame *)game)->gfx;
    if(allocate_tail) { gfx->tail-=64;memset(gfx->tail,0xC7,64); }
    if(consume_commands) { assert((u8 *)(gfx->head+1)<=gfx->tail);*gfx->head++=(RoomCommand){1,2}; }
}
/* Extracted unchanged from the donor update routine by the Python driver. */
typedef struct { int change_color_request,change_color_flag;float change_color_timer; } PLAYER_ACTOR;
typedef PLAYER_ACTOR ACTOR;
#define TRUE 1
#define FALSE 0
#include "donor_colour_update.inc"
int main(void) {
    RoomRigGame *game=(RoomRigGame *)game_storage.bytes;
    RoomRig actors[4],copy;memset(actors,0xA5,sizeof(actors));
    af_v3_test_room_materials=(RoomMaterialTable){.magic=ROOM_MATERIAL_MAGIC,.count=1,.stride=40,
        .rows={{.index=1805,.bytes=128,.mode=1,.segment=8,.frames=4,.models=1,
                .frame_bytes=32,.frame_offsets={0,32,64,96},.divisor=10,.state_offset=95,.lifecycle=3}}};
    u8 data[128]={0},used[4]={1,1,1,0};
    for(int i=0;i<4;++i) { actors[i].index=1805;actors[i].changed=0;actors[i].state=0;((u8 *)&actors[i])[0x12C]=1; }
    actors[2].index=1806;copy=actors[0];sound_actor=actors;
    af_v3_room_material_ct(actors,data);((u8 *)&copy)[0x12C]=0;
    assert(!memcmp(actors,&copy,sizeof(copy)));
    RoomColourOverlay overlay={.vrom_start=0x82D7F0,.vram_start=0x80936710,.vram_end=0x80950000,
                               .loaded=overlay_storage.bytes};
    RoomColourOverlay *p=&overlay;memcpy(owner_storage.bytes+0x170,&p,sizeof(p));
    RoomColourInstances work={actors,used,4};memcpy(overlay_storage.bytes+0x10E50,&work,sizeof(work));
    assert(af_v3_room_material_mv(actors,owner_storage.bytes,game,data));assert(!sounds);
    ((u8 *)actors)[0x12C]=1;actors[0].changed=1;
    assert(af_v3_room_material_mv(actors,owner_storage.bytes,game,data));
    assert(sounds==1 && ((u8 *)actors)[0x12C]==1 && !((u8 *)&actors[1])[0x12C]);
    assert(actors[1].changed && ((u8 *)&actors[2])[0x12C] && ((u8 *)&actors[3])[0x12C]);
    assert(!actors[2].changed && !actors[3].changed);
    af_v3_test_room_colour.request=0;
    int excluded[]={5,6,13,15};
    for(unsigned i=0;i<4;++i) { actors[0].state=excluded[i];af_v3_room_colour_mv(actors,owner_storage.bytes,game,95); }
    actors[0].state=0;af_v3_room_colour_mv(actors,0,game,95);
    assert(sounds==1 && !af_v3_test_room_colour.request);
    actors[0].changed=0;PLAYER_ACTOR donor={0};
    for(int frame=0;frame<240;++frame) {
        int on=(frame<115 || frame>=120);((u8 *)actors)[0x12C]=(u8)on;
        af_v3_room_colour_mv(actors,owner_storage.bytes,game,95);
        af_v3_room_colour_update(player,game,original);
        for(int tick=0;tick<2;++tick) { donor.change_color_request=on;Player_actor_Check_player_change_color_for_main(&donor); }
        assert(af_v3_test_room_colour.active==(u32)donor.change_color_flag);
        assert(af_v3_test_room_colour.timer==donor.change_color_timer && !af_v3_test_room_colour.request);
    }
    assert(updates==240);
    player=player_storage.bytes+0x800;
    af_v3_room_colour_update(player,game,original);assert(!af_v3_test_room_colour.active);
    af_v3_room_colour_mv(actors,owner_storage.bytes,game,95);
    af_v3_room_colour_update(player,game,original);assert(af_v3_test_room_colour.timer==1);
    player=player_storage.bytes;af_v3_test_room_colour.player=player;
    RoomCommand commands[32];RoomRigGraphics gfx={0};game->gfx=&gfx;
    float eye[]={0,0,0},centre[]={0,0,352},position[]={0,0,176};
    memcpy(game_storage.bytes+0x1960,eye,12);memcpy(game_storage.bytes+0x196C,centre,12);
    memcpy(player_storage.bytes+0x28,position,12);
    u8 *light=game_storage.bytes+0x1C60;light[7]=3;light[8]=4;light[9]=5;
    *(s16 *)(light+10)=900;*(s16 *)(light+12)=1000;
    draw_args[0]=game;draw_args[1]=&actors[0].keyframe;draw_args[2]=data;
    draw_args[3]=actors;draw_args[4]=&actors[1];draw_args[5]=player;
    const int rgb[][3]={{255,100,255},{255,255,255},{100,100,100},{100,255,255}};
    const int restore[]={3,4,5,0,900,1000};
    for(int phase=0;phase<8;++phase) {
        fogs=0;gfx.head=commands;gfx.tail=(u8 *)(commands+32);allocate_tail=1;consume_commands=1;
        af_v3_test_room_colour.timer=phase*10.0f;
        af_v3_room_colour_draw(game,draw_args[1],draw_args[2],draw_args[3],draw_args[4],player);
        assert(fogs==2 && !memcmp(colours[1],restore,sizeof(restore)) && gfx.head==commands+5);
        assert(gfx.tail==(u8 *)(commands+24));
        for(int i=0;i<64;++i) assert(gfx.tail[i]==0xC7);
        if(phase&1) assert(colours[0][4]==1 && colours[0][5]==1);
        else { assert(!memcmp(colours[0],rgb[phase/2],sizeof(rgb[0])));assert(colours[0][4]==210 && colours[0][5]==996); }
    }
    /* Zero view length disables fog; absent requests leave native draw intact. */
    memcpy(game_storage.bytes+0x196C,eye,12);fogs=0;allocate_tail=0;consume_commands=0;
    gfx.head=commands;gfx.tail=(u8 *)(commands+32);af_v3_test_room_colour.timer=0;
    af_v3_room_colour_draw(game,draw_args[1],draw_args[2],draw_args[3],draw_args[4],player);
    assert(colours[0][4]==1 && colours[0][5]==1);
    fogs=0;af_v3_test_room_colour.active=0;gfx.head=commands;
    af_v3_room_colour_draw(game,draw_args[1],draw_args[2],draw_args[3],draw_args[4],player);
    assert(!fogs && gfx.head==commands);
    /* A skeleton consuming the last space disables the initial tint in place. */
    fogs=0;af_v3_test_room_colour.active=1;consume_commands=1;
    gfx.head=commands;gfx.tail=(u8 *)(commands+4);commands[4]=(RoomCommand){0xA5,0x5A};
    af_v3_room_colour_draw(game,draw_args[1],draw_args[2],draw_args[3],draw_args[4],player);
    assert(fogs==2 && gfx.head==commands+3 && commands[0].b==0x03040500);
    assert(commands[4].a==0xA5 && commands[4].b==0x5A);
    fogs=0;consume_commands=0;gfx.head=commands;gfx.tail=(u8 *)(commands+3);
    af_v3_room_colour_draw(game,draw_args[1],draw_args[2],draw_args[3],draw_args[4],player);
    assert(!fogs && gfx.head==commands && draws==12);
    puts("480 donor ticks; shared material dispatch, exclusive switches, native callback arguments, fog restoration, and bounds pass");
    return 0;
}
