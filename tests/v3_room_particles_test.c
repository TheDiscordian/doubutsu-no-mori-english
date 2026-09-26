#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_EFFECT_STEAM_TEXTURES 0x06017000u
#define AF_EFFECT_STEAM_MODEL 0x06017240u
#define AF_EFFECT_STEAM_STEW 0x06017308u
#define AF_EFFECT_PROJECTILE_MODEL 0x06018000u
#define AF_EFFECT_PROJECTILE_SOUND 0x17Fu
#include "../overlays/v3/room_particles.c"

RoomEffectClip *af_test_effect_clip;
u32 af_test_effect_scene;
u8 *af_v3_room_debug;
static int creates,sounds,matrices,flushed;
static s16 created_id,created_a,created_b,expected_angle;
static u32 random_angle;
static float translated[3],scaled[3];
static RoomRigGame *expected_game;
static RoomEffect result;
u32 qrand(void) { return random_angle; }
float sin_s(s16 n) {
    if ((u16)n==0x4000) return 1;
    if ((u16)n==0xC000) return -1;
    return 0;
}
float cos_s(s16 n) {
    if (!n) return 1;
    if ((u16)n==0x8000) return -1;
    return 0;
}
void sAdo_OngenTrgStart(u32 sound,float *pos) {
    assert(sound==AF_EFFECT_PROJECTILE_SOUND && pos);++sounds;
}
static RoomEffect *create(s16 id,EffectPosition p,EffectPosition *offset,void *game,void *arg,
                          u16 item,int priority,s16 a,s16 b) {
    assert(p.x==1 && p.y==2 && p.z==3 && !offset && !arg);
    assert(game==expected_game && item==0xFFFF && priority==2);
    created_id=id;created_a=a;created_b=b;++creates;return &result;
}
static float adjust(s16 now,s16 start,s16 end,float a,float b) {
    if (now<=start)return a;
    if (now>=end)return b;
    return a+(float)(now-start)*((b-a)/(float)(end-start));
}
void Matrix_translate(float x,float y,float z,u8 mode) {
    assert(!mode);translated[0]=x;translated[1]=y;translated[2]=z;
}
void Matrix_mult(float *m,int mode) {
    assert(m==(float *)((u8 *)expected_game+0x1E5C) && mode==1);
}
void Matrix_scale(float x,float y,float z,u8 mode) {
    assert(mode==1);scaled[0]=x;scaled[1]=y;scaled[2]=z;
}
void Matrix_RotateY(s16 angle,int mode) { assert(angle==expected_angle && mode==1); }
void *_Matrix_to_Mtx(void *p) { assert(!((uptr)p&15));memset(p,0x42,64);++matrices;return p; }
void osWritebackDCache(void *p,int n) { assert(!((uptr)p&15) && n==64);++flushed; }
void *Lib_SegmentedToVirtual(void *p) { return (void *)((uptr)p+0x80000000u); }
void _texture_z_light_fog_prim_xlu(void *p) {
    RoomRigGraphics *g=p;*g->xlu_head++=(RoomCommand){0xDE000000,0x8010CB90};
}
void _texture_z_light_fog_prim(void *p) {
    RoomRigGraphics *g=p;*g->head++=(RoomCommand){0xDE000000,0x8010CAE0};
}
static void close_float(float a,float b) { assert(absolute(a-b)<0.00002f); }
static void steam_tick(RoomEffect *e,float drag) {
    e->velocity.x+=e->acceleration.x;e->velocity.y+=e->acceleration.y;e->velocity.z+=e->acceleration.z;
    e->position.x+=e->velocity.x;e->position.y+=e->velocity.y;e->position.z+=e->velocity.z;
    e->velocity.y*=drag;--e->timer;
}
static void projectile_tick(RoomEffect *e) {
    e->position.x+=e->velocity.x;e->position.y+=e->velocity.y;e->position.z+=e->velocity.z;
    if (e->position.x<e->offset.x || e->position.x>e->offset.y ||
            e->position.z<e->offset.z || e->position.z>e->scale.x) {
        e->timer=0;e->scale.z=0;return;
    }
    float dist=1000;
    if (absolute(e->position.x-e->offset.x)<16) dist=absolute(e->position.x-e->offset.x);
    else if (absolute(e->position.z-e->offset.z)<16)dist=absolute(e->position.z-e->offset.z);
    else if (absolute(e->position.x-e->offset.y)<16)dist=absolute(e->position.x-e->offset.y);
    else if (absolute(e->position.z-e->scale.x)<16)dist=absolute(e->position.z-e->scale.x);
    if (dist<20) {
        e->scale.z=dist/16;
        if (!e->specific[0]) { e->velocity.x*=0.5f;e->velocity.z*=0.5f;e->specific[0]=1; }
    } else e->scale.z=1;
    --e->timer;
}

