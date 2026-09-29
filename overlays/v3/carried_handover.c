/* Use the native discard animation and native inventory transaction. A refused
 * request must not consume the spirits or advance the source conversation. */
#include "carried_event.h"
typedef struct {
    u32 birth,change_master,change_mode;
    u8 request_mode,player_after_mode;u16 item;
    ACTOR *master,*target;
    u8 present,changed,pad[2];ACTOR *actor;u32 rebuild;
} NativeHandover;
extern NativeHandover *volatile af_cw_native_handover;
extern ACTOR *af_cw_native_player_actor(GAME *);
extern int af_cw_native_request_give(GAME *,u16,int,int,int);
extern int af_cw_native_give(void *,u16,int),af_carried_type(u32);
extern u32 af_carried_quantity(u32);
#ifdef __mips__
_Static_assert(sizeof(NativeHandover)==0x24,"Native handover clip width");
_Static_assert(__builtin_offsetof(NativeHandover,master)==0x10,"Native handover owner");
#endif
static NativeHandover *clip(void) {
    NativeHandover *h=af_cw_native_handover;
    return h && h->actor && h->birth && h->change_mode?h:0;
}
ACTOR *af_cw_player_actor(GAME *game) {return game?af_cw_native_player_actor(game):0;}
void *af_cw_handover_master(void) {
    NativeHandover *h=clip();
    /* An absent service is not a successfully finished animation. */
    return h?h->master:(void *)&af_cw_native_handover;
}
int mPlib_request_main_give_type1(GAME *game,u16 item,int mode,int present,int surface) {
    NativeHandover *h=clip();const u8 *player=(const u8 *)af_cw_player_actor(game);
    if(!h || !player || h->master || item!=0x2D28 || af_carried_quantity(item)!=1 ||
       mode!=7 || present || surface || af_cw_player()<0 || af_cw_player()>=4 ||
       !af_cw_private() || *(const int *)(player+0xCF0)!=0x40)return 0;
    ACTOR *npc=*(ACTOR *const *)(player+0xD10);
    if(!npc || npc->npc_id!=0xD0CD || !af_hp_admit(npc,game))return 0;
    return af_cw_native_request_give(game,item,mode,present,surface)==1;
}
int mPr_SetFreePossessionItem(void *player,u16 item,int condition) {
    if(!player || player!=af_cw_private() || af_cw_player()<0 || af_cw_player()>=4 ||
       condition || !item || af_carried_type(item)<=0)return 0;
    return af_cw_native_give(player,item,condition)==1;
}
