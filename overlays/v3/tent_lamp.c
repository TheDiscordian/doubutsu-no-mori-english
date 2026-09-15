/* The donor's timed scene lamp, owned by the native effect controller.
 * Native effect code and actor size stay intact; no collectible is repurposed. */
#include "tent_lamp.h"
#define MAGIC 0x41464C50u
#define GUARD 0xAF1AC0DEu
#define MODEL_BYTES 3248u
#define ASSET_BYTES (MODEL_BYTES+32u)
#ifdef __mips__
_Static_assert(sizeof(LampState)==36,"Native lamp state layout");
_Static_assert(sizeof(LampState)<=48,"Lamp state exceeds its explicit reservation");
#endif
_Static_assert(__builtin_offsetof(LampGraphics,xlu)==0x2A8,"Native translucent arena");
extern volatile int native_scene,native_seconds;
extern volatile u32 native_effect_loaded;
extern void *native_malloc(u32);
extern void native_free(void*);
extern int native_dma(void*,u32,u32);
extern void native_writeback(void*,u32);
extern float native_approach(float*,float,float,float,float);
extern void native_opaque_state(LampGraphics*);
extern void native_environment_body(void*,void*,void*);
extern void native_room_prim_body(void*);
extern void native_set_diffuse(void*);
extern void native_permit_diffuse(void*);
static const u8 source_colour[3]={235,190,185};

static void original(unsigned offset,void *actor,void *game) {
#ifdef __mips__
    u32 base=native_effect_loaded;
    /* The engine retains this descriptor through the last actor destructor. */
    if (base>=0x80051A80u && base<=0x80800000u-0x5510u && !(base&15u))
        ((void (*)(void*,void*))(base+offset))(actor,game);
#else
    extern void lamp_test_original(unsigned,void*,void*);
    lamp_test_original(offset,actor,game);
#endif
}
static int active(void *game) {
    return af_v3_lamp_state.magic==MAGIC && af_v3_lamp_state.game==game && native_scene==35;
}
static int nice(void) { return native_seconds<18000 || native_seconds>=64800; }
static void load_model(void) {
    LampState *s=&af_v3_lamp_state;
    if (s->allocation) return;
    if (s->retry) { --s->retry; return; }
    u8 *p=native_malloc(ASSET_BYTES);
    if (!p) { s->retry=30; ++s->failures; return; }
    for (unsigned i=0;i<4;++i) {
        ((u32*)p)[i]=GUARD;
        ((u32*)(p+16+MODEL_BYTES))[i]=GUARD;
    }
    if (native_dma(p+16,0x02489000u,MODEL_BYTES)) {
        native_free(p);s->retry=30;++s->failures;return;
    }
    native_writeback(p,ASSET_BYTES);
    s->allocation=p;
}

__attribute__((section(".entry")))
void af_v3_lamp_ct(void *actor,void *game) {
    original(0x17DC,actor,game);
    if (native_scene!=35 || af_v3_lamp_state.magic==MAGIC) return;
    LampState *s=&af_v3_lamp_state;
    s->owner=actor;s->game=game;s->allocation=0;s->target=nice();
    s->visual=s->target ? 1.0f : 0.0f;
    s->light=s->target ? 1.0f : 0.14f;
    s->retry=s->failures=0;s->magic=MAGIC;
    load_model();
}
void af_v3_lamp_dt(void *actor,void *game) {
    LampState *s=&af_v3_lamp_state;
    if (s->magic==MAGIC && s->owner==actor && s->game==game) {
        u8 *p=s->allocation;
        s->magic=0;s->owner=0;s->game=0;s->allocation=0;
        s->visual=s->light=0;s->target=0;s->retry=s->failures=0;
        if (p) native_free(p);
    }
    original(0x18C8,actor,game);
}
void af_v3_lamp_mv(void *actor,void *game) {
    original(0x1E3C,actor,game);
    if (!active(game) || af_v3_lamp_state.owner!=actor) return;
    LampState *s=&af_v3_lamp_state;s->target=nice();
    native_approach(&s->visual,s->target ? 1.0f : 0.0f,0.015f,0.1f,0.001f);
    load_model();
}

