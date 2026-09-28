/* Complete source offering effect uses the shared native effect pool, water
 * subeffects, installed sound programmes, and explicit palette selection. */
#include "holiday_coin.h"
extern void af_hp_native_sound(u32,xyz_t *);
void af_hp_coin(xyz_t p,int priority,s16 angle,GAME *g,u16 name,s16 a,s16 b) {
    if(af_sky_ready(g))af_sky_native_clip->request(AF_COIN_ID,p,priority,angle,g,name,a,b);
}
RoomEffect *af_coin_create(s16 id,xyz_t p,xyz_t *offset,GAME *g,void *arg,u16 name,int priority,s16 a,s16 b) {
    return id==AF_COIN_ID && af_sky_ready(g)?
        af_sky_native_clip->create(id,p,offset,g,arg,name,priority,a,b):0;
}
void af_coin_request(int id,xyz_t p,int priority,s16 angle,GAME *g,u16 name,s16 a,s16 b) {
    /* The already converted insect family retains these complete native
     * water effects, including every ripple/spray child and native cadence. */
    if(id==eEC_EFFECT_TURI_MIZU && af_sky_ready(g))
        af_sky_native_clip->request(id,p,priority,angle,g,name,a,b);
}
void af_coin_sound(u32 word,xyz_t *p) {
    if(p && (word==0x466 || word==0x467))af_hp_native_sound(af_coin_sounds[word-0x466],p);
}
extern void Matrix_translate(float,float,float,u8),Matrix_scale(float,float,float,u8);
extern void Matrix_RotateX(s16,int),Matrix_RotateY(s16,int),Matrix_RotateZ(s16,int);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
extern void _texture_z_light_fog_prim(void *),_texture_z_light_fog_prim_xlu(void *);
extern void *Setpos_HiliteReflect_init(xyz_t *,void *),*Setpos_HiliteReflect_xlu_init(xyz_t *,void *);
static int space(const void *head,const void *tail,u32 n) {
    uptr h=(uptr)head,t=(uptr)tail;
    return h && !((h|t)&7u) && t>=h && t-h>=n;
}
void af_coin_draw(RoomEffect *e,GAME *opaque) {
    RoomRigGame *game=opaque;
    if(!e || !af_sky_ready(game) || !game->gfx)return;
    RoomRigGraphics *g=game->gfx;int submerged=!!e->specific[0];
    /* Native reflection always allocates 32-byte LookAt + 16-byte Hilite
     * records from the opaque tail, even for translucent submission. */
    if(submerged) {
        if(!space(g->head,g->tail,48) || !space(g->xlu_head,g->xlu_tail,128+64+15))return;
    } else if(!space(g->head,g->tail,128+64+48+15))return;
    u8 **tail=submerged?&g->xlu_tail:&g->tail;
    void *matrix=(void *)(((uptr)*tail-64u)&~(uptr)15u);*tail=matrix;
    if(submerged) {
        _texture_z_light_fog_prim_xlu(g);Setpos_HiliteReflect_xlu_init(&e->position,game);
    } else {
        _texture_z_light_fog_prim(g);Setpos_HiliteReflect_init(&e->position,game);
    }
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_RotateX(e->specific[1],1);Matrix_RotateY(e->specific[2],1);Matrix_RotateZ(e->specific[3],1);
    Matrix_scale(.01f,.01f,.01f,1);_Matrix_to_Mtx(matrix);osWritebackDCache(matrix,64);
    RoomCommand **head=submerged?&g->xlu_head:&g->head;
    if(submerged) {
        u32 alpha=(u8)(int)af_sky_adjust(300-e->timer,0,300,180,0);
        *(*head)++=(RoomCommand){0xFA000080,0xFFFFFF00|alpha};
    }
    *(*head)++=(RoomCommand){0xDB060018,(u32)(uptr)af_coin_art};
    *(*head)++=(RoomCommand){0xDB060020,(u32)(uptr)af_coin_art+af_coin_palettes[e->specific[5]&1]};
    *(*head)++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    *(*head)++=(RoomCommand){0xDE000000,af_coin_models[submerged]};
    *(*head)++=(RoomCommand){0xDB060018,af_hp_native_segments[6]};
}
