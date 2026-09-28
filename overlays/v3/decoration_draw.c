#include "decoration_draw.h"

static const AFDecorStructureClip structure_clip={af_decor_palette};
static const AFDecorShadowClip shadow_clip={af_decor_shadow};
const __typeof__(af_decor_common) af_decor_common={{&structure_clip,&shadow_clip}};

static int space(const void *head,const void *tail,u32 needed) {
    uptr h=(uptr)head,t=(uptr)tail;
    return h && t && !((h|t)&7) && t>=h && t-h>=needed;
}

int af_decor_draw(ACTOR *actor,GAME *game,u16 name) {
    if (!actor || !game || !game->graph) return 0;
    const AFDecorRecord *row=0;
    for (u32 i=0;i<18;++i) if (af_decor_records[i].source_name==name) { row=af_decor_records+i;break; }
    if (!row || !row->draw || !af_decor_valid((STRUCTURE_ACTOR*)actor,row->owner)) return 0;
    GRAPH *g=game->graph;
    /* The full four-digit draw, its matrices, source callbacks, and shadow
       fit within this bound. Reject before any source draw-state mutation. */
    if (!space(g->opa,g->tail,8192) || !space(g->xlu,g->xlu_tail,1024) ||
        !space(g->shadow,g->shadow_tail,256)) return 0;
    STRUCTURE_ACTOR *a=(STRUCTURE_ACTOR*)actor;
    if (row->skeleton && a->keyframe.skeleton!=(void*)(uptr)row->skeleton) return 0;
    row->draw(actor,game);
    return 1;
}

void *af_decor_alloc(GRAPH *g,u32 size) {
    if (size>8192 || !space(g->opa,g->tail,size+16)) return 0;
    uptr at=((uptr)g->tail-size)&~(uptr)15;
    if (at<(uptr)g->opa+16) return 0;
    g->tail=(u8*)at;
    return (void*)at;
}

Mtx *af_decor_matrix(GRAPH *g) {
    Mtx *m=af_decor_alloc(g,sizeof(Mtx));
    if (m) { native_decor_matrix(m);native_decor_writeback(m,sizeof(Mtx)); }
    return m;
}

int af_decor_collision(ACTOR *actor,u16 name) {
    if (!actor) return 0;
    for (u32 i=0;i<18;++i) if (af_decor_records[i].source_name==name) {
        if (!af_decor_valid((STRUCTURE_ACTOR*)actor,af_decor_records[i].owner)) return 0;
        if (af_decor_records[i].collision) af_decor_records[i].collision(actor);
        return 1;
    }
    return 0;
}

Gfx *af_decor_scroll(GRAPH *g,int t0,u32 x0,u32 y0,int w0,int h0,
                    int t1,u32 x1,u32 y1,int w1,int h1) {
    Gfx *p=af_decor_alloc(g,5*sizeof(Gfx));
    if (!p) return 0;
    u32 x[2]={x0&0x7FF,x1&0x7FF},y[2]={y0&0x7FF,y1&0x7FF};
    int t[2]={t0,t1},w[2]={w0,w1},h[2]={h0,h1};
    for (u32 i=0;i<2;++i) {
        p[i*2]=(Gfx){0xE8000000,0};
        p[i*2+1]=(Gfx){0xF2000000|x[i]<<12|y[i],(u32)t[i]<<24|
            ((x[i]+((u32)w[i]-1)*4)&0xFFF)<<12|((y[i]+((u32)h[i]-1)*4)&0xFFF)};
    }
    p[4]=(Gfx){0xDF000000,0};
    native_decor_writeback(p,5*sizeof(Gfx));
    return p;
}

void af_decor_shadow(GAME *game,bIT_ShadowData_c *s,int type) {
    GRAPH *g=game->graph;
    if (!s || !s->count || s->count>32 || !s->vertices || !s->flags || !s->model) return;
    Vtx *v=af_decor_alloc(g,s->count*sizeof(Vtx));
    Mtx *m=af_decor_matrix(g);
    if (!v || !m || !space(g->shadow,g->shadow_tail,80)) return;
    int shift=(int)(*(float*)((u8*)game+0x1C50)*s->size);
    for (u32 i=0;i<s->count;++i) {
        v[i]=s->vertices[i];
        if (s->flags[i]==1) {
            s16 x=(s16)((u16)v[i].bytes[0]<<8|v[i].bytes[1]);
            u16 adjusted=(u16)(x+shift);v[i].bytes[0]=adjusted>>8;v[i].bytes[1]=adjusted;
        }
    }
    native_decor_writeback(v,s->count*sizeof(Vtx));
    _texture_z_light_fog_prim_shadow(g);
    Gfx *p=g->shadow;
    const u8 *light=(u8*)game+0x1C3A;u8 alpha=((u8*)game)[0x1C54];
    gDPPipeSync(p++);gSPMatrix(p++,m,0);gSPSegment(p++,8,v);
    gDPSetPrimColor(p++,0,alpha,light[0],light[1],light[2],alpha);
    /* Donor type one deliberately draws both terrain-shadow passes. It is
       not the N64 helper's third argument (a structure-bank index). */
    if (type==1) AF_CMD(p++,0xD9000000,0x00210455);
    gSPDisplayList(p++,s->model);
    if (type==1) { AF_CMD(p++,0xD9000000,0x00210445);gSPDisplayList(p++,s->model); }
    AF_CMD(p++,0xD9FFFFAF,0);
    g->shadow=p;
}

void af_decor_rig_draw(GAME *game,cKF_SkeletonInfo_R_c *key,Mtx *matrices,
                      AFDecorBefore before,void *after,void *actor) {
    const AFDecorRecord *row=0;
    for (u32 i=0;i<18;++i)
        if (af_decor_records[i].skeleton==(u32)(uptr)key->skeleton) { row=af_decor_records+i;break; }
    if (!row || !row->rig_base) return;
    u32 old=af_decor_segments[6];
    af_decor_segments[6]=row->rig_base&0x1FFFFFFF;
    GRAPH *g=game->graph;
    gSPSegment(g->opa++,6,(void*)(uptr)row->rig_base);
    gSPSegment(g->xlu++,6,(void*)(uptr)row->rig_base);
    native_decor_rig_draw(game,key,matrices,before,after,actor);
    native_decor_writeback(matrices,key->skeleton->num_shown_joints*sizeof(Mtx));
    af_decor_segments[6]=old;
}
