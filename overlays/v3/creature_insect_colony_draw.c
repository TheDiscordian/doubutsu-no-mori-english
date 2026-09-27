/* Complete two-layer ground-colony draw. Matrices and tile commands belong
 * to the current graphics frame, never to an actor destroyed before RSP use. */
#include "creature_insect_colony.h"
typedef struct {u32 a,b;} Command;
typedef struct {
    u8 prefix[0x298];Command *opaque;u8 *end;u8 pad[8];Command *xlu;u8 *xend;
} Graphics;
extern void af_insect_xlu_setup(Graphics *);
extern void *af_insect_hilite(xyz_t *,GAME *);
extern void af_insect_matrix(void *),af_insect_writeback(void *,int);

void af_insect_colony_draw(ACTOR *actor,GAME *game) {
    if (!actor || !game || actor->world.position.x<0.0f || actor->world.position.z<0.0f) return;
    Graphics *gfx=*(Graphics **)game;
    if (!gfx || !gfx->opaque || !gfx->end || !gfx->xlu || !gfx->xend) return;
    uintptr_t head=(uintptr_t)gfx->opaque,end=(uintptr_t)gfx->end;
    uintptr_t xhead=(uintptr_t)gfx->xlu,xend=(uintptr_t)gfx->xend;
    /* HiliteReflect_new consumes 32-byte LookAt + 16-byte Hilite and four
     * commands; setup consumes one. Our matrix/scroll uses 112 aligned bytes
     * and five commands. Reserve enough before either native helper writes. */
    if (((head|end|xhead|xend)&7) || end<head || end-head<176 ||
            xend<xhead || xend-xhead<80 || af_insect_colony_art_bytes<8 ||
            (af_insect_colony_model&7) || af_insect_colony_model>af_insect_colony_art_bytes-8u) return;
    af_insect_xlu_setup(gfx);
    af_insect_hilite(&actor->world.position,game);
    uintptr_t allocation=((uintptr_t)gfx->end-112u)&~(uintptr_t)15;
    gfx->end=(u8 *)allocation;
    Command *scroll=(Command *)(allocation+64);
    u32 frame=((AfInsectGameView *)game)->frame*2u;
    for (unsigned tile=0;tile<2;tile++) {
        u32 s=(((frame*(u32)(int)af_insect_colony_rates[tile][0])<<1)&0x3FFFu)>>2;
        u32 t=(((frame*(u32)(int)af_insect_colony_rates[tile][1])<<1)&0x3FFFu)>>2;
        scroll[tile*2]=(Command){0xE8000000,0};
        scroll[tile*2+1]=(Command){0xF2000000u|(s<<12)|t,
            (tile<<24)|(((s+124u)&0xFFFu)<<12)|((t+124u)&0xFFFu)};
    }
    scroll[4]=(Command){0xDF000000,0};
    af_insect_matrix((void *)allocation);
    Command *x=gfx->xlu;
    *x++=(Command){0xDB060018,(u32)(uintptr_t)af_insect_colony_art&0x1FFFFFFFu};
    *x++=(Command){0xDB060020,(u32)(uintptr_t)scroll&0x1FFFFFFFu};
    *x++=(Command){0xDA380003,(u32)allocation&0x1FFFFFFFu};
    *x++=(Command){0xFA0000FF,(u32)((AfInsectColony *)actor)->alpha};
    *x++=(Command){0xDE000000,0x06000000u+af_insect_colony_model};
    gfx->xlu=x;
    af_insect_writeback((void *)allocation,112);
}
#ifdef __mips__
_Static_assert(offsetof(Graphics,xlu)==0x2A8,"native translucent command head");
#endif
