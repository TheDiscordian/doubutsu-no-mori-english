/* Reuse save-device doubles; run only the connected changed state/save path. */
#define main retained_console_tests
#include "v3_console_storage_test.c"
#undef main
#undef state
#include "../overlays/v3/holiday_state.h"
#include "../overlays/v3/holiday_native.h"
#include "../overlays/v3/npc_registry.h"
#include "holiday-state-data.h"
AFDiary af_diary_storage;
u32 af_diary_guard[4];
volatile u8 af_holiday_rtc[8]={0,0,19,1,0,1,7,234};
static u32 rng_calls;
float af_holiday_random_native(void) {rng_calls++;return 0.5f;}
int af_holiday_state_lunar(AFDiaryDate *out,const AFDiaryDate *in) {
    CHECK(in->year>=2000 && in->year<=2032 && in->month==8 && in->day==15);
    *out=(AFDiaryDate){in->year,9,15};return 1; /* Native lunar conversion is doubled. */
}
extern int af_old_compress_diary(u8 *,u32,const u8 *,u32,const u8 *,u32,const AFDiary *,u32 *,u32);
extern int af_old_expand_diary(const u8 *,u32,u8 *,u32);
static u8 expanded[AF_CZ_DIARY_RAW];
static AFDiary copy,legacy,staging;
static AFDiaryDraft draft;
static u8 widths[256];
static int preflight(void *c,const AFDiary *d) {(void)c;return af_v3_diary_preflight(d);}
/* Mutable host storage observed through the native read-only table symbol. */
AFNpcExtras calendar_extras;
extern const AFNpcExtras af_v3_npc_extras __attribute__((alias("calendar_extras")));
AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
u8 af_holiday_native_index[128];
u32 af_holiday_native_count;
static u32 previous_calls;
int af_holiday_calendar_previous(void) {previous_calls++;return 7;}
static void calendar_path(void) {
    memset(af_holiday_native_index,255,sizeof(af_holiday_native_index));
    for(u32 i=0;i<AF_HN_DAYS;i++)af_holiday_native_days[i].type=~0u;
    af_holiday_native_days[0]=(AFHolidayNativeDay){70,1,0x601,0x831,AF_HE_SHOW|AF_HE_RUN,0x1234};
    af_holiday_native_index[70]=0;af_holiday_native_count=1;
    AFHolidayNativeDay camper=af_holiday_native_days[0];
    calendar_extras=(AFNpcExtras){.magic=AF_NPC_EXTRA_MAGIC,.version=1,.count=1,.stride=44,
        .rows={{.name=0xD090,.profile=0xCC}}};
    copy=*af_v3_diary_data();u32 calls=rng_calls;
    CHECK(af_holiday_calendar_before_cleanup()==7 && previous_calls==1);
    CHECK(af_holiday_native_count==1 && rng_calls==calls && !memcmp(&copy,af_v3_diary_data(),sizeof(copy)));
    calendar_extras.rows[0].flags=3;af_holiday_rtc[5]=4;af_holiday_rtc[3]=22;
    CHECK(af_holiday_calendar_update()>0 && af_holiday_native_count>1);
    CHECK(!memcmp(&camper,&af_holiday_native_days[0],sizeof(camper)));
    CHECK(af_holiday_native_current()==255); /* Only the native manager sets RUN. */
    u32 count=af_holiday_native_count;
    CHECK(af_holiday_calendar_before_cleanup()==7 && previous_calls==2 && af_holiday_native_count==count);
    af_holiday_rtc[2]=24;CHECK(af_holiday_calendar_update()==-1 && af_holiday_native_count==count);
    af_holiday_rtc[2]=19;calendar_extras.stride=45;CHECK(af_holiday_calendar_update()==-1);
    calendar_extras.stride=44;calendar_extras.rows[0].flags=0;
    af_holiday_rtc[5]=1;af_holiday_rtc[3]=1;af_diary_reset(af_v3_diary_data());rng_calls=0;
}

