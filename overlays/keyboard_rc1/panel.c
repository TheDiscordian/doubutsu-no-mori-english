/* Correct GC corner directions; retain the V1 colours and native key grid. */
#include <PR/mbi.h>
#include "textures.inc"

static Gfx *af_bg_panel(Gfx *g, int x, int y, int width, int height) {
    int half_w, half_h, ds, dt, right_y;
    if (x<0 || y<2 || width!=236 || height!=114 || x+width>320 || y+height>240) return g;
    half_w=width/2; half_h=height/2;
    /* The donor's right pair is one pixel higher at its 73-pixel height.
       Round the scaled displacement to two pixels for this 114-pixel panel. */
    right_y=y-2;
    ds=(64*1024+half_w/2)/half_w; dt=(32*1024+half_h/2)/half_h;
    gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_BLENDPEDECALA,G_CC_BLENDPEDECALA);
    gDPSetPrimColor(g++,0,255,225,205,225,255);
    gDPSetEnvColor(g++,160,90,245,255);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPLoadTextureBlock(g++,af_bg_frame_b,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                       G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
    gSPTextureRectangle(g++,x*4,(y+half_h)*4,(x+half_w)*4,(y+height)*4,
                       0,0,0,ds,dt);
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
