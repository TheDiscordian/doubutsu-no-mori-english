/* Bind the whole source calendar to native acre allocation and fish creation.
 * The original manager remains an explicit alternative, not a substituted
 * calendar. Selection is gated by complete creature readiness/profile readers.
 */
#include "creature_spawns.h"
#include "creature_water.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct {u8 actor,x,z,spawn;u32 extra;} SpawnNativeData;
extern int af_spawn_original(void *,void *);
extern int af_spawn_make(void *,SpawnNativeData *,void *);
extern float af_patrol_random(void);
extern int af_spawn_event(int,int),af_spawn_weather(void),af_spawn_rank(void);
extern const unsigned *af_spawn_collision(int,int);
extern unsigned af_v3_creature_profile_byte(unsigned);
extern int af_v3_creature_season(SpawnTerms *,SpawnDate,SpawnRandom,void *);
#ifdef __mips__
#define rtc ((const u8 *)0x80136FBCu)
#define history ((u8 *)0x8013794Cu)
#define history_slot (*(u32 *)0x80137948u)
#define event_area (*(u8 *)0x80136FE1u)
#define calendar ((const u8 *)0x8064D000u)
const u32 af_v3_fish_spawn_mode=0;
#else
extern u8 af_spawn_test_rtc[8],af_spawn_test_history[4],af_spawn_test_event_area;
extern u32 af_spawn_test_history_slot,af_v3_fish_spawn_mode;
extern const u8 *af_spawn_test_calendar;
#define rtc af_spawn_test_rtc
#define history af_spawn_test_history
#define history_slot af_spawn_test_history_slot
#define event_area af_spawn_test_event_area
#define calendar af_spawn_test_calendar
#endif
static float random_value(void *unused) {(void)unused;return af_patrol_random();}

int af_v3_fish_spawn(void *manager,void *game) {
    if (!manager || !game) return 0;
    /* Native mode is deliberately not advertised as supporting added fish yet.
     * The private composer keeps creature choices disabled until both spawning
     * alternatives, icons, and collection consumers are complete. */
    if (*(const volatile u32 *)&af_v3_fish_spawn_mode!=1) return af_spawn_original(manager,game);
    int *acre=(int *)((u8 *)manager+0x4180);
    if (acre[0]<0 || acre[0]>255 || acre[1]<0 || acre[1]>255 || history_slot>1) return 0;
    for (unsigned i=0;i<2;i++) if (history[i]==acre[0] && history[2+i]==acre[1]) return 0;
    const unsigned *collision=af_spawn_collision(acre[0],acre[1]);
    if (!collision) return 0;
    unsigned block=af_water_block(acre[0],acre[1]);
    unsigned water=block&0x800 ? 1 : block&0x80 ? 0 : 2;
    /* The native town has no island/offing fishing scene. Do not pretend the
     * retained source island table implements those absent locations. */
    if (block&0x400000u) return 0;
    SpawnDate date={(int)rtc[6]*256+rtc[7],rtc[5],rtc[3]};
    int time=af_v3_spawn_time(rtc[2]);SpawnTerms terms;
    if (time<0 || !af_v3_creature_season(&terms,date,random_value,0)) return 0;
    if (water==0 && (af_spawn_event(20,1) || af_spawn_event(2,1)) &&
        ((event_area==0 && (block&0x8000)) || (event_area==1 && (block&0x200)) ||
         (event_area==2 && (block&0x100))) && af_patrol_random()<0.75f) water=3;
    unsigned selected=af_v3_creature_profile_byte(0)|(af_v3_creature_profile_byte(1)&1u)<<8;
    SpawnPlan plan;
    if (!af_v3_spawn_plan(&plan,calendar,AF_FISH_CALENDAR_BYTES,water,terms,(unsigned)time,
                          selected,af_spawn_weather()==1)) return 0;
    /* Retain native repeated-acre protection and native actor creation limits. */
    history[history_slot]=(u8)acre[0];history[2+history_slot]=(u8)acre[1];history_slot^=1;
    int pick=af_v3_spawn_pick(&plan,block,af_spawn_rank(),random_value,0);
    if (pick<0) return 0;
    FishWaterBlock context={acre[0],acre[1],collision};SpawnPosition position;
    if (!af_v3_spawn_position(&position,plan.rows[pick].actor,af_v3_water_site,random_value,&context)) return 0;
    SpawnNativeData data={(u8)position.actor,(u8)position.x,(u8)position.z,1,0};
    return af_spawn_make(manager,&data,game);
}
