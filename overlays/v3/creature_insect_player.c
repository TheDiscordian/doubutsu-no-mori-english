/* Shared player impact notifications for the complete imported insect set. */
#include "creature_insect_player.h"
#ifdef __mips__
void *af_insect_player_resolve(u32 address) {
    if (address>=0x808B2D50u)
        address+=*(u32 *)0x80143900u-0x808DD748u;
    return (void *)address;
}
#else
void *af_insect_player_resolve(u32 address) {return af_test_insect_player_resolve(address);}
#endif
#define FN(a,r,...) ((r (*)(__VA_ARGS__))af_insect_player_resolve(a))

static void impact(void *actor,GAME *game,int left,int right,int action,float frame) {
    /* These three calls are already inside their native SearchAnimation
     * changed-frame branches. Keep all original effects/sounds/footprints and
     * use the actual native frame-crossing helper, including loop/reverse rules.
     * The target is the action's target position, not the player's own tile. */
    FN(0x808B9594u,void,void *,GAME *,int,int)(actor,game,left,right);
    if (FN(0x808B5844u,int,void *,float)((u8 *)actor+0x174,frame)) {
        int x=-1,z=-1;
        xyz_t position=*(xyz_t *)((u8 *)actor+0xD10);
        if (mFI_Wpos2UtNum(&x,&z,position)) af_v3_insect_event(action,x,z);
    }
}
void af_insect_player_axe(void *actor,GAME *game,int left,int right) {
    impact(actor,game,left,right,aINS_PL_ACT_REFLECT_AXE,15.0f);
}
void af_insect_player_rock(void *actor,GAME *game,int left,int right) {
    impact(actor,game,left,right,aINS_PL_ACT_REFLECT_SCOOP,13.0f);
}
void af_insect_player_dig(void *actor,GAME *game,int left,int right) {
    impact(actor,game,left,right,aINS_PL_ACT_DIG_SCOOP,14.0f);
}
int af_insect_player_tree(u32 item,int x,int z) {
    /* All four seasonal owners reach this point only at the actual fruit-drop
     * event. Fruit, money, furniture, bees, and immature trees do not release
     * hidden insects. Keep the existing optional gold-tree bee selection. */
    int bee=FN(af_insect_tree_bee_query,int,u32)(item);
    item&=0xFFFF;
    if (item==0x804 || item==0x861 || item==0x868)
        af_v3_insect_event(aINS_PL_ACT_SHAKE_TREE,x,z);
    return bee;
}
