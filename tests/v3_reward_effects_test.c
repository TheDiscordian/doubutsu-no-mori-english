/* Whole source-family timing, native light lifetime, and draw-arena checks. */
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "reward_effects.h"
#include "source.c"
#include "../overlays/v3/reward_effects.c"
#include "../overlays/v3/reward_effects_draw.c"
volatile const u8 af_hp_native_ticks=2;
static int visible,requests[3],kills,sounds,added,removed,reflections,available=1;
static int failed_light;
const u16 af_rw_effect_sounds[2]={0x400,0x401};
const u32 af_rw_effect_models[3]={0x6000100,0x6000200,0x6000300},af_rw_effect_kira_mode=0x6000400;
static RoomEffect created;
static RewardLightNode native_node;
static void *context;
int *af_rw_hem_visible(void){return &visible;}
int af_sky_ready(void *g){return g && available;}
float af_effect_random(void){return .9f;}
float sin_s(s16 a){return sinf(a*(6.28318530718f/65536));}
float cos_s(s16 a){return cosf(a*(6.28318530718f/65536));}
float af_sky_adjust(s16 n,s16 a,s16 b,float x,float y){
    if(n<=a)return x;if(n>=b)return y;return x+(y-x)*(n-a)/(b-a);
}
void af_sky_continuous(RoomEffect *e,s16 a,s16 b){(void)a;(void)b;(void)e;}
s16 af_sky_debug(unsigned int i){(void)i;return 0;}
void xyz_t_add(xyz_t *a,xyz_t *b,xyz_t *c){*c=(xyz_t){a->x+b->x,a->y+b->y,a->z+b->z};}
void add_calc(float *v,float target,float rate,float maximum,float minimum){
    float d=(target-*v)*rate;if(d>maximum)d=maximum;if(d<minimum)d=minimum;*v+=d;
}
float mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t p,float f){(void)p;(void)f;return 0;}
static void request(int id,xyz_t p,int prio,s16 angle,void *g,u16 name,s16 a,s16 b){
    (void)p;(void)prio;(void)angle;(void)g;(void)name;(void)a;(void)b;
    assert(id>=122 && id<=124);++requests[id-122];
}
static RoomEffect *create(s16 id,xyz_t p,xyz_t *offset,void *g,void *arg,u16 name,int prio,s16 a,s16 b){
    (void)offset;(void)g;(void)arg;(void)name;(void)prio;(void)b;
    assert(id>=122 && id<=124);created=(RoomEffect){.position=p,.arg0=a};return &created;
}
static void kill(int id,u16 name){assert(id==124 && name==65535);++kills;}
static AFSkyClip clip={.request=request,.kill=(void *)kill,.create=create};
AFSkyClip *af_sky_native_clip=&clip;
void af_hp_native_sound(u32 word,xyz_t *p){assert(p && (word==0x400 || word==0x401));++sounds;}
void Light_point_ct(RewardLight *l,s16 x,s16 y,s16 z,u8 r,u8 g,u8 b,s16 power){
    l->type=0;l->point.x=x;l->point.y=y;l->point.z=z;l->point.radius=power;
    l->point.colour[0]=r;l->point.colour[1]=g;l->point.colour[2]=b;
}
RewardLightNode *Global_light_list_new(void *g,RewardGlobalLight *list,RewardLight *l){
    assert(list==(RewardGlobalLight *)((u8 *)g+0x1C60));if(failed_light)return 0;
    native_node=(RewardLightNode){.info=l,.next=list->list};list->list=&native_node;++added;return &native_node;
}
void Global_light_list_delete(RewardGlobalLight *list,RewardLightNode *n){
    assert(list==(RewardGlobalLight *)((u8 *)context+0x1C60));assert(n==&native_node);
    list->list=n->next;++removed;
}
void Matrix_translate(float x,float y,float z,u8 mode){(void)x;(void)y;(void)z;(void)mode;}
void Matrix_scale(float x,float y,float z,u8 mode){(void)x;(void)y;(void)z;(void)mode;}
void Matrix_mult(float *m,int mode){(void)m;(void)mode;}
void *_Matrix_to_Mtx(void *m){memset(m,0,64);return m;}
void osWritebackDCache(void *p,int n){(void)p;(void)n;}
void _texture_z_light_fog_prim(void *g){(void)g;}
void _texture_z_light_fog_prim_xlu(void *g){(void)g;}
void _texture_z_light_fog_prim_shadow(void *g){(void)g;}
void *Lib_SegmentedToVirtual(void *p){return p;}
void *Setpos_HiliteReflect_xlu_init(xyz_t *p,void *g){
    (void)p;RoomRigGraphics *gfx=((RoomRigGame *)g)->gfx;
    gfx->tail-=48;for(int i=0;i<5;i++)*gfx->xlu_head++=(RoomCommand){0,0};++reflections;return gfx->tail;
}
static void step(RoomEffect *e,void *g){af_rw_effect_sphere_mv(e,g);if(e->timer>0)--e->timer;}
int main(void){
    unsigned long long game[0x2300/8]={0};context=game;
    RoomEffect appear={.arg0=1,.position={10,20,30}};
    af_rw_effect_sphere_ct(&appear,game,0);
    assert(appear.position.y==50 && appear.timer==2000 && added==1 && requests[2]==1 && sounds==1);
    for(int i=0;i<75;i++)step(&appear,game);
    assert(!visible && requests[1]==0);
    step(&appear,game);assert(visible && requests[1]==16);
    for(int i=0;i<24;i++)step(&appear,game);
    assert(appear.timer==0 && visible && requests[1]==16 && !removed);
    RoomEffect disappear={.arg0=0};af_rw_effect_sphere_ct(&disappear,game,0);
    assert(kills==1 && sounds==2);
    for(int i=0;i<100;i++)step(&disappear,game);
    assert(!visible && disappear.timer==0 && removed==1 && af_rw_effect_light_index==-1);
    RoomEffect sparkle={.position={0,20,0}};af_rw_effect_kira_ct(&sparkle,game,0);
    assert(sparkle.timer==500 && sparkle.velocity.y<0);
    for(int i=0;i<150;i++){af_rw_effect_kira_mv(&sparkle,game);if(sparkle.timer>0)--sparkle.timer;}
    assert(sparkle.timer==0);
    RoomEffect ground={0};af_rw_effect_light_ct(&ground,game,0);
    assert(ground.timer==195 && ground.position.y==0);
    eMHL_mv(&ground,game);assert(ground.specific[0]==170);
    ground.timer=75;eMHL_mv(&ground,game);assert(ground.specific[0]==0);
    ground.state=2;ground.timer=0;eMHL_mv(&ground,game);assert(ground.specific[0]==170);
    xyz_t p={0,0,0};failed_light=1;
    assert(af_rw_effect_light_reserve(game,&p,0,0,0,100)==-1 && !owner && !node);
    failed_light=0;af_rw_effect_light_index=af_rw_effect_light_reserve(game,&p,0,0,0,100);
    assert(af_rw_effect_light_index==0);af_rw_effect_light_colour(0,99,98,97);
    assert(light.point.colour[0]==99 && light.point.radius==100);
    af_rw_effect_reset(game);af_rw_effect_reset(game);assert(removed==2 && !owner && !node);
    RewardGraphics graphics={0};RoomCommand opaque[128],xlu[128],shadow[128];
    ((RoomRigGame *)game)->gfx=&graphics.ordinary;
    graphics.ordinary.head=opaque;graphics.ordinary.tail=(u8 *)(opaque+128);
    graphics.ordinary.xlu_head=xlu;graphics.ordinary.xlu_tail=(u8 *)(xlu+128);
    graphics.head=shadow;graphics.tail=(u8 *)(shadow+128);
    af_rw_effect_sphere_draw(&appear,game);assert(reflections==1 && graphics.ordinary.xlu_head==xlu+8);
    af_rw_effect_kira_draw(&sparkle,game);assert(graphics.ordinary.xlu_head==xlu+12);
    af_rw_effect_light_draw(&ground,game);assert(graphics.head==shadow+4);
    assert(shadow[1].a==0xFA000000 && shadow[2].b==0xFFFFFF64);
    graphics.ordinary.tail=(u8 *)opaque+47;
    RoomCommand *head=graphics.ordinary.xlu_head;u8 *tail=graphics.ordinary.xlu_tail;
    af_rw_effect_sphere_draw(&appear,game);assert(reflections==1 && head==graphics.ordinary.xlu_head && tail==graphics.ordinary.xlu_tail);
    graphics.tail=(u8 *)graphics.head+8;head=graphics.head;
    af_rw_effect_light_draw(&ground,game);assert(graphics.head==head);
    available=0;RoomEffect unavailable={.timer=300};af_rw_effect_sphere_mv(&unavailable,game);assert(!unavailable.timer);
    puts("Complete Shrine effects: visibility, single transition, sparks, ground light, cleanup, and arenas pass");
    return 0;
}
