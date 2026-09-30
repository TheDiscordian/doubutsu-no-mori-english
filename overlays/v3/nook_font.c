/* Complete GAFE01-r0 name/code glyphs. Retain the installed font's state,
 * sixteen existing glyphs, and ordinary native drawing paths. */
#ifndef AF_NP_GLYPH_HOST_TEST
#include <PR/mbi.h>
#else
typedef unsigned char u8;
typedef unsigned int u32;
#endif
extern const u8 *glyph_resource;
extern u32 active_glyph;
#include "nook-font-assets.inc"
#include "resource_dma.h"
#include "/source/runtime/crc32.h"
#include "/source/runtime/crc32.c"
static const u8 *af_np_pixels __attribute__((section(".data")))=0;
static int af_np_load_pixels(void) {
    u32 a=AF_NP_PIXELS_RAM;
    if(af_np_pixels)return 1;
    if(a<0x804DA000u || (a&15u) || a>0x80500000u || AF_NP_PIXELS_BYTES>0x80500000u-a)return 0;
    if(af_v3_resource_read((void *)a,AF_NP_PIXELS_ROM,AF_NP_PIXELS_BYTES,
            (int (*)(void *,unsigned int,unsigned int))0x80026B44u) ||
            af_crc32((const unsigned char *)a,AF_NP_PIXELS_BYTES)!=AF_NP_PIXELS_CRC)return 0;
    ((void (*)(void *,u32))0x8002FE00u)((void *)a,AF_NP_PIXELS_BYTES);
    af_np_pixels=(const u8 *)a;return 1;
}

int af_np_glyph_index(const u8 *text,u32 bytes) {
    u32 i;
    if(!glyph_resource || !text || bytes<2 || text[0]!=0x80)return -1;
    for(i=0;i<16;i++)if(text[1]==glyph_resource[32+i])return (int)i;
    return af_np_pixels?16+(int)text[1]:-1;
}
u32 af_np_glyph_width(const u8 *text,u32 bytes) {
    int i;
    if(!text || !bytes)return 0;
    i=af_np_glyph_index(text,bytes);
    if(i>=16)return af_np_pixels[32+i-16];
    if(i>=0)return glyph_resource[48+i];
    return 12u-((const u8 *)0x80106AF4u)[text[0]];
}
void af_np_glyph_end(u32 previous) {
    active_glyph=glyph_resource && previous<=272?previous:0;
}
int af_np_glyph_code_width(u32 code,int cut) {
    (void)cut;
    if(code==0x80 && active_glyph) {
        if(active_glyph>=17 && active_glyph<=272 && af_np_pixels)return af_np_pixels[32+active_glyph-17];
        if(active_glyph<=16)return glyph_resource[47+active_glyph];
    }
    return code<256?12-((const u8 *)0x80106AF4u)[code]:12;
}
int af_np_glyph_texture_code(int code) {
    if(code==0x80 && active_glyph) {
        if(active_glyph>=17 && active_glyph<=272)return (int)active_glyph-17;
        if(active_glyph<=16)return (int)active_glyph-1;
    }
    return code;
}
const u8 *af_np_glyph_texture(void) {
    if(active_glyph>=17 && active_glyph<=272 && af_np_pixels)return af_np_pixels+288;
    return active_glyph && active_glyph<=16?glyph_resource+64:(const u8 *)0x8013A680u;
}

#ifndef AF_NP_GLYPH_HOST_TEST
typedef struct {float x,y;} Point;
extern int af_np_previous_font_install(void);
extern void af_np_previous_poly(void *,Gfx **,int,Point *,Point *,int,int);
/* The complete native title replay remains resident for the demo's lifetime.
 * Its sole checked allocation site uses this separate Expansion Pak buffer,
 * leaving the ordinary town arena available for actors and menus. */
