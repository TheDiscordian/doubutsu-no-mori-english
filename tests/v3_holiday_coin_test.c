/* Execute generated complete donor motion with host-native service doubles.
 * Rendering assertions inspect commands and arena bounds, not visual output. */
#include <assert.h>
#include <math.h>
#include <string.h>
#include "holiday_coin.h"
const volatile u8 af_hp_native_ticks=2;
volatile u32 af_hp_native_segments[16]={[6]=0x12345678};
const u8 af_coin_art[2048]={0};
const u32 af_coin_models[2]={0x06000400,0x06000500},af_coin_palettes[2]={0,32};
const u16 af_coin_sounds[2]={0x478,0x479};
static int requests,created,sounds,reflections,transforms,writes;
static int last_id,last_sound,ready=1,shrine_present=1;
static float random_value=.25f;
static AFSkyPlayer shrine;
static RoomEffect effect;
void af_coin_init(xyz_t,int,s16,GAME *,u16,s16,s16);
void af_coin_ct(RoomEffect *,GAME *,void *),af_coin_mv(RoomEffect *,GAME *);
int af_sky_ready(void *g) {return g && ready;}
float af_effect_random(void) {return random_value;}
float fqrand(void) {return random_value;}
AFSkyPlayer *af_coin_native_find(void *info,s16 profile,int part) {
    assert(info && profile==0x5C && part==0);return shrine_present?&shrine:0;
}
float sin_s(s16 x) {return sinf(x*(6.283185307179586f/65536));}
float cos_s(s16 x) {return cosf(x*(6.283185307179586f/65536));}
int mFI_BlockKind2BkNum(int *x,int *z,u32 kind) {assert(kind==4);*x=*z=1;return 1;}
float mFI_BkNum2BaseHeight(int x,int z) {assert(x==1 && z==1);return 0;}
void xyz_t_add(xyz_t *a,xyz_t *b,xyz_t *out) {*out=(xyz_t){a->x+b->x,a->y+b->y,a->z+b->z};}
void af_sky_continuous(RoomEffect *e,s16 unused,s16 timer) {assert(unused==100 && timer==100);e->timer=timer;}
float af_sky_adjust(s16 n,s16 first,s16 last,float a,float b) {
    if(n<=first)return a;
    if(n>=last)return b;
    return a+(b-a)*(n-first)/(last-first);
}
void af_hp_native_sound(u32 word,xyz_t *pos) {assert(pos);++sounds;last_sound=(int)word;}
static void request(int id,xyz_t p,int priority,s16 angle,void *g,u16 item,s16 a,s16 b) {
    (void)p;(void)priority;(void)angle;(void)g;(void)item;(void)a;(void)b;
    ++requests;last_id=id;
}
static RoomEffect *create(s16 id,xyz_t pos,xyz_t *offset,void *g,void *arg,u16 item,int priority,s16 a,s16 b) {
    assert(id==119 && !offset && !arg);++created;
    effect=(RoomEffect){.name=id,.position=pos,.item=item,.priority=(u8)priority,.arg0=a,.arg1=b};
    af_coin_ct(&effect,g,arg);return &effect;
}
static AFSkyClip clip={.request=request,.create=create};
AFSkyClip *af_sky_native_clip=&clip;
void Matrix_translate(float x,float y,float z,u8 mode) {(void)x;(void)y;(void)z;assert(mode==0);++transforms;}
void Matrix_scale(float x,float y,float z,u8 mode) {assert(x==.01f && y==x && z==x && mode==1);++transforms;}
void Matrix_RotateX(s16 x,int mode) {(void)x;assert(mode==1);++transforms;}
void Matrix_RotateY(s16 x,int mode) {Matrix_RotateX(x,mode);}
void Matrix_RotateZ(s16 x,int mode) {Matrix_RotateX(x,mode);}
void *_Matrix_to_Mtx(void *p) {memset(p,0,64);return p;}
void osWritebackDCache(void *p,int n) {assert(p && n==64);++writes;}
void _texture_z_light_fog_prim(void *g) {(void)g;}
void _texture_z_light_fog_prim_xlu(void *g) {(void)g;}
static void *reflection(xyz_t *pos,void *opaque,int xlu) {
    assert(pos);RoomRigGraphics *g=((RoomRigGame *)opaque)->gfx;
    assert((uptr)g->tail-(uptr)g->head>=48);g->tail-=48;
    if(xlu)g->xlu_head+=4;else g->head+=4;
    ++reflections;return g->tail;
}
void *Setpos_HiliteReflect_init(xyz_t *p,void *g) {return reflection(p,g,0);}
void *Setpos_HiliteReflect_xlu_init(xyz_t *p,void *g) {return reflection(p,g,1);}
static void draw_check(RoomEffect *e,RoomRigGame *game,int xlu) {
    _Alignas(16) u8 opaque[1024]={0},transparent[1024]={0};RoomRigGraphics *g=game->gfx;
    g->head=(RoomCommand *)opaque;g->tail=opaque+sizeof opaque;
    g->xlu_head=(RoomCommand *)transparent;g->xlu_tail=transparent+sizeof transparent;
    e->specific[0]=xlu;e->specific[5]=1;e->timer=150;
    int before=transforms;af_coin_draw(e,game);assert(transforms==before+5);
    RoomCommand *commands=(RoomCommand *)(xlu?transparent:opaque)+4;
    if(xlu)assert((commands++)->b==0xFFFFFF5A); /* half of 180 */
    assert(commands[0].a==0xDB060018 && commands[0].b==(u32)(uptr)af_coin_art);
    assert(commands[1].a==0xDB060020 && commands[1].b==(u32)(uptr)af_coin_art+32);
    assert(commands[2].a==0xDA380003 && commands[3].b==af_coin_models[xlu]);
    assert(commands[4].a==0xDB060018 && commands[4].b==0x12345678);
    assert((uptr)g->head<=(uptr)g->tail && (uptr)g->xlu_head<=(uptr)g->xlu_tail);
    int old=reflections;g->tail=(u8 *)g->head+40;af_coin_draw(e,game);assert(reflections==old);
    if(xlu) {
        g->tail=opaque+sizeof opaque;g->xlu_tail=(u8 *)g->xlu_head+40;
        af_coin_draw(e,game);assert(reflections==old);
    }
}
int main(void) {
    RoomRigGraphics graphics={0};RoomRigGame game={.gfx=&graphics};xyz_t p={10,80,105};
    shrine.actor_class.world.position=(xyz_t){10,80,20};
    af_hp_coin(p,1,0,&game,0,0,0);assert(requests==1 && last_id==119);
    af_coin_init(p,1,0,&game,0,0,0);
    assert(created==1 && sounds==1 && last_sound==0x478 && effect.timer==100);
    assert(effect.position.x==19 && effect.position.y==91 && effect.position.z==90);
    assert(effect.offset.x==97.5f && effect.offset.y==93 && effect.acceleration.y==-.2f);
    float vy=effect.velocity.y;af_coin_mv(&effect,&game);
    assert(fabsf(effect.velocity.y-(vy-.4f))<.00001f && !effect.specific[0]);
    for(int i=0;i<80 && !effect.specific[0];i++) {--effect.timer;af_coin_mv(&effect,&game);}
    assert(effect.specific[0] && sounds==2 && last_sound==0x479 && last_id==119 && requests==1);
    assert(effect.position.x>-10 && effect.position.x<30 && fabsf(effect.position.z-72.5f)<.001f);
    assert(effect.timer==299 || effect.timer==300);
    for(int i=0;i<20;i++) {--effect.timer;af_coin_mv(&effect,&game);}
    assert(effect.position.y==93 && effect.velocity.y==0 && !effect.specific[1] && !effect.specific[3]);
    draw_check(&effect,&game,0);draw_check(&effect,&game,1);assert(writes==2 && reflections==2);
    /* The real actor height is independent of the field block's base. All
     * source random angles must land inside both seasonal box meshes. */
    for(int level=0;level<4;level++)for(int r=0;r<20;r++) {
        random_value=r/20.0f;shrine.actor_class.world.position.y=level*120.0f;
        p.y=shrine.actor_class.world.position.y;
        int before=sounds;af_coin_init(p,1,0,&game,0,0,0);
        assert(effect.timer==100 && sounds==before+1);
        af_coin_mv(&effect,&game);assert(!effect.specific[0]);
        for(int i=0;i<60 && !effect.specific[0];i++) {--effect.timer;af_coin_mv(&effect,&game);}
        assert(effect.specific[0] && sounds==before+2 && requests==1);
        assert(effect.position.x>-10 && effect.position.x<30 && fabsf(effect.position.z-72.5f)<.001f);
        assert(effect.position.y<=p.y+17.5f && effect.position.y>=p.y+17.3f);
    }
    shrine_present=0;int before=sounds;af_coin_init(p,1,0,&game,0,0,0);
    assert(effect.timer==0 && sounds==before);
    shrine_present=1;p.z=-100;af_coin_init(p,1,0,&game,0,0,0);
    assert(effect.timer==0 && sounds==before);
    ready=0;af_hp_coin(p,1,0,&game,0,0,0);af_coin_mv(&effect,&game);
    assert(requests==1 && effect.timer==0);
    return 0;
}