void af_v3_lamp_environment(void *game,void *kankyo,void *global_light) {
    native_environment_body(game,kankyo,global_light);
    if (!active(game)) return;
    LampState *s=&af_v3_lamp_state;
    if (s->target) native_approach(&s->light,1.0f,0.01f,0.01f,0.01f);
    else { s->light-=0.01f;if(s->light<0.14f)s->light=0.14f; }
    /* Native environment initialization retains light-list ownership. The donor
     * attenuates colour, not the point radius, and scales both celestial lights. */
    u8 *k=kankyo;float celestial=1.0f-0.6f*s->light;
    for(unsigned i=0;i<3;++i) {
        k[0x28+i]=(u8)(source_colour[i]*s->light);
        k[0x92+i]=(u8)(k[0x92+i]*celestial);
        k[0x98+i]=(u8)(k[0x98+i]*celestial);
    }
    k[0xBC]=(u8)((float)k[0xBC]+s->light*(150.0f-(float)k[0xBC]));
    native_set_diffuse(kankyo);native_permit_diffuse(kankyo);
}

void af_v3_lamp_room_prim(void *game) {
    if (!active(game)) { native_room_prim_body(game);return; }
    LampGraphics *g=*(LampGraphics**)game;
    if (!g || (uptr)g->opa_tail<(uptr)g->opa || (uptr)g->xlu_tail<(uptr)g->xlu
            || (uptr)g->opa_tail-(uptr)g->opa<16 || (uptr)g->xlu_tail-(uptr)g->xlu<16) return;
    const u8 *room=(u8*)game+0x1C3D;
    float p=af_v3_lamp_state.light;u32 colour=255;
    for(unsigned i=0;i<3;++i) {
        int c=(int)(room[i]*(1.0f-0.3f*p)+source_colour[i]*(0.6f*p));
        if(c<0)c=0;else if(c>255)c=255;
        colour|=(u32)c<<(24-8*i);
    }
    g->opa[0]=(LampCommand){0xE7000000,0};g->opa[1]=(LampCommand){0xFA000080,colour};g->opa+=2;
    g->xlu[0]=(LampCommand){0xE7000000,0};g->xlu[1]=(LampCommand){0xFA000080,colour};g->xlu+=2;
}

void af_v3_lamp_dw(void *actor,void *game) {
    original(0x1A80,actor,game);
    if (!active(game) || af_v3_lamp_state.owner!=actor || !af_v3_lamp_state.allocation) return;
    LampState *s=&af_v3_lamp_state;u8 *p=s->allocation;
    for(unsigned i=0;i<4;++i)
        if(((u32*)p)[i]!=GUARD || ((u32*)(p+16+MODEL_BYTES))[i]!=GUARD) { ++s->failures;return; }
    LampGraphics *g=*(LampGraphics**)game;if(!g)return;
    uptr head=(uptr)g->opa,tail=(uptr)g->opa_tail;
    if((head&7u)||(tail&15u)||tail<head||tail-head<192u)return;
    uptr frame=(tail-64u)&~(uptr)15u;g->opa_tail=(u8*)frame;
    /* Complete fixed-point identity translated to origin, scaled by 0.05.
     * Each axis uses trunc(0.05*65536)=3276; no prior actor matrix is borrowed. */
    u32 *matrix=(u32*)frame;for(unsigned i=0;i<16;++i)matrix[i]=0;
    matrix[7]=1;matrix[8]=0x0CCC0000;matrix[10]=0x00000CCC;matrix[13]=0x0CCC0000;
    native_writeback(matrix,64);native_opaque_state(g);
    int lod=(int)(255.0f+s->visual*-255.0f);
    if(lod<0)lod=0;else if(lod>255)lod=255;
    LampCommand *c=g->opa;
    c[0]=(LampCommand){0xDA380003,(u32)frame};
    c[1]=(LampCommand){0xDB060018,(u32)(uptr)(p+16)};
    c[2]=(LampCommand){0xFA000000|(u32)lod,0xFFFFFFFF};
    c[3]=(LampCommand){0xDE000000,0x06000B10};g->opa=c+4;
}
