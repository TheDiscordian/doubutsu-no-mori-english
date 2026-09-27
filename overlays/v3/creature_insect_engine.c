/* Native primitive bindings. The linker supplies checked resident functions;
 * actor callback addresses are read from the live, relocated native player. */
#include "creature_insect_engine.h"

extern const xyz_t af_insect_ball;
extern const void *af_insect_demo_clip;
extern const void *af_insect_demo_clip2;
extern int af_insect_player_main(GAME *);

const xyz_t *af_insect_ball_position(void) {return &af_insect_ball;}
int af_insect_demo_active(void) {return af_insect_demo_clip || af_insect_demo_clip2;}
int af_insect_is_flower(mActor_name_t item) {return item>=0x83Cu && item<=0x84Du;}
int af_insect_is_stump(mActor_name_t item) {
    /* Native bg_item_fg_sub uses 1..4 for every original tree family.
     * The shared V3 gold-tree conversion adds the donor's 7B..7E states. */
    return (item>=1 && item<=4) || (item>=0x7B && item<=0x7E);
}
int af_insect_putting_net_away(GAME *game) {return af_insect_player_main(game)==0x2F;}
u32 mCoBG_Wpos2BgAttribute_Original(xyz_t position) {
    const u32 *unit=af_insect_unit(position);
    return unit?*unit&63u:100u;
}
int mCoBG_CheckHole_OrgAttr(u32 attr) {
    return attr<=2 || (attr>=4 && attr<=6) || attr==10 || attr==22 ||
        attr==25 || attr==26 || attr==36 || (attr>=43 && attr<=46) || (attr>=59 && attr<=62);
}
void af_insect_register_catch(PLAYER_ACTOR *player,GAME *game,ACTOR *insect,f32 range) {
    typedef void (*Register)(PLAYER_ACTOR *,GAME *,ACTOR *,int,xyz_t *,f32);
    Register proc=*(Register *)((u8 *)player+0x1230);
    proc(player,game,insect,0,&insect->world.position,range);
}
