/* Complete source transforms and material overrides on bounded native arenas. */
#include "reward_effects.h"
typedef struct {
    RoomRigGraphics ordinary;
    u8 before_shadow[0x2C8-sizeof(RoomRigGraphics)];
    RoomCommand *head;u8 *tail;
} RewardGraphics;
#ifdef __mips__
ROOM_CHECK(RewardGraphics,head,0x2C8);ROOM_CHECK(RewardGraphics,tail,0x2CC);
#endif
extern void Matrix_translate(float,float,float,u8),Matrix_scale(float,float,float,u8),Matrix_mult(float *,int);
extern void *_Matrix_to_Mtx(void *),*Setpos_HiliteReflect_xlu_init(xyz_t *,void *);
extern void osWritebackDCache(void *,int),_texture_z_light_fog_prim(void *);
extern void _texture_z_light_fog_prim_xlu(void *),_texture_z_light_fog_prim_shadow(void *);
static void *reserve(RoomCommand *head,u8 **tail) {
    uptr h=(uptr)head,t=(uptr)*tail;
    if(!h || (h&7u) || t<h || t-h<48+64+15)return 0;
    uptr matrix=(t-64)&~(uptr)15u;
    *tail=(u8 *)matrix;return (void *)matrix;
}
static void matrix(RoomCommand **head,void *m) {
    _Matrix_to_Mtx(m);osWritebackDCache(m,64);
    *(*head)++=(RoomCommand){0xDA380003,(u32)(uptr)m};
}
void af_rw_effect_sphere_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *g=opaque;
    if(!e || !af_rw_effect_ready(g) || !g->gfx)return;
    RoomRigGraphics *p=g->gfx;
    /* The native reflection helper takes 48 bytes from the opaque tail and
     * emits five commands on the translucent stream before its own setup. */
    uptr h=(uptr)p->head,t=(uptr)p->tail;
    if(!h || (h&7u) || t<h || t-h<48)return;
    h=(uptr)p->xlu_head;t=(uptr)p->xlu_tail;
    if(!h || (h&7u) || t<h || t-h<96+64+15)return;
    void *m=reserve(p->xlu_head,&p->xlu_tail);if(!m)return;
    Setpos_HiliteReflect_xlu_init(&e->position,g);
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    float s=e->scale.x*.01f;Matrix_scale(s,s,s,1);
    _texture_z_light_fog_prim(p);
    *p->xlu_head++=(RoomCommand){0xFA0000FF,0xFFFFFF00|((u32)e->specific[0]&255)};
    matrix(&p->xlu_head,m);
    *p->xlu_head++=(RoomCommand){0xDE000000,af_rw_effect_models[0]};
}
void af_rw_effect_kira_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *g=opaque;
    if(!e || !af_rw_effect_ready(g) || !g->gfx)return;
    RoomRigGraphics *p=g->gfx;void *m=reserve(p->xlu_head,&p->xlu_tail);if(!m)return;
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_mult((float *)((u8 *)g+0x1E5C),1);
    Matrix_scale(e->scale.x,e->scale.y,e->scale.z,1);
    _texture_z_light_fog_prim_xlu(p);matrix(&p->xlu_head,m);
    *p->xlu_head++=(RoomCommand){0xFA0000FF,0xFFFFFFC8};
    *p->xlu_head++=(RoomCommand){0xDB060020,(u32)(uptr)Lib_SegmentedToVirtual((void *)(uptr)af_rw_effect_kira_mode)};
    *p->xlu_head++=(RoomCommand){0xDE000000,af_rw_effect_models[1]};
}
void af_rw_effect_light_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *g=opaque;
    if(!e || !af_rw_effect_ready(g) || !g->gfx)return;
    RewardGraphics *p=(RewardGraphics *)g->gfx;void *m=reserve(p->head,&p->tail);if(!m)return;
    Matrix_translate(e->position.x,e->position.y+.1f,e->position.z,0);
    Matrix_scale(.01f,.01f,.01f,1);_texture_z_light_fog_prim_shadow(p);matrix(&p->head,m);
    *p->head++=(RoomCommand){0xFA000000,0xFFFFDC00|((u32)e->specific[0]&255)};
    *p->head++=(RoomCommand){0xFB000000,0xFFFFFF64};
    *p->head++=(RoomCommand){0xDE000000,af_rw_effect_models[2]};
}
