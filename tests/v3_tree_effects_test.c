#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_effects.c"
const TreeRule af_v3_tree_rule={.first=0x863,.selected_item=0x223b};
const TreePosition af_v3_tree_sparkle_offsets[4]={{12,27,10},{13,33,10},{13,33,10},{13,33,10}};
static int selected,called,committed,variant,sequence;
static u32 expected_item;
static int expected_flag;
static const TreePosition position={10.5f,-12.0f,50.25f};
static unsigned game;
void *af_scenery_game=&game;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return selected?90:-1; }
static void effect(int kind,TreePosition p,int priority,s16 angle,void *g,u16 item,s16 a,s16 b) {
    const TreePosition *offset=af_v3_tree_sparkle_offsets+variant;
    assert(!sequence++);assert(kind==87 && priority==2 && angle==0 && g==&game);
    assert(item==0xffff && a==-1 && !b);
    assert(p.x==position.x+offset->x && p.y==position.y+offset->y && p.z==position.z+offset->z);
    called++;
}
static TreeMakeEffect clip[1]={effect};
TreeMakeEffect *af_scenery_effect_clip=clip;
void af_scenery_commit(u32 item,TreePosition p,int flag) {
    assert(sequence==called);sequence++;
    assert(item==expected_item && flag==expected_flag && !memcmp(&p,&position,sizeof(p)));
    committed++;
}
int main(void) {
    void (*const entries[4])(u32,TreePosition,int)={af_v3_tree_plant_commit0,af_v3_tree_plant_commit1,
        af_v3_tree_plant_commit2,af_v3_tree_plant_commit3};
    for (variant=0;variant<4;variant++) for (selected=0;selected<2;selected++)
        for (u32 item=0;item<65536;item++) {
            expected_item=item;expected_flag=(int)(item%3)-1;called=committed=sequence=0;
            entries[variant](item,position,expected_flag);
            assert(called==(selected && item==0x863) && committed==1 && sequence==called+1);
        }
    selected=1;variant=0;expected_item=0x863;expected_flag=1;
    for (int missing=0;missing<3;missing++) {
        called=committed=sequence=0;
        af_scenery_effect_clip=missing==0?NULL:clip;clip[0]=missing==1?NULL:effect;
        af_scenery_game=missing==2?NULL:&game;
        entries[0](expected_item,position,expected_flag);assert(!called && committed==1);
    }
    puts("shared planting effect and immutable native commit pass");return 0;
}
