/* Source transforms, colours, scrolling, and complete converted models. Each
 * draw reserves its matrix, tile program, and commands before touching arenas. */
#include "holiday_sky.h"
extern void Matrix_translate(float,float,float,u8),Matrix_scale(float,float,float,u8);
extern void Matrix_RotateY(s16,int),Matrix_RotateZ(s16,int),Matrix_mult(float *,int);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int),_texture_z_light_fog_prim_xlu(void *);
typedef struct { void *matrix;RoomCommand *tiles; } SkyDraw;
static int reserve(RoomRigGame *game,int scrolling,SkyDraw *out) {
    if(!game || !game->gfx)return 0;
    RoomRigGraphics *g=game->gfx;
    uptr head=(uptr)g->xlu_head,tail=(uptr)g->xlu_tail;
    u32 tile_bytes=scrolling?40:0;
    if(!head || (head&7u) || tail<head || tail-head<48u+64u+tile_bytes+15u)return 0;
    uptr matrix=(tail-64u)&~(uptr)15u;
    out->matrix=(void *)matrix;out->tiles=scrolling?(RoomCommand *)(matrix-tile_bytes):0;
    g->xlu_tail=(u8 *)(matrix-tile_bytes);return 1;
}
static void tiles(RoomCommand *out,int x0,int y0,int w0,int h0,int x1,int y1,int w1,int h1) {
    int xs[2]={x0,x1},ys[2]={y0,y1},ws[2]={w0,w1},hs[2]={h0,h1};
    for(u32 i=0;i<2;i++) {
        /* Dolphin doubles its 14-bit coordinates; N64 tile origins use 1/4
         * texels instead of 1/16. Keep signed wrap and image pitch distinct. */
        u32 s=(((u32)xs[i]<<1)&0x3FFFu)>>2,t=(((u32)ys[i]<<1)&0x3FFFu)>>2;
        out[i*2]=(RoomCommand){0xE8000000,0};
        out[i*2+1]=(RoomCommand){0xF2000000|(s<<12)|t,
            (i<<24)|(((s+4u*(ws[i]-1))&4095u)<<12)|((t+4u*(hs[i]-1))&4095u)};
    }
    out[4]=(RoomCommand){0xDF000000,0};osWritebackDCache(out,40);
}
static void matrix(RoomRigGraphics *g,SkyDraw *draw) {
    _Matrix_to_Mtx(draw->matrix);osWritebackDCache(draw->matrix,64);
    _texture_z_light_fog_prim_xlu(g);
    *g->xlu_head++=(RoomCommand){0xDA380003,(u32)(uptr)draw->matrix};
}
void af_sky_moon_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *game=opaque;SkyDraw draw;
    if(!e || !af_sky_ready(game) || (!af_sky_lookat(e->position) && e->state!=2) ||
        !reserve(game,1,&draw))return;
    u32 frame=*(u32 *)((u8 *)game+0x1EA0)*2u;
    tiles(draw.tiles,frame*af_sky_art.moon_x[0],frame*af_sky_art.moon_y[0],
        af_sky_art.moon_width[0],af_sky_art.moon_height[0],
        frame*af_sky_art.moon_x[1],frame*af_sky_art.moon_y[1],
        af_sky_art.moon_width[1],af_sky_art.moon_height[1]);
    Matrix_translate(e->position.x+e->offset.x,e->position.y+e->offset.y,e->position.z+e->offset.z,0);
    Matrix_RotateY(-e->specific[0],1);Matrix_scale(1.075f,1,1,1);
    Matrix_RotateY(e->specific[0],1);Matrix_RotateY(-e->specific[1],1);
    Matrix_scale(1,1,1.075f,1);Matrix_RotateY(e->specific[1],1);Matrix_scale(.049f,1,.049f,1);
    RoomRigGraphics *g=game->gfx;matrix(g,&draw);
    *g->xlu_head++=(RoomCommand){0xFA000028,0xFFFF64AA};
    *g->xlu_head++=(RoomCommand){0xDB060020,(u32)(uptr)draw.tiles};
    *g->xlu_head++=(RoomCommand){0xDE000000,af_sky_art.moon};
}
void af_sky_shooting_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *game=opaque;SkyDraw draw;
    if(!e || !af_sky_ready(game) || !reserve(game,1,&draw))return;
    int elapsed=320-e->timer;
    tiles(draw.tiles,0,-((elapsed-120)*6),8,256,0,0,8,32);
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_RotateY(-e->specific[1],1);Matrix_scale(1.035f,1,1,1);
    Matrix_RotateY(e->specific[1],1);Matrix_RotateY(e->arg1,1);
    Matrix_scale(.01f,.01f,.01f*(e->specific[0]*.01f),1);
    RoomRigGraphics *g=game->gfx;matrix(g,&draw);
    *g->xlu_head++=(RoomCommand){0xDB060024,(u32)(uptr)draw.tiles};
    *g->xlu_head++=(RoomCommand){0xDE000000,af_sky_art.shooting};
}
void af_sky_kira_draw(RoomEffect *e,void *opaque) {
    RoomRigGame *game=opaque;SkyDraw draw;
    if(!e || !af_sky_ready(game) || !reserve(game,0,&draw))return;
    s16 max=42+af_sky_debug(32),counter=max-e->timer,fadeout=max*.87f;
    float alpha=counter<=fadeout ? af_sky_adjust(counter,0,max*.87f,100,150):
        af_sky_adjust(counter,max*.87f,max,150,100);
    /* Convert through an integer before narrowing: direct float->s16 past
     * 32767 is undefined in C, while the donor wraps the angle to 16 bits. */
    s16 angle=(s16)(int)af_sky_adjust(counter,0,max,0,131072);
    Matrix_translate(e->position.x,e->position.y,e->position.z,0);
    Matrix_mult((float *)((u8 *)game+0x1E5C),1);Matrix_RotateZ(angle,1);
    Matrix_scale(e->scale.x,e->scale.y,e->scale.z,1);
    RoomRigGraphics *g=game->gfx;matrix(g,&draw);
    *g->xlu_head++=(RoomCommand){0xFA0000FF,0xFFFFFF00|((u32)(int)alpha&255)};
    *g->xlu_head++=(RoomCommand){0xDB060020,(u32)(uptr)Lib_SegmentedToVirtual((void *)(uptr)af_sky_art.kira_mode)};
    *g->xlu_head++=(RoomCommand){0xDE000000,af_sky_art.kira};
}
