/* Complete donor steam and room-projectile lifecycles in the native effect
 * pool. One native update advances two source physics ticks; the native owner
 * supplies the remaining timer decrement. No additional particle state. */
#include "room_effects.h"
extern u32 qrand(void);
extern float sin_s(s16),cos_s(s16);
extern u8 *af_v3_room_debug;
extern void Matrix_translate(float,float,float,u8);
extern void Matrix_mult(float *,int);
extern void Matrix_scale(float,float,float,u8);
extern void Matrix_RotateY(s16,int);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
extern void _texture_z_light_fog_prim(void *);
extern void _texture_z_light_fog_prim_xlu(void *);
extern void sAdo_OngenTrgStart(u32,float *);

static float steam_register(u32 index) {
    uptr debug=(uptr)af_v3_room_debug;
    if (!debug || (debug&1u)) return 0;
#ifdef __mips__
    if (debug<0x80000000u || debug>0x80800000u-0x1C94u) return 0;
#endif
    return *(const s16 *)(debug+0x14u+2u*(36u*96u+index));
}

void af_v3_steam_init(EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    (void)angle;
    if (room_effect_clip) room_effect_clip->create(ROOM_EFFECT_STEAM,pos,0,game,0,item,priority,a,b);
}

void af_v3_steam_ct(RoomEffect *e,void *game,void *arg) {
    (void)game;(void)arg;
    s16 angle=(s16)qrand();
    e->position.y+=steam_register(0x34)+1.0f;
    float scale=steam_register(0x37)*0.0001f+0.001f;
    e->scale=(EffectPosition){scale,scale,scale};
    e->timer=44;
    e->acceleration=(EffectPosition){0,steam_register(0x32)*0.001f+0.017f,0};
    e->velocity=(EffectPosition){0,0,0};
    e->position.x+=e->arg0*sin_s(angle);
    e->position.z+=e->arg0*cos_s(angle);
}

static void integrate(RoomEffect *e) {
    e->velocity.x+=e->acceleration.x;
    e->velocity.y+=e->acceleration.y;
    e->velocity.z+=e->acceleration.z;
    e->position.x+=e->velocity.x;
    e->position.y+=e->velocity.y;
    e->position.z+=e->velocity.z;
}

void af_v3_steam_mv(RoomEffect *e,void *game) {
    (void)game;
    float drag=steam_register(0x39)*0.001f+0.95f;
    for (int step=0;step<2 && e->timer>step;++step) {
        integrate(e);e->velocity.y*=drag;
    }
    if (e->timer>0) --e->timer;
}

/* Reserve all commands and the matrix before modifying either arena. */
static void *particle_matrix(RoomRigGraphics *g,int translucent,u32 commands) {
    uptr head=(uptr)(translucent ? g->xlu_head:g->head);
    uptr tail=(uptr)(translucent ? g->xlu_tail:g->tail);
    if (!head || (head&7u) || tail<head || tail-head<commands*8u+64u+15u) return 0;
    uptr matrix=(tail-64u)&~(uptr)15u;
    if (translucent) g->xlu_tail=(u8 *)matrix;else g->tail=(u8 *)matrix;
    return (void *)matrix;
}

void af_v3_steam_dw(RoomEffect *e,RoomRigGame *game) {
    static const u8 pairs[22][2]={
        {0,0},{0,0},{0,0},{0,0},{0,0},{0,0},{0,1},{0,1},{0,1},{1,1},{1,2},
        {1,2},{1,2},{2,2},{2,3},{2,3},{2,3},{3,3},{3,3},{3,3},{3,3},{3,3}};
    static const u8 fractions[22]={0,0,0,0,0,0,64,128,192,0,64,128,192,0,64,128,192,0,0,0,0,0};
    if (!game || !game->gfx || !room_effect_clip || e->timer<=0 || e->timer>44) return;
    s16 elapsed=44-e->timer;
    u32 frame=(u32)elapsed>>1;
    float start=e->arg1 ? 0.001f:steam_register(0x37)*0.0001f+0.001f;
    float end=e->arg1 ? 0.01f:steam_register(0x38)*0.0001f+0.005f;
    float scale=room_effect_clip->adjust(elapsed,0,44,start,end);
    e->scale=(EffectPosition){scale,scale,scale};
    int alpha=(int)room_effect_clip->adjust(elapsed,0,44,
        steam_register(0x35)+(e->arg1 ? 190.0f:130.0f),steam_register(0x36)+10.0f);
    RoomRigGraphics *g=game->gfx;
    void *matrix=particle_matrix(g,1,6);
    if (!matrix) return;
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_mult((float *)((u8 *)game+0x1E5C),1);
    Matrix_scale(scale,scale,scale,1);
    _Matrix_to_Mtx(matrix);osWritebackDCache(matrix,64);
    _texture_z_light_fog_prim_xlu(g);
    *g->xlu_head++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    for (u32 i=0;i<2;++i) {
        void *texture=Lib_SegmentedToVirtual((void *)(uptr)(AF_EFFECT_STEAM_TEXTURES+128u*pairs[frame][i]));
        *g->xlu_head++=(RoomCommand){0xDB060020u+i*4u,(u32)(uptr)texture};
    }
    *g->xlu_head++=(RoomCommand){0xFA000000u|fractions[frame],
        (e->arg1 ? 0xFFC88200u:0xFFFFFF00u)|((u32)alpha&255u)};
    *g->xlu_head++=(RoomCommand){0xDE000000,e->arg1 ? AF_EFFECT_STEAM_STEW:AF_EFFECT_STEAM_MODEL};
}

