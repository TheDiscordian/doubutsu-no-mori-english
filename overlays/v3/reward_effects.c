/* Complete Shrine-effect services use the native pool and global light list.
 * The enclosing actor/controller must reset these references before scene teardown.
 */
#include "reward_effects.h"
typedef struct {
    u8 type,pad;
    struct { s16 x,y,z;u8 colour[3],glow;s16 radius; } point;
} RewardLight;
typedef struct RewardLightNode {
    RewardLight *info;
    struct RewardLightNode *prev,*next;
} RewardLightNode;
typedef struct { RewardLightNode *list;u8 environment[12]; } RewardGlobalLight;
extern void Light_point_ct(RewardLight *,s16,s16,s16,u8,u8,u8,s16);
extern RewardLightNode *Global_light_list_new(void *,RewardGlobalLight *,RewardLight *);
extern void Global_light_list_delete(RewardGlobalLight *,RewardLightNode *);
static RewardLight light;
static RewardLightNode *node;
static void *owner;
extern void af_hp_native_sound(u32,xyz_t *);
int af_rw_effect_light_index=-1;
_Static_assert(sizeof(RewardLight)==14,"Native point-light record");
ROOM_CHECK(RewardLight,point,2);
#ifdef __mips__
_Static_assert(sizeof(RewardGlobalLight)==16,"Native global-light record");
#endif

int af_rw_effect_ready(void *game) {
    return af_sky_ready(game) && af_rw_hem_visible() && af_hp_native_ticks>0 && af_hp_native_ticks<=2;
}
void af_rw_effect_sound(u32 word,xyz_t *p) {
    if(p && (word==0x468 || word==0x469))af_hp_native_sound(af_rw_effect_sounds[word-0x468],p);
}
void af_rw_effect_request(int id,xyz_t p,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    if(id>=AF_RW_EFFECT_FIRST && id<AF_RW_EFFECT_FIRST+3 && af_rw_effect_ready(game))
        af_sky_native_clip->request(id,p,priority,angle,game,item,a,b);
}
RoomEffect *af_rw_effect_create(s16 id,xyz_t p,xyz_t *offset,void *game,void *arg,
        u16 item,int priority,s16 a,s16 b) {
    return id>=AF_RW_EFFECT_FIRST && id<AF_RW_EFFECT_FIRST+3 && af_rw_effect_ready(game)?
        af_sky_native_clip->create(id,p,offset,game,arg,item,priority,a,b):0;
}
void af_rw_effect_kill(int id,u16 item) {
    if(id>=AF_RW_EFFECT_FIRST && id<AF_RW_EFFECT_FIRST+3 && af_sky_native_clip && af_sky_native_clip->kill)
        ((void (*)(int,u16))af_sky_native_clip->kill)(id,item);
}
int af_rw_effect_light_reserve(void *game,xyz_t *p,u8 r,u8 g,u8 b,s16 power) {
    if(!game || !p || node || owner)return -1;
    Light_point_ct(&light,(s16)p->x,(s16)p->y,(s16)p->z,r,g,b,power);
    node=Global_light_list_new(game,(RewardGlobalLight *)((u8 *)game+0x1C60),&light);
    if(!node)return -1;
    owner=game;return 0;
}
void af_rw_effect_light_colour(int index,u8 r,u8 g,u8 b) {
    if(index==0 && node && owner) {light.point.colour[0]=r;light.point.colour[1]=g;light.point.colour[2]=b;}
}
int af_rw_effect_light_cancel(int index,void *game) {
    if(index==0 && node && owner==game) {
        Global_light_list_delete((RewardGlobalLight *)((u8 *)game+0x1C60),node);
        node=0;owner=0;
    }
    return -1;
}
void af_rw_effect_reset(void *game) {
    if(owner && owner!=game)return;
    if(node)af_rw_effect_light_cancel(0,game);
    af_rw_effect_light_index=-1;
    int *visible=af_rw_hem_visible();if(visible)*visible=0;
}