static void state_paths(void) {
    AFDiary *d=af_v3_diary_data();
    CHECK(d->bytes[5]==2 && !d->bytes[6]);
    CHECK(!af_holiday_state_switch_on(d,(AFDiaryDate){2026,1,1},0));
    CHECK(!af_holiday_state_complete(d,(AFDiaryDate){2026,1,1},0));
    CHECK(af_diary_valid(d));
    for(u32 random=0;random<30;random++) {
        af_diary_reset(d);CHECK(af_holiday_state_init(d,random));
        CHECK(d->bytes[6]==random+1+(random>=3));CHECK(d->bytes[6]!=4);
    }
    af_diary_reset(d);AFHolidayNpc npc={0};AFHolidayEventWorld world;
    CHECK(af_holiday_npc_event_world(&npc,&world));CHECK(d->bytes[6]==17 && rng_calls==1);
    CHECK(af_holiday_npc_event_world(&npc,&world) && rng_calls==1);
    CHECK(world.dates.town_day==17 && world.dates.harvest_month==9 && world.dates.harvest_day==26);
    for(u32 year=2000;year<=2032;year++) {
        AFDiaryDates dates;CHECK(af_holiday_state_dates(d,year,&dates));
        if(year>=2002 && year<=2030)CHECK(dates.harvest_month==af_holiday_harvest_days[(year-2002)*2] &&
            dates.harvest_day==af_holiday_harvest_days[(year-2002)*2+1]);
    }
    CHECK(!af_holiday_state_dates(d,1999,&world.dates));
    CHECK(!af_holiday_state_dates(d,2033,&world.dates));
    for(u32 month=1;month<=2;month++)for(u32 player=0;player<4;player++) {
        AFDiaryDate date={2026,month,1};CHECK(af_holiday_state_start(d,date,player));
        CHECK(af_holiday_state_period(d,date)==0 && af_holiday_state_after(d,date)==1);
        CHECK(!af_holiday_state_available(d,date));
        for(u32 day=2;day<=8;day++) {
            date.day=day;CHECK(af_holiday_state_period(d,date)==1);
            CHECK(af_holiday_state_day(d,date)==(int)day-2);
            CHECK(!af_holiday_state_enter(d,date,17,player,0));
            CHECK(!af_holiday_state_enter(d,date,22,player,0));
            CHECK(!af_holiday_state_enter(d,date,19,4,0));
            CHECK(!af_holiday_state_enter(d,date,19,player,1));
            CHECK(af_holiday_state_enter(d,date,19,player,0));
            CHECK(!af_holiday_state_switch_check(d,date,6));
            CHECK(af_holiday_state_switch_check(d,date,5));
            CHECK(af_holiday_state_switch_on(d,date,player));
            CHECK(af_holiday_state_switch_check(d,date,6));
            CHECK(!af_holiday_state_enter(d,date,19,player,0));
        }
        date.day=9;CHECK(af_holiday_state_period(d,date)==2);
        CHECK(af_holiday_state_check(d,date,player)==(month==1?1:3));
        CHECK(af_holiday_state_check(d,date,4)==0);
        CHECK(af_holiday_state_complete(d,date,player));CHECK(af_holiday_state_check(d,date,player)==0);
        CHECK(d->bytes[14]==(1u<<player));
        date.day=18;CHECK(af_holiday_state_period(d,date)==2);
        date.day=19;CHECK(af_holiday_state_available(d,date));
        CHECK(!d->bytes[11] && !d->bytes[12] && !d->bytes[13] && !d->bytes[14]);
    }
    CHECK(af_holiday_state_start(d,(AFDiaryDate){2024,2,28},2));
    CHECK(af_holiday_state_day(d,(AFDiaryDate){2024,3,1})==1);
    CHECK(af_holiday_state_available(d,(AFDiaryDate){2024,2,27}) && !d->bytes[11]);
    CHECK(af_holiday_state_start(d,(AFDiaryDate){2026,1,1},1));
    CHECK(af_holiday_state_check(d,(AFDiaryDate){2026,1,9},1)==2);
    npc.world.player=3;af_holiday_rtc[5]=2;
    world.lighthouse_start(&npc);CHECK(!npc.failed && d->bytes[10]==2 && d->bytes[13]==8);
    CHECK(world.lighthouse_after(&npc)==1);
    CHECK(af_holiday_state_switch_on(d,(AFDiaryDate){2026,2,2},1));
    CHECK(af_holiday_state_switch_on(d,(AFDiaryDate){2026,2,3},3));
    AFHolidayClock clock;CHECK(af_holiday_state_clock(d,(const u8 *)af_holiday_rtc,0,&clock));
    CHECK(clock.special.town_day==17 && !clock.vacation_available && clock.hour==19);
    CHECK(clock.vernal_day==20 && clock.autumnal_day==23);
    af_holiday_rtc[3]=20;copy=*d;
    CHECK(af_holiday_state_clock(d,(const u8 *)af_holiday_rtc,1,&clock));
    CHECK(!memcmp(&copy,d,sizeof(copy)) && !clock.vacation_available);
    for(u32 i=0;i<16;i++) {
        copy=*d;copy.bytes[14]=i;CHECK(af_diary_valid(&copy));
    }
    copy=*d;copy.bytes[14]=16;CHECK(!af_diary_valid(&copy));
    copy=*d;copy.bytes[6]=4;CHECK(!af_diary_valid(&copy));
}

