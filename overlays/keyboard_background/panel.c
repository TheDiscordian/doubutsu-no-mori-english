/* GC keyboard frame texels/colours, adapted to the existing N64 hint panel. */
#include <PR/mbi.h>
#include "textures.inc"

static Gfx *af_bg_panel(Gfx *g, int x, int y, int width, int height) {
    int half_w, half_h, ds, dt;
    if (x<0 || y<0 || width!=236 || height!=114 || x+width>320 || y+height>240) return g;
    half_w=width/2; half_h=height/2;
    /* Donor half-panels sample 64x32 texels, clamping the 32x32 image. */
    ds=(64*1024+half_w/2)/half_w; dt=(32*1024+half_h/2)/half_h;
    gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_BLENDPEDECALA,G_CC_BLENDPEDECALA);
    gDPSetPrimColor(g++,0,255,225,205,225,255);
    gDPSetEnvColor(g++,160,90,245,255);
    gDPSetTextureFilter(g++,G_TF_BILERP);
    gDPLoadTextureBlock(g++,af_bg_frame_b,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                        G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
    /* Bottom-left and diagonally reflected top-right, as in the GC model. */
    gSPTextureRectangle(g++,x*4,(y+half_h)*4,(x+half_w)*4,(y+height)*4,
                        0,0,0,ds,dt);
    gSPTextureRectangle(g++,(x+half_w)*4,y*4,(x+width)*4,(y+half_h)*4,
                        0,2048,1024,-ds,-dt);
    gDPPipeSync(g++);
    gDPLoadTextureBlock(g++,af_bg_frame_a,G_IM_FMT_IA,G_IM_SIZ_8b,32,32,0,
                        G_TX_CLAMP,G_TX_CLAMP,5,5,0,0);
    /* Bottom-right and top-left use the complementary donor corners. */
    gSPTextureRectangle(g++,(x+half_w)*4,(y+half_h)*4,(x+width)*4,(y+height)*4,
                        0,2048,0,-ds,dt);
    gSPTextureRectangle(g++,x*4,y*4,(x+half_w)*4,(y+half_h)*4,0,0,0,ds,dt);
    return g;
}
