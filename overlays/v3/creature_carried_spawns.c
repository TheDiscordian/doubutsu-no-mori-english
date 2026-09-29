/* Actual acre-entry dispatch for quest creatures. Ordinary populations keep
 * their installed manager and chosen N64/GameCube policy. The quest uses the
 * complete shared habitat/group algorithms, not an unconditional creation. */
#include "creature_carried.h"
#include "creature_insect_manager.h"
extern int af_holiday_calendar_status(int,int);
extern int af_carried_find_block(int *,int *,u32);

static float random_value(void *unused) {(void)unused;return fqrand();}
typedef struct {GAME *game;int x,z;} BirthContext;
static int create(void *opaque,const InsectBirth *birth) {
    BirthContext *ctx=opaque;AfInsectInit init;
    init.type=(int)birth->actor;init.extra=(int)birth->extra;init.game=ctx->game;
    af_insect_tile_position(&init.position,ctx->x,ctx->z,(int)birth->x,(int)birth->z);
    init.position.x+=20.0f;init.position.z+=20.0f;
    return af_insect_native_clip->make(&init,0)!=0;
}
static int match(const AfSpiritCommon *common,int x,int z) {
    for(unsigned i=0;i<5;i++)
        if(common->hitodama_block_data.block_x[i]==x &&
           common->hitodama_block_data.block_z[i]==z)return 1;
    return 0;
}
static int countdown(AfSpiritCommon *common,int x,int z) {
    int lake_x,lake_z;
    /* Native countdown is event 6. The shared observer aliases its imported
     * owner when the GameCube calendar is selected. ACTIVE is bit zero. */
    if(!af_holiday_calendar_status(6,1) ||
       !af_carried_find_block(&lake_x,&lake_z,0x8000u) || x!=lake_x || z!=lake_z)return 0;
    for(unsigned i=0;i<5;i++) {
        if(common->hitodama_block_data.block_x[i]!=lake_x ||
           common->hitodama_block_data.block_z[i]!=lake_z)continue;
        int bx,bz,duplicate;
        /* Preserve the donor's random draw order and its 0/2/4 duplicate
         * check, including its avoidance of the whole lake row and column. */
        do {
            do {bx=1+(int)(fqrand()*5.0f);bz=1+(int)(fqrand()*5.0f);} while(bx==lake_x);
            duplicate=0;
            for(unsigned j=0;j<5;j+=2)
                if(common->hitodama_block_data.block_x[j]==bx &&
                   common->hitodama_block_data.block_z[j]==bz)duplicate=1;
        } while(bz==lake_z || duplicate);
        common->hitodama_block_data.block_x[i]=(u8)bx;
        common->hitodama_block_data.block_z[i]=(u8)bz;
        return 1;
    }
    return 0;
}
int af_carried_insect_spawn(void *manager,GAME *game) {
    if(!manager || !game)return 0;
    AfSpiritCommon *common=af_carried_spirit_common();
    if(!af_carried_creature_enabled(40) || !af_carried_spirit_running() ||
       !common || !(common->flags&0x4000u))return af_v3_insect_spawn(manager,game);
    const int *acre=(const int *)((const u8 *)manager+0x4180);
    if(acre[0]<0 || acre[0]>127 || acre[1]<0 || acre[1]>127)return 0;
    unsigned block=af_insect_block_kind(acre[0],acre[1]);
    if(block&0x200000u || !match(common,acre[0],acre[1]))return af_v3_insect_spawn(manager,game);
    /* Source checks existing wild insects/colonies before changing quest
     * acres. The released/held slot does not suppress a new wild creature. */
    if(block&0x400000u || af_insect_occupied_acre(acre[0],acre[1]) ||
       af_insect_colony_present(acre[0],acre[1],game))return 0;
    if(countdown(common,acre[0],acre[1]))
        return af_v3_insect_spawn(manager,game);
    if(!af_insect_native_clip || !af_insect_native_clip->make)return 0;
    InsectHabitat habitat={af_insect_foreground(acre[0],acre[1]),af_insect_deposits(acre[0],acre[1]),
        af_insect_collision_map(acre[0],acre[1]),block,af_insect_weather()};
    SpawnPlan plan={1,{{40,3,100.0f}}};
    int row=af_v3_insect_spawn_choose(&plan,&habitat,af_insect_rank(),0,random_value,0);
    if(row<0)return 0;
    BirthContext ctx={game,acre[0],acre[1]};int last=0;
    int count=af_v3_insect_spawn_group(plan.rows+row,&habitat,af_insect_calendar,
        af_insect_calendar_bytes,random_value,create,&ctx,&last);
    return count>=0 && last;
}
