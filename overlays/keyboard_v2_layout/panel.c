/* Unedited GC key-tray textures, with code-drawn N64-style controller shells. */
#include <PR/mbi.h>
#include "textures.inc"

static Gfx *af_bg_piece(Gfx *g, int x, int y, int width, int height) {
    int half_w=width/2, half_h=height/2, right_y=y-1;
    int ds=(64*1024+half_w/2)/half_w, dt=(32*1024+half_h/2)/half_h;
    if (x<0 || y<1 || x+width>320 || y+height>240) return g;
    gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_BLENDPEDECALA,G_CC_BLENDPEDECALA);
    gDPSetPrimColor(g++,0,255,235,235,235,255);
    gDPSetEnvColor(g++,174,177,181,255);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPLoadTextureBlock(g++,af_bg_frame_b,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                       G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
    gSPTextureRectangle(g++,x*4,(y+half_h)*4,(x+half_w)*4,(y+height)*4,0,0,0,ds,dt);
    gSPTextureRectangle(g++,(x+half_w)*4,right_y*4,(x+width)*4,(right_y+half_h)*4,
                       0,2048,1024,-ds,-dt);
    gDPPipeSync(g++);
    gDPLoadTextureBlock(g++,af_bg_frame_a,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                       G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
    gSPTextureRectangle(g++,(x+half_w)*4,(right_y+half_h)*4,(x+width)*4,(right_y+height)*4,
                       0,2048,1024,-ds,-dt);
    gSPTextureRectangle(g++,x*4,y*4,(x+half_w)*4,(y+half_h)*4,0,0,0,ds,dt);
    return g;
}

static Gfx *af_bg_panel(Gfx *g, int x, int y, int width, int height) {
    /* Rounded shoulders and tapered left/centre/right N64-style grips.
       These code-drawn shapes introduce no replacement bitmap assets. */
    static const unsigned char sections[][5]={
        {42,112,62,24,0}, {108,112,64,20,0}, {176,112,62,24,0},
        {12,150,54,70,1}, {228,115,76,50,0},
        {234,158,66,72,1}, {87,198,148,36,1}
    };
    static const unsigned char rounded[16]={12,7,4,2,1,0,0,0,0,0,0,1,2,4,7,12};
    static const unsigned char grip[16]={10,5,2,1,0,0,0,1,2,3,5,7,10,13,17,22};
    unsigned int i,j;
    (void)width; (void)height;
    gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_PRIMITIVE,G_CC_PRIMITIVE);
    for (i=0;i<sizeof(sections)/sizeof(sections[0]);++i) {
        const unsigned char *p=sections[i];
        int px=p[0]+x-42, py=p[1]+y-113;
        if (px<0 || py<0 || px+p[2]>320 || py+p[3]>240) continue;
        for (j=0;j<16;++j) {
            int edge=(p[4] ? grip[j] : rounded[j])*p[2]/64;
            int top=py+j*p[3]/16, bottom=py+(j+1)*p[3]/16;
            int shade=j ? 220-(int)j*2 : 242;
            gDPPipeSync(g++);
            gDPSetPrimColor(g++,0,255,shade,shade,shade+2,255);
            /* In one-cycle mode the lower/right rectangle edges are exclusive. */
            gDPFillRectangle(g++,px+edge,top,px+p[2]-edge,bottom);
        }
    }
    return af_bg_piece(g,52+x-42,128+y-113,184,76);
}
