/* Exact English sign pixels; retain the original lighting and cached geometry. */
#include <PR/mbi.h>

#define SIGN_LIST(base) \
    gsDPPipeSync(), \
    gsDPLoadTextureBlock_4b((base) + 0x25D0, G_IM_FMT_CI, 96, 32, 15, \
        G_TX_CLAMP, G_TX_MIRROR, 0, 5, 0, 0), \
    gsDPSetTile(G_IM_FMT_CI, G_IM_SIZ_4b, 6, 0, 1, 15, \
        G_TX_MIRROR, 5, 0, G_TX_CLAMP, 0, 0), \
    gsDPSetTileSize(1, 0, 0, 380, 124), \
    gsSP2Triangles(7, 8, 9, 0, 8, 10, 9, 0), \
    gsDPPipeSync(), \
    gsDPLoadTextureBlock_4b((base) + 0x1C78, G_IM_FMT_CI, 128, 32, 15, \
        G_TX_MIRROR, G_TX_MIRROR, 7, 5, 0, 0), \
    gsDPSetTile(G_IM_FMT_CI, G_IM_SIZ_4b, 8, 0, 1, 15, \
        G_TX_MIRROR, 5, 0, G_TX_MIRROR, 7, 0), \
    gsDPSetTileSize(1, 0, 0, 508, 124), \
    gsSPEndDisplayList()

const Gfx summer_sign[] __attribute__((section(".summer"), aligned(8))) = {
    SIGN_LIST(0x06095480),
};
const Gfx winter_sign[] __attribute__((section(".winter"), aligned(8))) = {
    SIGN_LIST(0x06098100),
};
