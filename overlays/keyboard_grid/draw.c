/* Native display lists with the supplied losslessly untiled GC keycap. */
#include <PR/mbi.h>
#include "editor.h"

#define U32(p,o) (*(unsigned int *)((unsigned char *)(p)+(o)))
#define PTR(p,o) (*(void **)((unsigned char *)(p)+(o)))
static const unsigned char slide[4]={0,3,7,10};

static int space(void *graph, unsigned int bytes) {
    unsigned int head=U32(graph,0x298),tail=U32(graph,0x29C);
    return head<=tail && bytes<=tail-head;
}

static void text(void *graph, void *game, const unsigned char *s, int length,
                 float x, float y, int selected, int disabled, float scale) {
    int r=selected ? 255 : disabled ? 120 : 35;
    int g=selected ? 255 : disabled ? 120 : 30;
    int b=selected ? 255 : disabled ? 120 : 55;
    /* Mode zero emits to opaque graphics. Leave room for vertices and setup. */
    if (length<1 || length>64 || !space(graph,512u+(unsigned int)length*256u)) {
        af_grid_context.error=2;return;
    }
    af_hboard_font_line(game,s,length,x,y,r,g,b,255,0,1,scale,scale,0);
}

static void label(void *graph, void *game, const char *s, float x, float y) {
    int length=0;
    while (s[length] && length<64) ++length;
    text(graph,game,(const unsigned char *)s,length,x,y,0,0,0.75f);
}

static Gfx *rectangle(Gfx *g, int x, int y, int width, int height) {
    /* Clipping is handled before emission; never wrap negative RDP coordinates. */
    if (x<0 || y<0 || x+width>320 || y+height>240) return g;
    gDPFillRectangle(g++,x,y,x+width-1,y+height-1);
    return g;
}

void af_grid_editor_draw(void *submenu, void *menu, void *game) {
    struct af_grid_context *ctx=&af_grid_context;
    unsigned char *ovl;
    void *graph;
    Gfx *g;
    struct af_grid_state cell;
    unsigned int i,code;
    int x,y,selected,disabled,apology,newline,width;
    float dx,dy;
    unsigned char glyph[2];
    if (!game || !menu || !af_grid_owned(submenu) || menu!=ctx->menu) return;
    graph=PTR(game,0);ovl=((struct af_hboard_submenu_pointer *)submenu)->overlay;
    if (!graph || !space(graph,4096)) {ctx->error=2;return;}
    dx=*(float *)((unsigned char *)menu+0x18);dy=*(float *)((unsigned char *)menu+0x1C);
    if (!(dx>=-320.0f && dx<=320.0f && dy>=-240.0f && dy<=240.0f)) {ctx->error=3;return;}
    /* Original caller-window cursor/end markers still use segment twelve. */
    *(unsigned int *)0x801458D0u=U32(menu,0x28)+0x80000000u;
    g=PTR(graph,0x298);
    gSPSegment(g++,12,PTR(menu,0x28));
    gDPPipeSync(g++);
    gDPSetCycleType(g++,G_CYC_1CYCLE);
    gDPSetRenderMode(g++,G_RM_XLU_SURF,G_RM_XLU_SURF2);
    gDPSetDepthSource(g++,G_ZS_PRIM);
    gDPSetAlphaCompare(g++,G_AC_NONE);
    gDPSetTexturePersp(g++,G_TP_NONE);
    gDPSetTextureLUT(g++,G_TT_NONE);
    gDPSetCombineMode(g++,G_CC_PRIMITIVE,G_CC_PRIMITIVE);
    gDPSetPrimColor(g++,0,255,239,223,190,255);
    g=rectangle(g,(int)(42+dx),(int)(113-dy),236,114);
    gDPPipeSync(g++);
    gDPSetCombineLERP(g++,0,0,0,PRIMITIVE,0,0,0,TEXEL0,
                         0,0,0,PRIMITIVE,0,0,0,TEXEL0);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPLoadTextureBlock_4b(g++,af_grid_keycap,G_IM_FMT_I,16,16,0,
                         G_TX_MIRROR,G_TX_MIRROR,4,4,0,0);
    for (i=0;i<40;++i) {
        x=(int)(60+16*(i%10)+slide[i/10]+dx);y=(int)(133+16*(i/10)-dy);
        if (x<0 || y<0 || x+16>320 || y+16>240) continue;
        selected=(ctx->state.column==i%10 && ctx->state.row==i/10);
        gDPPipeSync(g++);
        gDPSetPrimColor(g++,0,255,selected ? (ctx->state.upper ? 0 : 205) : 255,
            selected ? 0 : 255,selected ? (ctx->state.upper ? 205 : 0) : 255,255);
        /* Donor UVs span 32 texels across a 16-pixel mirrored key. */
        gSPTextureRectangle(g++,x*4,y*4,(x+16)*4,(y+16)*4,0,0,0,2048,2048);
    }
    gDPPipeSync(g++);
    PTR(graph,0x298)=g;
    ((struct af_hboard_matrix_pointer *)(ovl+0x106B4))->function(graph);
    apology=af_grid_apology(submenu);newline=ctx->editor->rows>1;
    cell=ctx->state;
    for (i=0;i<40;++i) {
        cell.column=(unsigned char)(i%10);cell.row=(unsigned char)(i/10);
        code=af_grid_key(&cell,af_grid_tables,newline,apology);
        selected=(ctx->state.column==cell.column && ctx->state.row==cell.row);
        disabled=code==AF_GRID_DISABLED;
        x=(int)(60+16*cell.column+slide[cell.row]+dx);y=(int)(133+16*cell.row-dy);
        if (x<0 || y<0 || x+16>320 || y+16>240) continue;
        if (code==0xCD) {
            text(graph,game,(const unsigned char *)"RET",3,x+3,y+3,selected,0,0.5f);
        } else {
            if (disabled) code='-';
            if (code==' ') code='_';
            glyph[0]=(unsigned char)code;
            width=code>255 ? 12 : af_hboard_code_width(code,1);
            if (width<1 || width>12) {ctx->error=4;continue;}
            if (code>255) {glyph[0]=0x80;glyph[1]=(unsigned char)code;}
            text(graph,game,glyph,code>255 ? 2 : 1,x+(16-width)*0.5f,y+1,selected,disabled,1.0f);
        }
    }
    label(graph,game,ctx->state.page==1 ? "Symbols" : ctx->state.page==2 ? "Marks" :
        ctx->state.alphabetical ? "ABC" : "QWERTY",54+dx,116-dy);
    label(graph,game,"L: Case   Z: Page   L+Z: ABC",110+dx,117-dy);
    label(graph,game,"A: Type   B: Del   R: Space   Start: Done",51+dx,202-dy);
    label(graph,game,"Move: Stick/D-pad   Cursor: C   L+A: Alter",51+dx,215-dy);
    ++ctx->draws;
}