void *af_np_title_buffer(u32 bytes) {
    if(*(volatile u32 *)0x80000318u==0x800000u && bytes==AF_NP_TITLE_BYTES)
        return (void *)AF_NP_TITLE_RAM;
    return ((void *(*)(u32))0x8009BFC0u)(bytes);
}
#ifdef AF_NP_CARD_E_MESSAGE
#include "/source/overlays/v3/nook_code_string.c"
struct AfNpMessageData {int loaded,id,length,cut;u8 text[1024];};
struct AfNpMessageWindow {
    u8 prefix[12];struct AfNpMessageData *data;u8 before_flags[0x28C-16];u32 flags;
};
extern int af_np_previous_dispatch(struct AfNpMessageWindow *,int *);
extern void af_np_dialogue_fault(int) __attribute__((noreturn));
int af_np_dispatch(struct AfNpMessageWindow *window,int *index) {
    struct AfNpMessageData *d=window?window->data:0;
    if(d && index && d->id==AF_NP_CARD_E_MESSAGE && *index>=0 &&
       *index<d->length-1 && d->length<=1024 && d->text[*index]==0x7F &&
       (d->text[*index+1]==0x34 || d->text[*index+1]==0x35)) {
        const u8 *code=(const u8 *)0x804C7808u;
        int row=d->text[*index+1]-0x34;
        int result=af_np_code_string(d->text,&d->length,*index,code+14*row);
        if(result<0)af_np_dialogue_fault(-1);
        if(result>0){window->flags&=~(1u<<16);return 0;}
    }
    return af_np_previous_dispatch(window,index);
}
#endif
/* The established polygon renderer gives each glyph a transparent border.
 * Use the same geometry and filtering for every source character. */
void af_np_glyph_poly(void *graph,Gfx **gpp,int code,Point *tl,Point *br,int s,int t) {
    Gfx *g=*gpp;
    Vtx *v;
    float sx,sy;
    int x0,x1,y0,y1,i;
    u32 slot=active_glyph-17;
    if(!af_np_pixels || slot>=256 || code!=0x80 || s<1 || s>12 || t!=16) {
        af_np_previous_poly(graph,gpp,code,tl,br,s,t);return;
    }
    v=(Vtx *)(*(u32 *)((u8 *)graph+0x29C)-64);
    *(u32 *)((u8 *)graph+0x29C)=(u32)v;
    sx=(br->x-tl->x)/(float)s;sy=(br->y-tl->y)/16.0f;
    x0=(int)((tl->x-sx-160.0f)*16.0f);x1=(int)((br->x+sx-160.0f)*16.0f);
    y0=(int)((120.0f-(tl->y-sy))*16.0f);y1=(int)((120.0f-(br->y+sy))*16.0f);
    for(i=0;i<4;i++) {
        v[i].v.ob[0]=i>=2?x1:x0;v[i].v.ob[1]=(i==1 || i==2)?y1:y0;
        v[i].v.ob[2]=0;v[i].v.flag=0;
        v[i].v.tc[0]=i>=2?(s+2)*64:0;v[i].v.tc[1]=(i==1 || i==2)?18*64:0;
        v[i].v.cn[0]=v[i].v.cn[1]=v[i].v.cn[2]=v[i].v.cn[3]=0;
    }
    gDPLoadTextureBlock_4b(g++,af_np_pixels+24864+slot*144,G_IM_FMT_I,16,18,0,
        G_TX_CLAMP,G_TX_CLAMP,0,0,0,0);
    gSPVertex(g++,v,4,0);gSP2Triangles(g++,0,1,2,0,0,2,3,0);*gpp=g;
}
int af_np_font_install(void) {
    volatile u32 *entry=(volatile u32 *)0x800911E8u;
    volatile u32 *title=(volatile u32 *)0x800C8DC0u;
    if(*title!=0x0C026FF0u)return 0;
    if(!af_np_load_pixels() || af_np_previous_font_install()!=1)return 0;
    if(entry[0]!=(0x08000000u|(((u32)af_np_previous_poly>>2)&0x03FFFFFFu)) || entry[1])return 0;
    entry[0]=0x08000000u|(((u32)af_np_glyph_poly>>2)&0x03FFFFFFu);entry[1]=0;
    ((void (*)(void *,u32))0x8002FE00u)((void *)entry,8);
    ((void (*)(void *,u32))0x80034CE0u)((void *)entry,8);
#ifdef AF_NP_CARD_E_MESSAGE
    entry=(volatile u32 *)0x800A21C0u;
    if(entry[0]!=(0x08000000u|(((u32)af_np_previous_dispatch>>2)&0x03FFFFFFu)) || entry[1])return 0;
    entry[0]=0x08000000u|(((u32)af_np_dispatch>>2)&0x03FFFFFFu);entry[1]=0;
    ((void (*)(void *,u32))0x8002FE00u)((void *)entry,8);
    ((void (*)(void *,u32))0x80034CE0u)((void *)entry,8);
#endif
    *title=0x0C000000u|(((u32)af_np_title_buffer>>2)&0x03FFFFFFu);
    ((void (*)(void *,u32))0x8002FE00u)((void *)title,4);
    ((void (*)(void *,u32))0x80034CE0u)((void *)title,4);
    return 1;
}
#endif