int main(void) {
    init();fill_console();calendar_path();state_paths();memset(widths,6,sizeof(widths));
    for(u32 p=0;p<4;p++) {
        CHECK(af_diary_begin(&draft,af_v3_diary_data(),p,p,p,widths)==1);
        CHECK(af_diary_command(&draft,8,'A'+p,widths)==1);
        CHECK(af_diary_commit(af_v3_diary_data(),&draft,&staging,widths,preflight,0)==1);
    }
    copy=af_diary_storage;CHECK(af_v3_save_sync()==0 && erases==1 && writes==512);
    memcpy(saved,chip,65536);CHECK(saved[0xF985]==12);
    CHECK(af_old_expand_diary(saved,65536,expanded,sizeof(expanded))==AF_CZ_FORMAT);
    CHECK(af_v3_save_reset()==1 && af_v3_save_read(bank,0)==1);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(&copy,&af_diary_storage,sizeof(copy)));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    CHECK(af_v3_save_expand_diary(saved,65536,expanded,sizeof(expanded))==0);
    /* Valid v11 pages migrate; probes do not commit, and header/version
     * mismatches cannot be misinterpreted as older saves. */
    legacy=copy;legacy.bytes[5]=1;memset(legacy.bytes+6,0,10);
    CHECK(af_old_compress_diary(bank,65536,expanded,65536,console_before,6528,&legacy,
        af_console_hash,AF_CZ_WORK_BYTES)>0 && bank[0xF985]==11);
    CHECK(af_v3_save_check(bank,65536,af_save_current,0)>0);
    CHECK(!memcmp(&copy,&af_diary_storage,sizeof(copy)));
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);legacy.bytes[5]=2;
    CHECK(!memcmp(&legacy,&af_diary_storage,sizeof(legacy)));
    CHECK(af_old_compress_diary(bank,65536,expanded,65536,console_before,6528,&copy,
        af_console_hash,AF_CZ_WORK_BYTES)>0);
    CHECK(af_v3_save_check(bank,65536,af_save_current,0)==AF_SAVE_FORMAT);
    af_diary_storage=copy;af_v3_console_player_clear(af_console_players+0xBD0);
    CHECK(af_diary_storage.bytes[13]==(copy.bytes[13]&~32u));
    CHECK(af_diary_storage.bytes[6]==copy.bytes[6] && af_diary_storage.bytes[12]==copy.bytes[12]);
    CHECK(af_diary_page(&af_diary_storage,1,1,1)[0]==32);
    for(u32 p=0;p<4;p++)if(p!=1)CHECK(af_diary_page(&af_diary_storage,p,p,p)[0]=='A'+p);
    memcpy(bank,saved,65536);bank[400]^=1;legacy=af_diary_storage;
    CHECK(af_v3_save_check(bank,65536,af_save_current,0)<0);
    CHECK(!memcmp(&legacy,&af_diary_storage,sizeof(legacy)) && erases==1 && writes==512);
    printf("%u connected holiday/save assertions: native-calendar adapter/selection, date providers, quest boundaries, all players, format-12 reload, format-11 migration, old-reader rejection, and player clear pass. Native I/O is doubled.\n",assertions);
    return 0;
}
