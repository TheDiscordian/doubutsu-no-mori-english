#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/tent_lamp.h"
LampState af_v3_lamp_state;
volatile int native_scene,native_seconds;
volatile u32 native_effect_loaded;
static int originals[4],allocated,freed,fail_malloc,fail_dma,plain_env,plain_room;
static _Alignas(16) u8 game[0x2000],other[0x2000],actor[0x200];
static _Alignas(16) LampCommand opaque[128],translucent[128];
static LampGraphics graphics;
void lamp_test_original(unsigned offset,void *a,void *g) {
    assert(a==actor && (g==game || g==other));
    int i=offset==0x17DC?0:offset==0x18C8?1:offset==0x1E3C?2:offset==0x1A80?3:-1;
    assert(i>=0);++originals[i];
}
void *native_malloc(u32 n) { assert(n==3280);if(fail_malloc)return NULL;++allocated;return aligned_alloc(16,n); }
void native_free(void *p) { ++freed;free(p); }
int native_dma(void *p,u32 source,u32 n) {
    assert(source==0x2489000 && n==3248);memset(p,0x5A,n);return fail_dma ? -1:0;
}
void native_writeback(void *p,u32 n) { assert(p && (n==64 || n==3280)); }
float native_approach(float *value,float target,float fraction,float maximum,float minimum) {
    float d=target-*value;
    if(d!=0) {
        float step=d*fraction;
        if(fabsf(step)<minimum)step=copysignf(minimum,step);
        if(fabsf(step)>maximum)step=copysignf(maximum,step);
        *value+=step;
        if((d>0 && *value>target)||(d<0 && *value<target))*value=target;
    }
    return target-*value;
}
void native_opaque_state(LampGraphics *g) { *g->opa++=(LampCommand){0xDE000000,0x12345678}; }
void native_environment_body(void *g,void *k,void *l) {
    assert(g && k && l);++plain_env;
    memset((u8*)k+0x92,200,3);memset((u8*)k+0x98,100,3);((u8*)k)[0xBC]=80;
}
void native_room_prim_body(void *g) { assert(g);++plain_room; }
void native_set_diffuse(void *k) { assert(k); }
void native_permit_diffuse(void *k) { assert(k); }
static void arenas(void) {
    memset(opaque,0xA5,sizeof(opaque));memset(translucent,0xA5,sizeof(translucent));
    graphics.opa=opaque;graphics.opa_tail=(u8*)(opaque+128);
    graphics.xlu=translucent;graphics.xlu_tail=(u8*)(translucent+128);
    *(LampGraphics**)game=&graphics;*(LampGraphics**)other=&graphics;
}
static void environment(void) { af_v3_lamp_environment(game,game+0x1B98,game+0x1C60); }
int main(void) {
    arenas();native_scene=7;native_seconds=64800;
    af_v3_lamp_ct(actor,game);assert(!af_v3_lamp_state.magic && !allocated);
    af_v3_lamp_room_prim(game);assert(plain_room==1);
    native_scene=35;native_seconds=17999;af_v3_lamp_ct(actor,game);
    assert(allocated==1 && af_v3_lamp_state.visual==1 && af_v3_lamp_state.light==1);
    u8 *allocation=af_v3_lamp_state.allocation;assert(allocation && allocation[16]==0x5A);
    af_v3_lamp_ct(actor,game);assert(allocated==1); /* No duplicate resource. */
    environment();assert(game[0x1BC0]==235 && game[0x1BC1]==190 && game[0x1BC2]==185);
    assert(game[0x1C54]==150);
    af_v3_lamp_dw(actor,game);assert(graphics.opa==opaque+5);
    assert(opaque[3].a==0xFA000000 && opaque[4].b==0x06000B10);
    u32 *m=(u32*)graphics.opa_tail;
    assert(m[7]==1 && m[8]==0x0CCC0000 && m[10]==0xCCC && m[13]==0x0CCC0000);
    for(int i=0;i<16;++i)if(i!=7 && i!=8 && i!=10 && i!=13)assert(m[i]==0);
    native_seconds=18000;af_v3_lamp_mv(actor,game);environment();
    assert(af_v3_lamp_state.target==0 && fabsf(af_v3_lamp_state.visual-0.985f)<0.000001f);
    assert(fabsf(af_v3_lamp_state.light-0.99f)<0.000001f);
    for(int i=0;i<500;++i) { af_v3_lamp_mv(actor,game);environment(); }
    assert(af_v3_lamp_state.visual==0 && af_v3_lamp_state.light==0.14f);
    assert(game[0x1BC0]==32 && game[0x1BC1]==26 && game[0x1BC2]==25);
    arenas();memset(game+0x1C3D,200,3);af_v3_lamp_room_prim(game);
    assert(graphics.opa==opaque+2 && graphics.xlu==translucent+2);
    assert(opaque[1].a==0xFA000080 && opaque[1].b==translucent[1].b);
    assert((opaque[1].b>>24)==211);
    arenas();af_v3_lamp_dw(actor,game);assert(opaque[3].a==0xFA0000FF);
    native_seconds=64799;af_v3_lamp_mv(actor,game);assert(af_v3_lamp_state.target==0);
    native_seconds=64800;af_v3_lamp_mv(actor,game);environment();
    assert(af_v3_lamp_state.target==1 && af_v3_lamp_state.visual>0 && af_v3_lamp_state.light>0.14f);
    for(int i=0;i<500;++i) { af_v3_lamp_mv(actor,game);environment(); }
    assert(af_v3_lamp_state.light==1 && af_v3_lamp_state.visual==1);
    arenas();graphics.opa_tail=(u8*)(opaque+8);af_v3_lamp_dw(actor,game);
    assert(graphics.opa==opaque); /* No partial draw on arena exhaustion. */
    arenas();((u32*)allocation)[0]^=1;af_v3_lamp_dw(actor,game);
    assert(graphics.opa==opaque && af_v3_lamp_state.failures==1);((u32*)allocation)[0]^=1;
    arenas();af_v3_lamp_dw(actor,other);assert(graphics.opa==opaque);
    af_v3_lamp_dt(actor,other);assert(!freed && af_v3_lamp_state.magic);
    af_v3_lamp_dt(actor,game);assert(freed==1 && !af_v3_lamp_state.magic && !af_v3_lamp_state.allocation);
    fail_malloc=1;af_v3_lamp_ct(actor,game);assert(af_v3_lamp_state.retry==30 && !af_v3_lamp_state.allocation);
    fail_malloc=0;for(int i=0;i<31;++i)af_v3_lamp_mv(actor,game);
    assert(allocated==2 && af_v3_lamp_state.allocation);af_v3_lamp_dt(actor,game);
    fail_dma=1;af_v3_lamp_ct(actor,game);assert(!af_v3_lamp_state.allocation && allocated==freed);
    fail_dma=0;af_v3_lamp_dt(actor,game);
    assert(plain_env>0 && originals[0]>0 && originals[1]>0 && originals[2]>0 && originals[3]>0);
    puts("pass: lamp ownership, donor fades, complete model draw, room light, failures, and cleanup");
}
