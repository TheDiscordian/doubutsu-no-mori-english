#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/holiday_sky.c"
#include "../overlays/v3/holiday_sky_draw.c"
#include "sky-source.c"
const AFSkyClock af_sky_native_rtc={0,30,19,15,1,9,2026};
const AFSkyArt af_sky_art={0x06001000,0x06002000,0x06003000,0x06003100,{64,32},{64,32},{0,1},{0,1}};
u8 *af_sky_native_debug;
void *af_sky_native_npc_clip;
AFSkyClip *af_sky_native_clip;
static AFSkyPlayer player;
static RoomEffect created;
static unsigned int rng=1;
static int requests,attentions,creates,pool=1,visible=1,title;
static int request_id,request_a,request_b,created_id;
static EffectPosition requested,translated;
static RoomCommand tile_copy[5];
static RoomRigGame *game;
static float last_scale[3];
static void near(float a,float b) {assert(fabsf(a-b)<.0002f);}
AFSkyPlayer *af_sky_player(void *g) {assert(g==game);return &player;}
int mFI_BlockKind2BkNum(int *x,int *z,u32 kind) {assert(kind==32768);*x=2;*z=3;return pool;}
int mFI_BkNum2WposXZ(float *x,float *z,int bx,int bz) {assert(bx==2&&bz==3);*x=1280;*z=1920;return 1;}
float mFI_BkNum2BaseHeight(int bx,int bz) {assert(bx==2&&bz==3);return 120;}
int af_sky_title_demo(void) {return title;}
float af_effect_random(void) {rng=rng*1664525u+1013904223u;return (rng>>8)*(1.0f/16777216.0f);}
float sin_s(s16 n) {return sinf(n*(6.28318530718f/65536.0f));}
float cos_s(s16 n) {return cosf(n*(6.28318530718f/65536.0f));}
static void continuous(RoomEffect *e,s16 unused,s16 timer) {
    (void)unused;if(e->state<2 && e->timer<=1){e->state=1;e->timer=timer;}
}
static float adjust(s16 n,s16 start,s16 end,float a,float b) {
    if(start==end || n<=start)return a;
    if(n>=end)return b;
    return a+(n-start)*((b-a)/(end-start));
}
static int lookat(EffectPosition p) {(void)p;return visible;}
static void attention(int kind,void *a,EffectPosition *p) {
    assert(kind==2&&!a&&p);assert(p->y==340);++attentions;
}
static void request(int id,EffectPosition p,int priority,s16 angle,void *g,u16 name,s16 a,s16 b) {
    assert(priority==2&&g==game&&name==0xFFFF);(void)angle;
    ++requests;request_id=id;requested=p;request_a=a;request_b=b;
}
static RoomEffect *create(s16 id,EffectPosition p,EffectPosition *offset,void *g,void *arg,
        u16 name,int priority,s16 a,s16 b) {
    assert(!offset&&!arg&&g==game&&name==0xFFFF&&priority==2);++creates;created_id=id;
    created=(RoomEffect){.position=p,.priority=priority,.item=name,.arg0=a,.arg1=b};return &created;
}
void Matrix_translate(float x,float y,float z,u8 mode) {assert(!mode);translated=(EffectPosition){x,y,z};}
void Matrix_scale(float x,float y,float z,u8 mode) {assert(mode==1);last_scale[0]=x;last_scale[1]=y;last_scale[2]=z;}
void Matrix_RotateY(s16 angle,int mode) {(void)angle;assert(mode==1);}
void Matrix_RotateZ(s16 angle,int mode) {(void)angle;assert(mode==1);}
void Matrix_mult(float *p,int mode) {assert(p==(float *)((u8 *)game+0x1E5C)&&mode==1);}
void *_Matrix_to_Mtx(void *p) {assert(!((uptr)p&15));memset(p,0x42,64);return p;}
void osWritebackDCache(void *p,int bytes) {
    assert(bytes==40||bytes==64);if(bytes==40)memcpy(tile_copy,p,40);
}
void _texture_z_light_fog_prim_xlu(void *p) {
    RoomRigGraphics *g=p;*g->xlu_head++=(RoomCommand){0xDE000000,0x8010CB90};
}
void *Lib_SegmentedToVirtual(void *p) {return (void *)((uptr)p+0x80000000u);}
static void pair(RoomEffect *e,void (*native)(RoomEffect *,void *),void (*source)(RoomEffect *,void *)) {
    RoomEffect reference=*e;unsigned int seed=rng;
    requests=attentions=0;native(e,game);--e->timer;if(e->timer<0)e->timer=0;
    int count=requests,looks=attentions,id=request_id,a=request_a,b=request_b;
    EffectPosition p=requested;unsigned int after=rng;
    rng=seed;requests=attentions=0;source(&reference,game);--reference.timer;
    if(reference.timer>0){source(&reference,game);--reference.timer;}
    if(reference.timer<0)reference.timer=0;
    assert(!memcmp(e,&reference,sizeof(*e))&&rng==after&&count==requests&&looks==attentions);
    if(count)assert(id==request_id&&a==request_a&&b==request_b&&!memcmp(&p,&requested,sizeof(p)));
}
int main(void) {
    _Alignas(16) u8 game_data[0x1EB0]={0},arena[512],debug[0x1C94]={0},npc[64]={0};
    RoomRigGraphics gfx={0};game=(RoomRigGame *)game_data;game->gfx=&gfx;
    AFSkyClip clip={.request=request,.continuous=continuous,.adjust=adjust,.create=create,.lookat=lookat};
    af_sky_native_clip=&clip;af_sky_native_debug=debug;af_sky_native_npc_clip=npc;
    *(void (**)(int,void *,EffectPosition *))(npc+0x18)=attention;
    player.actor_class.world.position=(EffectPosition){1500,120,2100};
    assert(af_sky_identity(65)==115&&af_sky_identity(116)==116&&af_sky_identity(115)==117&&af_sky_identity(117)==118);
    assert(af_sky_identity(0)==-1&&af_sky_seconds()==70200);
    void (*init[4])(xyz_t,int,s16,void *,u16,s16,s16)={af_sky_moon_init,af_sky_set_init,af_sky_shooting_init,af_sky_kira_init};
    void (*ctor[4])(RoomEffect *,void *,void *)={af_sky_moon_ct,af_sky_set_ct,af_sky_shooting_ct,af_sky_kira_ct};
    void (*moves[4])(RoomEffect *,void *)={af_sky_moon_mv,af_sky_set_mv,af_sky_shooting_mv,af_sky_kira_mv};
    void (*originals[4])(RoomEffect *,void *)={eNight13Moon_mv,eShootingSet_mv,eShooting_mv,eShootingKira_mv};
    for(int kind=0;kind<4;kind++) {
        init[kind]((xyz_t){1600,140,2240},2,0x4000,game,0xFFFF,80,0);
        assert(created_id==115+kind);RoomEffect e=created;ctor[kind](&e,game,0);
        if(!kind){near(e.position.x,1600);near(e.position.y,139);near(e.position.z,2240);assert(e.timer==20000);}
        if(kind==2)assert(e.timer==320&&e.specific[0]>=70&&e.specific[0]<100);
        if(kind==3)assert(e.timer==42&&e.acceleration.x==1508&&e.velocity.x==1692);
        for(int frame=0;frame<450&&e.timer;frame++)pair(&e,moves[kind],originals[kind]);
        if(kind>=2)assert(e.timer==0);
    }
    assert(creates==4);
    RoomEffect e={.timer=100,.position={1600,140,2240},.priority=2,.item=0xFFFF};
    e.specific[1]=120;title=-9;
    for(int i=0;i<70;i++)pair(&e,af_sky_set_mv,eShootingSet_mv);
    assert(e.specific[0]==0&&!requests&&!attentions);title=0;
    visible=0;for(int i=0;i<70;i++)pair(&e,af_sky_set_mv,eShootingSet_mv);
    assert(!requests&&!attentions);visible=1;
    pool=0;af_sky_moon_ct(&e,game,0);assert(!e.timer&&!e.specific[3]);
    pool=1;pair(&e,af_sky_moon_mv,eNight13Moon_mv);assert(e.specific[3]==1&&e.timer>100);
    e.state=2;e.timer=80;for(int i=0;i<40;i++)pair(&e,af_sky_moon_mv,eNight13Moon_mv);assert(e.timer==0);
    void (*draw[3])(RoomEffect *,void *)={af_sky_moon_draw,af_sky_shooting_draw,af_sky_kira_draw};
    for(int kind=0;kind<3;kind++) {
        e=(RoomEffect){.position={1600,140,2240},.scale={.01f,.01f,.01f},.timer=kind==1?318:20};
        e.specific[0]=80;*(u32 *)(game_data+0x1EA0)=17;
        memset(arena,0xA5,sizeof(arena));gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+496;
        draw[kind](&e,game);assert((u8 *)gfx.xlu_head==arena+16+(kind==1?4:5)*8);
        for(int i=0;i<16;i++)assert(arena[i]==0xA5&&arena[496+i]==0xA5);
        assert(((RoomCommand *)(arena+16))[kind==1?3:4].b==0x06001000u+(u32)kind*0x1000u);
        if(kind==0){assert(tile_copy[1].a==0xF2000000);assert(tile_copy[3].a==0xF2011011);near(last_scale[0],.049f);}
        if(kind==1){assert(tile_copy[1].a==0xF2000162);assert(tile_copy[1].b==(28u<<12|((354+1020)&4095)));}
        RoomEffect before=e;memset(arena,0xA5,sizeof(arena));gfx.xlu_head=(RoomCommand *)(arena+16);gfx.xlu_tail=arena+24;
        draw[kind](&e,game);assert((u8 *)gfx.xlu_head==arena+16&&gfx.xlu_tail==arena+24);
        assert(!memcmp(&e,&before,sizeof(e)));for(unsigned int i=0;i<sizeof(arena);i++)assert(arena[i]==0xA5);
    }
    clip.create=0;assert(!af_sky_ready(game));af_sky_moon_ct(&e,game,0);assert(e.timer==0);
    puts("complete sky source lifecycles, native services, timing, and drawing bounds pass");
}
