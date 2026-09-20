/* Source planting-completion effect, using the native sparkle and frame rate.
   The original seasonal caller still owns bounce timing and callback cleanup. */
#include "scenery_trees.h"
typedef void (*TreeMakeEffect)(int,TreePosition,int,s16,void *,u16,s16,s16);
extern TreeMakeEffect *af_scenery_effect_clip;
extern void *af_scenery_game;
extern void af_scenery_commit(u32,TreePosition,int);
extern const TreePosition af_v3_tree_sparkle_offsets[4];

static void commit(u32 item,TreePosition pos,int flag,u32 variant) {
    if ((item&65535u)==af_v3_tree_rule.first &&
            af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0 &&
            af_scenery_effect_clip && af_scenery_effect_clip[0] && af_scenery_game) {
        const TreePosition *offset=af_v3_tree_sparkle_offsets+variant;
        TreePosition effect={pos.x+offset->x,pos.y+offset->y,pos.z+offset->z};
        /* Native KIGAE_LIGHT is 87; the donor's 86 is a different native effect.
           Native effect code retains its 15-frame (30-fps) lifetime. */
        af_scenery_effect_clip[0](87,effect,2,0,af_scenery_game,0xffffu,-1,0);
    }
    af_scenery_commit(item,pos,flag);
}
#define COMMIT(n) \
void af_v3_tree_plant_commit##n(u32 item,TreePosition pos,int flag) { commit(item,pos,flag,n); }
COMMIT(0) COMMIT(1) COMMIT(2) COMMIT(3)
