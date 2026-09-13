/* Unedited GC tray; analytically rounded, softly filtered N64 controller shells. */
#include <PR/mbi.h>
#include "textures.inc"

static Gfx *af_bg_piece(Gfx *g, int x, int y, int width, int height) {
    int half_w=width/2, half_h=height/2, right_y=y-1;
    int ds=(64*1024+half_w/2)/half_w, dt=(32*1024+half_h/2)/half_h;
    int i;
    if (x<0 || y<1 || x+width>320 || y+height>240) return g;
    /* The caller already selects this same grey material and bilinear filter. */
    for (i=0;i<4;++i) {
        int mirror=i&1, px=x+(mirror ? half_w : 0);
        int py=(mirror ? right_y : y)+((i==0 || i==3) ? half_h : 0);
        if (!mirror) {
            const void *tile=i ? af_bg_frame_a : af_bg_frame_b;
            gDPPipeSync(g++);
            gDPLoadTextureBlock(g++,tile,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                               G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
        }
        gSPTextureRectangle(g++,px*4,py*4,(px+half_w)*4,(py+half_h)*4,0,
                            mirror ? 2048 : 0,mirror ? 1024 : 0,
                            mirror ? -ds : ds,mirror ? -dt : dt);
    }
    return g;
}

static Gfx *af_bg_panel(Gfx *g, int x, int y, int width, int height) {
    /* Nine-slice a shared antialiased quarter-circle at each shell's radius. */
    static const unsigned char sections[][5]={
        {42,112,62,24,12}, {108,112,64,20,10}, {176,112,62,24,12},
        {12,150,54,70,24}, {236,114,64,61,20},
        {228,175,76,56,22}, {87,198,148,36,18}
    };
    unsigned int i,j,k;
    (void)width; (void)height;
    gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_BLENDPEDECALA,G_CC_BLENDPEDECALA);
    gDPSetPrimColor(g++,0,255,223,226,230,255);
    gDPSetEnvColor(g++,174,177,181,255);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPLoadTextureBlock_4b(g++,af_bg_corner,G_IM_FMT_I,16,16,0,
                          G_TX_CLAMP,G_TX_CLAMP,4,4,0,0);
    for (i=0;i<sizeof(sections)/sizeof(sections[0]);++i) {
        const unsigned char *p=sections[i];
        int px=p[0]+x-42, py=p[1]+y-113;
        int r=p[4], step=15360/(r-1);
        int xs[4]={px,px+r,px+p[2]-r,px+p[2]};
        int ys[4]={py,py+r,py+p[3]-r,py+p[3]};
        int delta[3]={step,0,-step};
        if (px<0 || py<0 || px+p[2]>320 || py+p[3]>240) continue;
        for (j=0;j<3;++j) for (k=0;k<3;++k) {
            if (xs[k]==xs[k+1] || ys[j]==ys[j+1]) continue;
            gSPTextureRectangle(g++,xs[k]*4,ys[j]*4,xs[k+1]*4,ys[j+1]*4,0,
                                k ? 480 : 0,j ? 480 : 0,delta[k],delta[j]);
        }
    }
    return af_bg_piece(g,52+x-42,128+y-113,184,76);
}
