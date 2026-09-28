/* Event table interactions reuse the complete native player action; only the
 * donor-specific search, refusal, height, and completion are added. */
#include "decoration_actor.h"
extern int af_holiday_item_type(u32),af_holiday_pickup_prior_resolve(u16);
extern int af_holiday_pickup_find(const void*,u16,u32),af_holiday_pickup_title(void);
extern void af_holiday_pickup_demo(int,ACTOR*,void (*)(ACTOR*));
extern void af_holiday_pickup_message(int);
extern u8 *af_holiday_pickup_active;
extern u32 af_holiday_pickup_player_ctor;
static void *native(u32 address) {
    return (void *)(uptr)(af_holiday_pickup_player_ctor-0x808DD748u+address);
}
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
static int enabled(void) {return af_holiday_item_type(0x2530)==47;}
static aHTBL_Clip_c *clip(void) {return af_decor_actor_context.clip.htbl_clip;}
static int same_position(const xyz_t *a,const xyz_t *b) {
    return a && b && a->x==b->x && a->y==b->y && a->z==b->z;
}
int af_holiday_pickup_pocket(u16 item,int condition) {
    if((item!=0 && item!=0x2530) || condition!=0 || !af_holiday_pickup_active || !enabled())return -1;
    return af_holiday_pickup_find(af_holiday_pickup_active,item,condition);
}
int af_holiday_pickup_resolve(u16 source) {
    if(source==0x2530)return enabled()?0x2530:-1;
    return af_holiday_pickup_prior_resolve(source);
}
static void refuse(ACTOR *actor) {
    /* Reuse animation, listen, name suppression, and the yellow text window.
     * Only this callback overrides the message; ordinary refusal is unchanged. */
    FN(0x808C0624u,void,ACTOR*)(actor);
    af_holiday_pickup_message(AF_HOLIDAY_FORK_REFUSAL);
}
int af_holiday_pickup_try(GAME *game) {
    aHTBL_Clip_c *c=clip();
    if(!game || !enabled() || af_holiday_pickup_title()>0 || !c || !c->search_pick_up_item_layer2_proc ||
       c->pickup_counter || c->search_pick_up_item_layer2_proc(game)!=0x2530)return 0;
    int slot=af_holiday_pickup_pocket(0,0);
    if(slot<0) {
        ACTOR *player=af_decor_native_player(game);
        if(player)af_holiday_pickup_demo(9,player,refuse);
        return 0; /* The donor continues the ordinary search after refusal. */
    }
    if(slot>=15)return 0;
    xyz_t pos=c->pickup_pos;
    return FN(0x808C8218u,int,GAME*,int,u16,const xyz_t*,int)(game,slot,0x2530,&pos,0);
}
void af_holiday_pickup_insert(int slot,u16 item,xyz_t *position) {
    aHTBL_Clip_c *c=clip();u8 *owner=af_holiday_pickup_active;
    int fork=enabled() && item==0x2530 && slot>=0 && slot<15 && c &&
        same_position(position,&c->pickup_pos);
    /* This is the actual ordinary pocket insertion, not an early reward.
     * Layer-two clearing is retained; the source controller clears the real
     * foreground fork after its two source updates. */
    FN(0x808B55E8u,void,int,u16,xyz_t*)(slot,item,position);
    if(fork && c==clip() && owner && owner==af_holiday_pickup_active &&
       *(u16 *)(owner+0x14+2*slot)==item && !((*(u32 *)(owner+0x34)>>(2*slot))&3u))c->pickup_counter=2;
}
void af_holiday_pickup_height(xyz_t *position) {
    if(position && enabled())position->y=af_decor_native_ground(*position,0.0f);
}
