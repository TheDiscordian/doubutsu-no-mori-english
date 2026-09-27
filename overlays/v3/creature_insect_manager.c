/* Native manager entry for the complete insect population, retaining the
 * original manager as the explicit N64 alternative. No old 20-row buffers
 * are enlarged in place. Constructor reset owns transient cache lifetime.
 */
#include "creature_insect_manager.h"
static SpawnPlan cached;
static unsigned cached_month,cached_time,cached_mask,cached_island,cached_mode,valid;
#ifdef __mips__
const u32 af_v3_insect_spawn_mode=0;
#endif
typedef struct {GAME *game;int bx,bz;} BirthContext;
static float random_value(void *unused) {(void)unused;return fqrand();}

void af_v3_insect_spawn_reset(void) {valid=0;cached.count=0;}

static int create(void *opaque,const InsectBirth *birth) {
    BirthContext *ctx=opaque;
    AfInsectInit init;init.type=(int)birth->actor;init.extra=(int)birth->extra;init.game=ctx->game;
    af_insect_tile_position(&init.position,ctx->bx,ctx->bz,(int)birth->x,(int)birth->z);
    init.position.x+=20.0f;init.position.z+=20.0f;
    if (birth->colony) return af_insect_make_colony(&init,ctx->bx,ctx->bz);
    return af_insect_native_clip && af_insect_native_clip->make && af_insect_native_clip->make(&init,0)!=0;
}
int af_v3_insect_spawn(void *manager,GAME *game) {
    if (!manager || !game) return 0;
    unsigned mode=*(const volatile u32 *)&af_v3_insect_spawn_mode;
    if (mode>1) return 0;
    unsigned selected=(af_v3_creature_profile_byte(1)>>1)|((af_v3_creature_profile_byte(2)&1u)<<7);
    if (!mode && !selected) return af_insect_spawn_original(manager,game);
    if (!af_insect_native_clip || !af_insect_native_clip->make) return 0;
    const int *acre=(const int *)((const u8 *)manager+0x4180);
    if (acre[0]<0 || acre[0]>127 || acre[1]<0 || acre[1]>127) return 0;
    unsigned block=af_insect_block_kind(acre[0],acre[1]);
    if (block&0x400000u) return 0;
    /* The donor checks wild slots and colonies, not the carried/released slot.
     * Native mode retains its original admission rule through the fallback. */
    if (mode && (af_insect_occupied_acre(acre[0],acre[1]) ||
                 af_insect_colony_present(acre[0],acre[1],game))) return 0;
    SpawnDate date={(int)af_insect_rtc[6]*256+af_insect_rtc[7],af_insect_rtc[5],af_insect_rtc[3]};
    int time=af_v3_insect_spawn_time(af_insect_rtc[2]);
    if (time<0 || date.month<1 || date.month>12 || date.day<1 || date.day>31) return 0;
    unsigned island=!!(block&0x200000u);
    if (!valid || cached_month!=(unsigned)date.month || cached_time!=(unsigned)time ||
            cached_mask!=selected || cached_island!=island || cached_mode!=mode) {
        SpawnTerms terms={(unsigned)date.month-1,(unsigned)date.month-1,1.0f};
        if (mode && !island && !af_insect_saved_season(&terms,date,random_value,0)) return 0;
        if (!af_v3_insect_spawn_plan(&cached,af_insect_calendar,af_insect_calendar_bytes,terms,
                                     (unsigned)time,selected,(int)island)) return 0;
        cached_month=(unsigned)date.month;cached_time=(unsigned)time;
        cached_mask=selected;cached_island=island;cached_mode=mode;valid=1;
    }
    InsectHabitat habitat={af_insect_foreground(acre[0],acre[1]),af_insect_deposits(acre[0],acre[1]),
        af_insect_collision_map(acre[0],acre[1]),block,af_insect_weather()};
    SpawnPlan plan;plan.count=cached.count;
    for (unsigned i=0;i<cached.count;i++) plan.rows[i]=cached.rows[i];
    int row=af_v3_insect_spawn_choose(&plan,&habitat,af_insect_rank(),!mode,random_value,0);
    if (row==-2) return af_insect_spawn_original(manager,game);
    if (row<0) return 0;
    BirthContext context={game,acre[0],acre[1]};
    int last=0;
    int count=af_v3_insect_spawn_group(plan.rows+row,&habitat,af_insect_calendar,
        af_insect_calendar_bytes,random_value,create,&context,&last);
    return count>=0 && last;
}
