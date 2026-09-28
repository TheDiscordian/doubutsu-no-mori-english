/* Complete rope and shadow submission. Deformation and collision come from the
 * donor source; both vertex loads share one full, per-frame mutable array. */
#include "holiday_participants.h"
#include "room_rigs.h"
typedef struct {
    RoomRigGraphics base;
    u8 before_shadow[0x2C8-0x2A8-2*sizeof(void *)];
    RoomCommand *shadow;u8 *shadow_tail;
} AFHPGraphics;
extern const Vtx tol_rope_1_v[60];
extern volatile u32 af_hp_native_segments[16];
extern void _Matrix_to_Mtx(void *),osWritebackDCache(void *,int);
extern void _texture_z_light_fog_prim_npc(void *),_texture_z_light_fog_prim_shadow(void *);
#ifdef __mips__
_Static_assert(__builtin_offsetof(AFHPGraphics,shadow)==0x2C8,"Native shadow arena");
#endif
static int space(const void *head,const void *tail,u32 bytes) {
    uptr h=(uptr)head,t=(uptr)tail;
    return h && !((h|t)&7u) && t>=h && t-h>=bytes;
}
void af_hp_rope_draw(ACTOR *actor,GAME *game,void (*deform)(Vtx *)) {
    if(!actor || !game || !deform || !af_hp_admit(actor,game))return;
    AFHPGraphics *graphics=*(AFHPGraphics **)game;
    if(!graphics)return;
    RoomRigGraphics *g=&graphics->base;
    if(!space(g->head,g->tail,80+64+15) || !space(graphics->shadow,graphics->shadow_tail,64))return;
    void *matrix=(void *)(((uptr)g->tail-64)&~(uptr)15);
    g->tail=matrix;
    const Vtx *vertices=tol_rope_1_v;
    /* Preserve the source's static-geometry fallback when vertex space runs
     * out. Never let an allocation failure become an invalid segment. */
    if(space(g->head,g->tail,80+60*sizeof(Vtx)+15)) {
        Vtx *work=(Vtx *)(((uptr)g->tail-60*sizeof(Vtx))&~(uptr)15);
        g->tail=(u8 *)work;deform(work);osWritebackDCache(work,60*sizeof(Vtx));vertices=work;
    }
    _Matrix_to_Mtx(matrix);osWritebackDCache(matrix,64);
    u32 base=(u32)(uptr)af_hp_rope_art,previous=af_hp_native_segments[6];
    _texture_z_light_fog_prim_npc(graphics);
    *g->head++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    *g->head++=(RoomCommand){0xDB060018,base};
    *g->head++=(RoomCommand){0xDB060020,(u32)(uptr)vertices};
    *g->head++=(RoomCommand){0xDE000000,af_hp_rope_models[0]};
    *g->head++=(RoomCommand){0xDB060018,previous};
    _texture_z_light_fog_prim_shadow(graphics);
    *graphics->shadow++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    *graphics->shadow++=(RoomCommand){0xDB060018,base};
    *graphics->shadow++=(RoomCommand){0xDE000000,af_hp_rope_models[1]};
    *graphics->shadow++=(RoomCommand){0xDB060018,previous};
}