int main(void) {
    RoomEffectClip clip={.create=create,.adjust=adjust};af_test_effect_clip=&clip;
    _Alignas(16) u8 game_mem[0x1EA0]={0};expected_game=(RoomRigGame *)game_mem;
    RoomRigGraphics gfx={0};expected_game->gfx=&gfx;
    af_v3_steam_init((EffectPosition){1,2,3},2,123,expected_game,0xFFFF,9,7);
    assert(creates==1 && created_id==113 && created_a==9 && created_b==7);
    af_v3_projectile_init((EffectPosition){1,2,3},2,123,expected_game,0xFFFF,9,7);
    assert(creates==2 && created_id==114 && created_a==123 && created_b==7);
    _Alignas(16) u8 arena[320],debug[0x1C94]={0};
    af_v3_room_debug=debug;s16 *registers=(s16 *)(debug+0x14+36*96*2);
    static const u8 pairs[22][2]={
        {0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,1},{0,1},{0,1},{1,1},{1,2},
        {1,2},{1,2},{2,2},{2,3},{2,3},{2,3},{3,3},{3,3},{3,3},{3,3},{3,3}};
    static const u8 fractions[22]={0,0,0,0,0,0,64,128,192,0,64,128,192,0,64,128,192,0,0,0,0,0};
    for (int custom=0;custom<2;++custom) for (int variant=0;variant<2;++variant) {
        registers[0x32]=custom*2;registers[0x34]=custom*3;
        registers[0x35]=custom*4;registers[0x36]=custom*5;
        registers[0x37]=custom*6;registers[0x38]=custom*7;registers[0x39]=custom*8;
        random_angle=0x4000;
        struct { u32 guard1[4];RoomEffect e;u32 guard2[4]; } guarded;
        memset(&guarded,0xA5,sizeof(guarded));memset(&guarded.e,0,sizeof(guarded.e));
        RoomEffect *e=&guarded.e;e->position=(EffectPosition){100,20,100};e->arg0=9;e->arg1=variant;
        af_v3_steam_ct(e,expected_game,0);
        assert(e->timer==44 && e->position.x==109 && e->position.y==21+custom*3 && e->position.z==100);
        RoomEffect reference=*e;
        for (int frame=0;frame<22;++frame) {
            memset(arena,0xA5,sizeof(arena));gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+304;
            af_v3_steam_dw(e,expected_game);
            assert((u8 *)gfx.xlu_head==arena+64);
            RoomCommand *commands=(RoomCommand *)(arena+16);
            assert(commands[2].a==0xDB060020 && commands[3].a==0xDB060024);
            for (int i=0;i<2;++i)assert(commands[i+2].b==0x86017000u+128u*pairs[frame][i]);
            assert(commands[4].a==(0xFA000000u|fractions[frame]));
            assert(commands[5].b==(variant ? AF_EFFECT_STEAM_STEW:AF_EFFECT_STEAM_MODEL));
            float scale=adjust(frame*2,0,44,variant ? .001f:.001f+custom*.0006f,
                                                   variant ? .01f:.005f+custom*.0007f);
            close_float(scaled[0],scale);close_float(scaled[1],scale);close_float(scaled[2],scale);
            int alpha=(int)adjust(frame*2,0,44,(variant ? 190:130)+custom*4,10+custom*5);
            assert(commands[4].b==((variant ? 0xFFC88200u:0xFFFFFF00u)|(u32)alpha));
            for(int i=0;i<16;++i)assert(arena[i]==0xA5 && arena[304+i]==0xA5);
            af_v3_steam_mv(e,expected_game);--e->timer;
            steam_tick(&reference,.95f+custom*.008f);steam_tick(&reference,.95f+custom*.008f);
            assert(e->timer==reference.timer);close_float(e->position.y,reference.position.y);
            close_float(e->velocity.y,reference.velocity.y);
        }
        for(int i=0;i<4;++i)assert(guarded.guard1[i]==0xA5A5A5A5 && guarded.guard2[i]==0xA5A5A5A5);
        int count=matrices;af_v3_steam_dw(e,expected_game);assert(matrices==count);
    }
    /* Every native room and firing orientation, complete motion to a wall or
       the source time limit, compared with two independent donor steps. */
    const u32 scenes[]={6,20,21,22};const int widths[]={6,4,6,8};
    for (int scene=0;scene<4;++scene) for(int direction=0;direction<4;++direction) {
        af_test_effect_scene=scenes[scene];RoomEffect e={.position={120,40,200},.arg0=(s16)(direction*0x4000)};
        int before=sounds;af_v3_projectile_ct(&e,expected_game,0);
        assert(sounds==before+1 && e.timer==360 && e.offset.y==40+40*widths[scene] && e.scale.x==200+40*widths[scene]);
        RoomEffect reference=e;int frames=0;
        while(e.timer>0) {
            for(int step=0;step<2 && reference.timer>0;++step)projectile_tick(&reference);
            af_v3_projectile_mv(&e,expected_game);if(e.timer>0)--e.timer;
            assert(e.timer==reference.timer && e.specific[0]==reference.specific[0]);
            close_float(e.position.x,reference.position.x);close_float(e.position.z,reference.position.z);
            close_float(e.velocity.x,reference.velocity.x);close_float(e.velocity.z,reference.velocity.z);
            close_float(e.scale.z,reference.scale.z);assert(++frames<=180);
        }
        assert(e.specific[0]==1);
        expected_angle=e.arg0;memset(arena,0xA5,sizeof(arena));gfx.head=(RoomCommand *)(arena+16);gfx.tail=arena+304;
        af_v3_projectile_dw(&e,expected_game);
        assert((u8 *)gfx.head==arena+40 && ((RoomCommand *)(arena+16))[2].b==AF_EFFECT_PROJECTILE_MODEL);
        close_float(scaled[0],.01f);close_float(scaled[2],e.scale.z*.01f);
        for(int i=0;i<16;++i)assert(arena[i]==0xA5 && arena[304+i]==0xA5);
        /* Near-wall creation is suppressed in the actual firing direction. */
        e=(RoomEffect){.position={120,40,200},.arg0=expected_angle};
        if(!direction)e.position.z=200+40*widths[scene]-21;
        if(direction==1)e.position.x=40+40*widths[scene]-21;
        if(direction==2)e.position.z=61;
        if(direction==3)e.position.x=61;
        before=sounds;af_v3_projectile_ct(&e,expected_game,0);assert(e.timer==0 && sounds==before);
    }
    RoomEffect e={.position={120,40,200},.arg0=0x1000};int count=sounds;
    af_v3_projectile_ct(&e,expected_game,0);assert(e.timer==360 && sounds==count);
    assert(near_angle(15,0) && !near_angle(16,0) && !near_angle(65535,0));
    e.timer=44;count=matrices;gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+112;
    af_v3_steam_dw(&e,expected_game);assert(matrices==count);
    gfx.head=(RoomCommand *)(arena+16);gfx.tail=arena+96;
    af_v3_projectile_dw(&e,expected_game);assert(matrices==count && matrices==flushed);
    af_test_effect_clip=0;
    af_v3_steam_init((EffectPosition){1,2,3},2,0,expected_game,0xFFFF,9,0);assert(creates==2);
    puts("complete steam/projectile physics, frame blending, drawing, and bounds pass");
    return 0;
}