void af_v3_projectile_init(EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    (void)a;
    if (room_effect_clip) room_effect_clip->create(ROOM_EFFECT_PROJECTILE,pos,0,game,0,item,priority,angle,b);
}

static float absolute(float n) { return n<0 ? -n:n; }
static int near_angle(u16 a,u16 b) { int delta=(int)a-(int)b;return delta>=-15 && delta<=15; }

void af_v3_projectile_ct(RoomEffect *e,void *game,void *arg) {
    (void)game;(void)arg;
    e->acceleration=(EffectPosition){0,0,0};
    e->velocity=(EffectPosition){sin_s(e->arg0)*2.0f,0,cos_s(e->arg0)*2.0f};
    e->timer=360;
    u32 scene=room_effect_scene;
    int size=scene==20 ? 4:(scene==6 || scene==21) ? 6:scene==22 ? 8:0;
    e->offset=(EffectPosition){size ? 40.0f:0,size ? 40.0f+40.0f*size:0,size ? 40.0f:0};
    e->scale.x=size ? 200.0f+40.0f*size:0;
    float distance;
    if (near_angle((u16)e->arg0,0)) distance=e->position.z-e->scale.x;
    else if (near_angle((u16)e->arg0,0x4000)) distance=e->position.x-e->offset.y;
    else if (near_angle((u16)e->arg0,0x8000)) distance=e->position.z-e->offset.z;
    else if (near_angle((u16)e->arg0,0xC000)) distance=e->position.x-e->offset.x;
    else return;
    if (absolute(distance)<=21.0f) { e->timer=0;return; }
    sAdo_OngenTrgStart(AF_EFFECT_PROJECTILE_SOUND,&e->position.x);
    e->specific[0]=0;
}

void af_v3_projectile_mv(RoomEffect *e,void *game) {
    (void)game;
    for (int step=0;step<2 && e->timer>step;++step) {
        integrate(e);
        if (e->position.x<e->offset.x || e->position.z<e->offset.z ||
                e->position.x>e->offset.y || e->position.z>e->scale.x) {
            e->timer=0;e->scale.z=0;break;
        }
        float distances[4]={absolute(e->position.x-e->offset.x),absolute(e->position.z-e->offset.z),
                            absolute(e->position.x-e->offset.y),absolute(e->position.z-e->scale.x)};
        float distance=1000.0f;
        for (int i=0;i<4;++i) if (distances[i]<16.0f) { distance=distances[i];break; }
        if (distance<20.0f) {
            e->scale.z=distance/16.0f;
            if (!e->specific[0]) {
                e->velocity.x*=0.5f;e->velocity.z*=0.5f;e->specific[0]=1;
            }
        } else e->scale.z=1.0f;
    }
    if (e->timer>0) --e->timer;
}

void af_v3_projectile_dw(RoomEffect *e,RoomRigGame *game) {
    if (!game || !game->gfx) return;
    RoomRigGraphics *g=game->gfx;
    void *matrix=particle_matrix(g,0,3);
    if (!matrix) return;
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_RotateY(e->arg0,1);
    Matrix_scale(0.01f,0.01f,e->scale.z*0.01f,1);
    _Matrix_to_Mtx(matrix);osWritebackDCache(matrix,64);
    _texture_z_light_fog_prim(g);
    *g->head++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    *g->head++=(RoomCommand){0xDE000000,AF_EFFECT_PROJECTILE_MODEL};
}
