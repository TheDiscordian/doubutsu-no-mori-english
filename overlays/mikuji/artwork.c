/* Source-matching GC fortune table, expressed in native F3DEX2 commands. */
#include <PR/mbi.h>

const Gfx mikuji_entry[] __attribute__((section(".entry"), aligned(8))) = {
    gsSPDisplayList(0x06023118),
    gsSPEndDisplayList(),
    gsSPNoOp(),
    gsSPNoOp(),
};

const Gfx mikuji_model[] __attribute__((section(".model"), aligned(8))) = {
    gsDPPipeSync(),
    gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON),
    gsDPSetCombineLERP(TEXEL0, 0, SHADE, 0, 0, 0, 0, TEXEL0,
                      PRIMITIVE, 0, COMBINED, 0, 0, 0, 0, COMBINED),
    gsDPSetRenderMode(G_RM_FOG_SHADE_A, G_RM_AA_ZB_TEX_EDGE2),
    gsDPSetTextureLUT(G_TT_RGBA16),
    gsDPSetPrimColor(0, 128, 255, 255, 255, 255),
    /* The GC-only G_DECAL_LEQUAL name contributes zero bits. */
    gsSPLoadGeometryMode(G_ZBUFFER | G_SHADE | G_CULL_BACK | G_FOG |
                        G_LIGHTING | G_SHADING_SMOOTH),
    gsDPLoadTLUT_pal16(15, 0x060223A8),
    gsDPLoadTextureBlock_4b(0x060223E8, G_IM_FMT_CI, 64, 64, 15,
                          G_TX_MIRROR, G_TX_MIRROR, 6, 6, 0, 0),
    gsSPVertex(0x06022DE8, 27, 0),
    gsSP2Triangles(0, 1, 2, 0, 0, 2, 3, 0),
    gsSP2Triangles(1, 4, 5, 0, 1, 5, 2, 0),
    gsSP2Triangles(6, 7, 8, 0, 6, 8, 9, 0),
    gsSP2Triangles(10, 11, 12, 0, 11, 13, 12, 0),
    gsSP2Triangles(11, 14, 13, 0, 11, 15, 14, 0),
    gsSP2Triangles(16, 17, 18, 0, 19, 20, 21, 0),
    gsSP2Triangles(20, 22, 21, 0, 19, 23, 20, 0),
    gsSP2Triangles(23, 24, 20, 0, 24, 25, 20, 0),
    gsSP2Triangles(25, 22, 20, 0, 24, 26, 25, 0),
    gsDPPipeSync(),
    gsDPLoadTLUT_pal16(15, 0x060223C8),
    gsDPLoadTextureBlock_4b(0x06022BE8, G_IM_FMT_CI, 32, 32, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 5, 5, 0, 0),
    gsSPVertex(0x06022F98, 24, 0),
    gsSP2Triangles(0, 1, 2, 0, 0, 2, 3, 0),
    gsSP2Triangles(4, 5, 6, 0, 4, 6, 7, 0),
    gsSP2Triangles(8, 9, 10, 0, 8, 10, 11, 0),
    gsSP2Triangles(12, 13, 14, 0, 12, 14, 15, 0),
    gsSP2Triangles(16, 17, 18, 0, 16, 18, 19, 0),
    gsSP2Triangles(20, 21, 22, 0, 20, 22, 23, 0),
    gsSPEndDisplayList(),
};
