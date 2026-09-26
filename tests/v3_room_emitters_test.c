#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_TRIGGER_SOUND
#define AF_V3_ROOM_PARTICLES
#include "../overlays/v3/room_static.c"
#include "../overlays/v3/room_materials.c"
RoomMaterialTable af_v3_test_room_materials;
void *_Matrix_to_Mtx_new(void *p) {
    RoomRigGraphics *gfx=p;gfx->tail-=64;return gfx->tail;
}

const RoomStaticTable af_v3_room_static_table={0x41464931,2,8,0,
    {{1169,3,9,0x55,0},{1225,4,0,0x44F,0}}};
RoomPrivateWallet *af_v3_test_static_private;
RoomStaticClip *af_v3_test_static_clip;
RoomEffectClip *af_test_effect_clip;
u32 af_test_effect_scene;
static unsigned loops,requests;
static RoomSoundActor *expected_actor;
static void *expected_game;
static u8 expected_sound=0x55;
static int effect_id,priority;
static s16 angle,spread;
static EffectPosition position;
void sAdo_OngenTrgStart(u32 word,float *p) { (void)word;(void)p;assert(0); }
void sAdo_OngenPos(u32 id,u8 sound,float *p) {
    assert(id==(u32)(uptr)expected_actor && sound==expected_sound && p==expected_actor->position);++loops;
}
static void request(int id,EffectPosition p,int pri,s16 facing,void *game,u16 item,s16 a,s16 b) {
    assert(game==expected_game && item==0xFFFF && !b);
    effect_id=id;position=p;priority=pri;angle=facing;spread=a;++requests;
}
int main(void) {
    RoomEffectClip effects={.request=request};af_test_effect_clip=&effects;
    _Alignas(16) u8 game[0x1EB0]={0},owner[0x1C0]={0};RoomStaticClip clip={0};
    u8 *owner_ptr=owner;memcpy(&clip,&owner_ptr,sizeof(owner_ptr));af_v3_test_static_clip=&clip;
    RoomSoundActor actor={0};actor.position[0]=17;actor.position[1]=29;actor.position[2]=43;
    expected_actor=&actor;expected_game=game;
    const unsigned frames[]={0,1,7,8,15,16,0xFFFFFFF8u,0xFFFFFFFFu};
    for(unsigned alias=0;alias<2;++alias) for(int state=0;state<16;++state)
    for(unsigned f=0;f<sizeof(frames)/sizeof(frames[0]);++f) {
        actor.index=1169+alias*1024;actor.state=state;actor.changed=0;
        *(u32 *)(game+0x1EA0)=frames[f];((RoomRigGame *)game)->frame=3;
        loops=requests=0;RoomSoundActor before=actor;
        assert(af_v3_room_static_mv(&actor,owner,(RoomRigGame *)game));
        int excluded=state==5 || state==6 || state==13 || state==15;
        assert(loops==(unsigned)!excluded && requests==(unsigned)(!excluded && !(frames[f]&7)));
        if(requests)assert(effect_id==113 && priority==1 && !angle && spread==9 &&
            position.x==17 && position.y==59 && position.z==43);
        assert(!memcmp(&actor,&before,sizeof(actor)));
    }
    const u8 pulses[]={0,1,2,255};const u16 angles[]={0,0x4000,0x8000,0xC000};
    for(unsigned alias=0;alias<2;++alias) for(int state=0;state<16;++state)
    for(int direction=0;direction<4;++direction) for(unsigned p=0;p<4;++p) {
        actor.index=1225+alias*1024;actor.state=state;actor.changed=pulses[p];
        *(int *)(owner+0x1A0)=direction;
        *(s16 *)((u8 *)&actor+0x124)=(s16)angles[p];
        loops=requests=0;RoomSoundActor before=actor;
        assert(af_v3_room_static_mv(&actor,owner,(RoomRigGame *)game));
        int excluded=state==5 || state==6 || state==13 || state==15;
        unsigned want=!excluded && pulses[p]==1 && (direction==0 || direction==2);
        assert(!loops && requests==want);
        if(want)assert(effect_id==114 && priority==2 && !spread &&
            (u16)angle==(u16)(angles[p]+(direction==2 ? 0x8000u:0)) &&
            position.x==17 && position.y==29 && position.z==43);
        assert(!memcmp(&actor,&before,sizeof(actor)));
    }
    actor.index=1225;actor.state=0;actor.changed=1;*(int *)(owner+0x1A0)=0;
    requests=0;af_v3_test_static_clip=0;
    af_v3_room_static_mv(&actor,owner,(RoomRigGame *)game);assert(!requests);
    af_v3_test_static_clip=&clip;owner_ptr=0;memcpy(&clip,&owner_ptr,sizeof(owner_ptr));
    af_v3_room_static_mv(&actor,owner,(RoomRigGame *)game);assert(!requests);
    af_test_effect_clip=0;actor.index=1169;loops=0;
    af_v3_room_static_mv(&actor,owner,(RoomRigGame *)game);assert(loops==1 && !requests);
    af_v3_room_static_mv(&actor,owner,0);assert(loops==1 && !requests);
    RoomRig material={0};RoomMaterialPlay play={0};RoomRigGraphics gfx={0};
    _Alignas(16) u8 art[256]={0},arena[512]={0};
    play.game.gfx=&gfx;material.position[0]=17;material.position[1]=29;material.position[2]=43;
    expected_actor=(RoomSoundActor *)&material;expected_game=&play.game;expected_sound=0x54;
    af_test_effect_clip=&effects;
    af_v3_test_room_materials=(RoomMaterialTable){.magic=ROOM_MATERIAL_MAGIC,.count=1,.stride=40,
        .rows={{.index=1300,.bytes=256,.mode=0,.segment=8,.frames=2,.models=3,.divisor=6,
            .frame_bytes=32,.model_offsets={64,96,128},.frame_offsets={0,32},
            .state_offset=0x54,.kind=1,.lifecycle=4}}};
    for(unsigned alias=0;alias<2;++alias) for(int state=0;state<16;++state)
    for(unsigned frame=0;frame<12;++frame) {
        material.index=1300+alias*1024;material.state=state;
        play.play_frame=frame;play.game.frame=frame+1;loops=requests=0;
        RoomRig before=material;
        af_v3_room_material_ct(&material,art);
        assert(af_v3_room_material_mv(&material,owner,&play.game,art));
        int excluded=state==5 || state==6 || state==13 || state==15;
        assert(loops==(unsigned)!excluded && requests==(unsigned)(!excluded && !(frame&3)));
        if(requests)assert(effect_id==113 && position.y==44 && spread==10);
        gfx.head=(RoomCommand *)arena;gfx.tail=arena+sizeof(arena);
        af_v3_room_material_dw(&material,alias ? 0:owner,&play.game,art);
        RoomCommand *commands=(RoomCommand *)arena;
        u32 counter=alias ? play.game.frame:play.play_frame;
        assert(gfx.head==commands+5 && gfx.tail==arena+sizeof(arena)-64);
        assert(commands[1].a==0xDB060020 && commands[1].b==
            ((u32)(uptr)(art+32*((counter*2/6)&1))&0x1FFFFFFFu));
        for(unsigned i=0;i<3;++i)assert(commands[2+i].a==0xDE000000 && commands[2+i].b==0x06000040+32*i);
        assert(!memcmp(&material,&before,sizeof(material)));
    }
    puts("shared periodic/directional emitters, native state gates, and bounds pass");
    return 0;
}
