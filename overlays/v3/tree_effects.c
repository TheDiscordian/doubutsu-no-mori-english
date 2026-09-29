/* Native services for the complete generated tree-effect family. */
#include "tree_effects.h"
#include "paged_resource.h"
#include "resource_dma.h"
extern int af_tree_load(void),af_tree_native_term(void);
extern volatile u32 af_tree_native_season;
extern u8 *volatile af_tree_native_owner;
extern u8 *volatile af_tree_native_player;
extern const u16 *tree_rule(u32);
extern int mFI_UtNum2CenterWpos(xyz_t *,int,int);
extern f32 af_tree_unit_height(int,int);
extern int af_v3_tree_player_query(u32,u32);
extern int af_v3_player_selected_equipment(u32),af_carried_category(u32);
const xyz_t ZeroVec={0,0,0};
extern const u32 af_tree_art_pages[40],af_tree_art_crc;
extern int af_tree_dma(void *,u32,u32);
extern u32 af_tree_crc(const void *,u32);
extern void af_tree_fault(const char *,const char *);
static int art_ready;
static int resource_dma(void *dest,u32 source,u32 bytes) {
    return af_v3_resource_read(dest,source,bytes,af_tree_dma);
}

/* The complete AFPG page directory belongs to the CRC-checked startup packet.
 * Validate every cartridge extent before changing the reserved art region. */
static int load_art(void) {
    if(art_ready)return 1;
    if(!af_v3_paged_read((u8 *)af_tree_art,0x24000u,af_tree_art_pages,40u,
            af_tree_art_crc,resource_dma,af_tree_crc))return 0;
    osWritebackDCache((void *)af_tree_art,0x24000u);art_ready=1;return 1;
}

int af_tree_resources(void) {
    if(!af_tree_load())return 0;
    if(load_art())return 1;
    af_tree_fault("V3 tree effects","Invalid complete resource");return 0;
}
int af_tree_ready(GAME *g) {return g && g->graph && room_effect_clip && af_tree_resources();}
int af_tree_term(void) {return af_tree_native_term();}
int af_tree_season(void) {return (int)af_tree_native_season;}
u32 af_tree_frame(GAME *g) {return *(u32 *)((u8 *)g+0x1EA0)*2u;}
s16 af_tree_debug(unsigned int index) {
    /* TAKREG 20/41/50/51 are donor developer offsets, all zero at normal boot.
       There is no matching native debug bank for imported tree coordinates. */
    (void)index;return 0;
}
mFM_field_pal_c *af_tree_palettes(void) {
    static mFM_field_pal_c p;
    unsigned int term=(unsigned int)af_tree_term();
    if(term>=18u)term=0;
    unsigned int i=af_tree_palette_terms[term];
    p.cedar_tree_pal=(u16 *)af_tree_palette_data[0][i];
    p.palm_tree_pal=(u16 *)af_tree_palette_data[1][i];
    p.golden_tree_pal=(u16 *)af_tree_palette_data[2][i];
    return &p;
}
int af_tree_admit(s16 variant) {
    if(variant < -1 || variant>16 || !af_tree_load())return 0;
    if(variant>=13)return af_v3_player_selected_equipment(0x223B)>=0;
    if(variant>=8)return af_carried_category(0x290A)>0;
    if(variant>=4)return af_carried_category(0x2807)>0;
    return 1;
}
int af_tree_collision(xyz_t p) {
    u16 *fg=mFI_GetUnitFG(p);
    if(fg && af_tree_load() && (af_v3_tree_player_query(*fg,0) || af_v3_tree_player_query(*fg,3)))return 1;
    /* Keep the original complete predicate, including native stump cases. Its
       code does not read the actor's resized joint/matrix workspace. */
    u8 *owner=af_tree_native_owner;
    return owner?((int (*)(xyz_t))(owner+0x214))(p):0;
}
void af_tree_player_effect(GAME *g,u16 item,s16 type,int x,int z) {
    const u16 *r=af_tree_load()?tree_rule(item):NULL;
    if(r && af_v3_tree_player_query(item,0)) {
        unsigned int step=(unsigned int)item-r[0];
        int size=step<r[1]?(s16)r[8+step*2+1]:4;
        int base=r[7]==1?3:r[7]==2?7:12;
        s16 variant=(s16)(base+size);
        if(r[7]==2 && item==0x82)variant=12;
        xyz_t p;
        if(size>=1 && size<=4 && af_tree_make_clip && mFI_UtNum2CenterWpos(&p,x,z)) {
            p.y=af_tree_unit_height(x,z);af_tree_make_clip(g,type,variant,&p);
        }
        return;
    }
    u8 *owner=af_tree_native_player;
    if(owner)((void (*)(GAME *,u16,s16,int,int))(owner+0x69A8))(g,item,type,x,z);
}
void af_tree_camera(GAME *g,xyz_t *out) {
    xyz_t *eye=(xyz_t *)((u8 *)g+0x1A60),*center=eye+1;
    f32 distance=search_position_distance(eye,center);
    xyz_t_sub(eye,center,out);
    if(distance>0)xyz_t_mult_v(out,1.0f/distance);
    else *out=(xyz_t){0,0,1};
}
static void request(int id,xyz_t p,int priority,s16 angle,GAME *g,u16 item,s16 a,s16 b) {
    RoomEffectClip *c=room_effect_clip;
    if(c && c->request && (id==120 || id==121 || id==52))c->request(id,p,priority,angle,g,item,a,b);
}
static RoomEffect *create(s16 id,xyz_t p,xyz_t *q,GAME *g,void *arg,u16 item,int priority,s16 a,s16 b) {
    RoomEffectClip *c=room_effect_clip;
    return c && c->create && (id==120 || id==121)?c->create(id,p,q,g,arg,item,priority,a,b):NULL;
}
static void speed(xyz_t *v,f32 power,f32 x,f32 z) {
    RoomEffectClip *c=room_effect_clip;
    if(c && c->unused[2])((void (*)(xyz_t *,f32,f32,f32))c->unused[2])(v,power,x,z);
}
static f32 adjust(s16 t,s16 a,s16 b,f32 x,f32 y) {
    return room_effect_clip->adjust(t,a,b,x,y);
}
const TreeEffectServices af_tree_services={request,create,speed,adjust};
static int space(const void *head,const void *tail,u32 n) {
    uptr h=(uptr)head,t=(uptr)tail;
    return h && !((h|t)&7u) && t>=h && t-h>=n;
}
int af_tree_draw_space(GAME *g) {
    if(!g || !g->graph)return 0;
    GRAPH *p=g->graph;
    /* Three six-matrix actors, complete joint commands, setup, palette changes,
       and three root matrices fit this bound on either native draw stream. */
    return space(p->head,p->tail,2048) && space(p->xlu_head,p->xlu_tail,2048);
}
Mtx *af_tree_alloc(GRAPH *g) {
    uptr p=((uptr)g->tail-sizeof(Mtx))&~(uptr)15u;g->tail=(u8 *)p;
    return (Mtx *)p;
}
