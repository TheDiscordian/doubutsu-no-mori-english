/* Give proportional polygon glyphs a transparent filtering border.
 * Character advances, speech rectangles, and original glyph pixels stay intact. */
#include <PR/mbi.h>
typedef struct { float x,y; } Point;
extern int af_previous_install(void);
extern const unsigned char *af_glyph_texture(void);
extern int af_glyph_texture_code(int);
extern void af_original_poly(void *,Gfx **,int,Point *,Point *,int,int);
extern const unsigned char af_border_map[256];
extern const unsigned char af_border_pixels[][144];
#define WORD(p,n) (*(u32 *)((unsigned char *)(p)+(n)))

void af_border_poly(void *graph,Gfx **gpp,int code,Point *tl,Point *br,int s,int t) {
    const unsigned char *texture=af_glyph_texture();
    int selected=af_glyph_texture_code(code),slot=-1;
    Gfx *g=*gpp;
    Vtx *v;
    float sx,sy;
    int x0,x1,y0,y1,i;
    if (texture==(const unsigned char *)0x8013A680u) {
        if ((unsigned)selected<256u && af_border_map[selected]!=255u) slot=af_border_map[selected];
    } else if ((unsigned)selected<16u) slot=81+selected;
    if (slot<0 || s<1 || s>12 || t!=16) {
        af_original_poly(graph,gpp,code,tl,br,s,t);
        return;
    }
    /* The native routine also reserves four vertices from this same arena.
     * Textures are immutable and persistent, not extra per-frame allocations. */
    v=(Vtx *)(WORD(graph,0x29C)-64);
    WORD(graph,0x29C)=(u32)v;
    sx=(br->x-tl->x)/(float)s;
    sy=(br->y-tl->y)/16.0f;
    x0=(int)((tl->x-sx-160.0f)*16.0f);
    x1=(int)((br->x+sx-160.0f)*16.0f);
    y0=(int)((120.0f-(tl->y-sy))*16.0f);
    y1=(int)((120.0f-(br->y+sy))*16.0f);
    for (i=0;i<4;++i) {
        v[i].v.ob[0]=i>=2 ? x1 : x0;
        v[i].v.ob[1]=(i==1 || i==2) ? y1 : y0;
        v[i].v.ob[2]=0; v[i].v.flag=0;
        v[i].v.tc[0]=i>=2 ? (s+2)*64 : 0;
        v[i].v.tc[1]=(i==1 || i==2) ? 18*64 : 0;
        v[i].v.cn[0]=v[i].v.cn[1]=v[i].v.cn[2]=v[i].v.cn[3]=0;
    }
    gDPLoadTextureBlock_4b(g++,af_border_pixels[slot],G_IM_FMT_I,16,18,0,
        G_TX_CLAMP,G_TX_CLAMP,0,0,0,0);
    gSPVertex(g++,v,4,0);
    gSP2Triangles(g++,0,1,2,0,0,2,3,0);
    *gpp=g;
}

int af_border_install(void) {
    volatile u32 *entry=(volatile u32 *)0x800911E8u;
    if (entry[0]!=0x27BDFF88u || entry[1]!=0xAFBF0024u) return 0;
    if (af_previous_install()!=1) return 0;
    entry[0]=0x08000000u|(((u32)af_border_poly>>2)&0x03FFFFFFu);
    entry[1]=0;
    ((void (*)(void *,u32))0x8002FE00u)((void *)entry,8);
    ((void (*)(void *,u32))0x80034CE0u)((void *)entry,8);
    return 1;
}
