#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/console_storage.h"
#include "../overlays/v3/save_runtime.h"
typedef unsigned char u8;
typedef unsigned int u32;
struct AfSaveRuntime af_save_runtime;
struct AFConsoleStorage af_console_storage;
u8 af_save_current[AF_SAVE_PROFILE],af_save_live[AF_SAVE_PAYLOAD];
u8 af_console_scratch[AF_CZ_RAW+16],af_console_players[4*0xBD0];
u32 af_console_hash[AF_CZ_HASH_WORDS+4],af_console_scratch_guard[4],af_console_hash_guard[4];
static u8 chip[131072],allocation[65536],bank[65536],saved[65536],town_before[AF_SAVE_PAYLOAD];
static u8 console_before[6528],decoded[AF_CZ_RAW],working_before[AF_SAVE_STATE];
static u32 erases,writes,clears,reads;
static jmp_buf halted;
static unsigned assertions;
#define CHECK(x) do {assert(x);assertions++;} while(0)
extern int af_console_canonical_check(const u8 *,u32,const u8 *,u8 *);
extern int af_console_canonical_pack(u8 *,u32,const u8 *);
u32 af_v3_surface_profile_byte(u32 i) {(void)i;return 0;}
#ifdef AF_V3_CREATURE_PROFILE
#include "../overlays/v3/creature_spawns.h"
#define af_creature_test_state af_save_runtime
#include "../overlays/v3/creature_save.c"
static u32 creature_mask=0x1FFFFu;
int af_creature_item_type(u32 item) {
    u32 index=item<0x2D00 ? item-0x2320 : item-0x2D20+9;
    return index<17 && (creature_mask&(1u<<index)) ? (index<9 ? 8 : 18) : 0;
}
static unsigned random_calls;
static float season_random(void *ctx) {(void)ctx;random_calls++;return 0.25f;}
extern int af_console_canonical_collect(u8 *,u32,u32,u32);
extern int af_legacy_pack(u8 *,u32,const u8 *),af_legacy_check(const u8 *,u32,const u8 *,u8 *);
extern int af_legacy_compress(u8 *,u32,const u8 *,u32,const u8 *,u32,u32 *,u32);
#define DISK_FORMAT 7
#ifdef AF_V3_INSECT_SEASONS
#include "../overlays/v3/creature_insect_save.c"
extern int af_fish_canonical_pack(u8 *,u32,const u8 *),af_fish_canonical_check(const u8 *,u32,const u8 *,u8 *);
extern int af_fish_compress(u8 *,u32,const u8 *,u32,const u8 *,u32,u32 *,u32);
extern int af_fish_expand(const u8 *,u32,u8 *,u32);
#undef DISK_FORMAT
#define DISK_FORMAT 9
#endif
#else
#define DISK_FORMAT 5
#endif
void af_save_copy(const void *src,void *dst,u32 n) {memcpy(dst,src,n);}
u32 af_save_sum(const u8 *p,u32 n) {
    u32 s=0;for(u32 i=0;i<n;i+=2)s+=((u32)p[i]<<8)|p[i+1];return s&65535;
}
void af_save_header(u8 *p) {
    memcpy(p+4,"NAFJ",4);memcpy(p+8,af_save_live+0x2F68,2);memset(p+10,0x12,8);
}
u8 *af_save_allocate(u32 n) {CHECK(n==65536);return allocation;}
void af_save_release(void *p) {CHECK(p==allocation);}
int af_save_erase(void) {erases++;memset(chip,0xFF,sizeof(chip));return 0;}
int af_save_write_page(const u8 *p,u32 page) {
    CHECK(page<512 && p==allocation+page*128);writes++;memcpy(chip+page*128,p,128);return 0;
}
int af_v3_original_save_read(u8 *p,u32 page) {
    CHECK(page==0 || page==512);reads++;memcpy(p,chip+page*128,65536);return 1;
}
void af_v3_original_save_clear(u8 *p) {memset(p+4,0xFF,6);memset(p+10,0,10);}
void af_console_original_clear(u8 *p) {CHECK(p>=af_console_players && p<af_console_players+sizeof(af_console_players));clears++;}
void af_save_halt(int reason) {longjmp(halted,-reason);}
static void init(void) {
    memset(af_save_current,0,AF_SAVE_PROFILE);af_save_current[29]=0x24;af_save_current[49]=2;
    memset(af_save_live,0x53,AF_SAVE_PAYLOAD);af_save_live[0x2F68]=0x30;af_save_live[0x2F69]=1;
    CHECK(af_v3_save_reset()==1);CHECK(af_v3_console_storage_valid());
    for(u32 i=0;i<6528;i++)CHECK(!af_console_storage.players[i]);
    af_save_runtime.working[AF_SAVE_PROFILE+2*128+17]=2;
}
static void fill_console(void) {
    u8 *p=af_v3_console_player_data();u32 value=1;
    for(u32 i=0;i<6528;i++){value=value*1664525u+1013904223u;p[i]=value>>24;}
    memcpy(console_before,p,6528);
}
int main(void) {
    init();fill_console();memcpy(town_before,af_save_live,AF_SAVE_PAYLOAD);
#ifdef AF_V3_CREATURE_PROFILE
    CHECK(AF_SAVE_STATE==1232 && sizeof(af_save_runtime)==1264);
    for(u32 p=0;p<4;p++)for(u32 i=0;i<17;i++) {
        u32 item=i<9 ? 0x2320+i : 0x2D20+i-9;
        CHECK(af_console_canonical_collect(af_save_runtime.working,p,item,0)==0);
        CHECK(af_console_canonical_collect(af_save_runtime.working,p,item,1)==1);
    }
    SpawnTerms terms;SpawnDate date={2006,1,14};
    CHECK(af_v3_creature_season(&terms,date,season_random,NULL)==1);
    CHECK(random_calls==1 && terms.next==1);
    CHECK(af_v3_creature_season(&terms,date,season_random,NULL)==1 && random_calls==1);
#ifdef AF_V3_INSECT_SEASONS
    CHECK(af_insect_saved_season(&terms,date,season_random,NULL)==1 && random_calls==2);
    CHECK(terms.current==0 && terms.next==0 && terms.rate==1.0f);
    CHECK(af_save_runtime.working[AF_SAVE_INSECT_SEASON_OFFSET]==1);
    CHECK(af_insect_saved_season(&terms,date,season_random,NULL)==1 && random_calls==2);
#endif
    u8 creatures_before[32];memcpy(creatures_before,af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,32);
#endif
    memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);af_v3_save_prepare(bank);
    CHECK(bank[AF_SAVE_PAYLOAD+5]==DISK_FORMAT && af_save_sum(bank,AF_SAVE_PAYLOAD)==0);
    memcpy(saved,bank,65536);memcpy(chip,bank,65536);memcpy(chip+65536,bank,65536);
    CHECK(af_v3_save_expand(bank,65536,decoded,AF_CZ_RAW)==0);
    CHECK(memcmp(decoded+20,town_before+20,AF_SAVE_PAYLOAD-20)==0);
    CHECK(memcmp(decoded+65536,console_before,6528)==0);
    CHECK(erases==0 && writes==0);
    // Probe both banks without committing any town, catalogue, or console state.
    memset(af_console_storage.players,0x31,6528);
    memcpy(working_before,af_save_runtime.working,AF_SAVE_STATE);
    CHECK(af_v3_save_read(bank,0)==1);CHECK(af_v3_save_read(bank,512)==1);
    for(u32 i=0;i<6528;i++)CHECK(af_console_storage.players[i]==0x31);
    CHECK(!memcmp(working_before,af_save_runtime.working,AF_SAVE_STATE));
    CHECK(!memcmp(town_before,af_save_live,AF_SAVE_PAYLOAD));
    CHECK(af_v3_save_reset()==1);memset(af_save_live,0,AF_SAVE_PAYLOAD);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(decoded,af_save_live,AF_SAVE_PAYLOAD));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    CHECK(af_save_runtime.working[AF_SAVE_PROFILE+2*128+17]==2);
    CHECK(af_save_runtime.ready && af_save_runtime.town==0x3001);
#ifdef AF_V3_CREATURE_PROFILE
    CHECK(!memcmp(creatures_before,af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,32));
    unsigned calls_before=random_calls;
    CHECK(af_v3_creature_season(&terms,date,season_random,NULL)==1 && random_calls==calls_before);
#ifdef AF_V3_INSECT_SEASONS
    CHECK(af_insect_saved_season(&terms,date,season_random,NULL)==1 && random_calls==calls_before);
    CHECK(af_fish_expand(bank,65536,decoded,AF_CZ_RAW)==AF_CZ_FORMAT);
    CHECK(af_fish_canonical_check(decoded,65536,af_save_current,NULL)==AF_SAVE_FORMAT);
    /* Migrate the complete preceding creature bank, including all caught
     * species, fish season, and four console records. Only insect state is new. */
    u8 fish_state[AF_SAVE_STATE],fish_canonical[65536],fish_disk[65536],fish_migrated[AF_SAVE_STATE];
    memcpy(fish_state,af_save_runtime.working,AF_SAVE_STATE);
    memset(fish_state+AF_SAVE_INSECT_SEASON_OFFSET,0,3);
    memcpy(fish_canonical,decoded,65536);
    CHECK(af_fish_canonical_pack(fish_canonical,65536,fish_state)==AF_SAVE_OK);
    CHECK(af_fish_compress(fish_disk,65536,fish_canonical,65536,console_before,6528,
                          af_console_hash,AF_CZ_WORK_BYTES)>0);
    CHECK(af_v3_save_check(fish_disk,65536,af_save_current,fish_migrated)==AF_SAVE_OK);
    CHECK(!memcmp(fish_state,fish_migrated,AF_SAVE_STATE));
    /* Every newly assigned byte and the remaining padding is validated before
     * changing output. Invalid dates and RNG cannot change saved seasons. */
    const unsigned offsets[]={23,24,25,26,31};const u8 invalid[]={12,6,2,1,1};
    for(unsigned i=0;i<sizeof(invalid);i++) {
        memcpy(fish_state,af_save_runtime.working,AF_SAVE_STATE);
        fish_state[AF_SAVE_CREATURE_OFFSET+offsets[i]]=invalid[i];
        memcpy(fish_canonical,decoded,65536);
        CHECK(af_console_canonical_pack(fish_canonical,65536,fish_state)==AF_SAVE_CATALOGUE_INVALID);
        CHECK(!memcmp(fish_canonical,decoded,65536));
    }
    CHECK(!af_insect_saved_season(&terms,(SpawnDate){2006,2,30},season_random,NULL));
    CHECK(!memcmp(creatures_before,af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,32));
    /* Month/year transitions use their own state, never the fish bytes. */
    CHECK(af_insect_saved_season(&terms,(SpawnDate){2006,12,29},season_random,NULL));
    CHECK(af_insect_saved_season(&terms,(SpawnDate){2007,1,1},season_random,NULL));
    CHECK(!memcmp(creatures_before,af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,23));
    memcpy(af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,creatures_before,32);
#endif
    creature_mask=0xFFFF;
    CHECK(af_v3_save_check(bank,65536,af_save_current,NULL)==AF_SAVE_PROFILE_MISSING);
    creature_mask=0x1FFFF;
    /* Generate a prior-format bank with the same codec built without the new
     * extension. This tests migration, not a replay of an old game build. */
    u8 legacy_canonical[65536],legacy_disk[65536],migrated[AF_SAVE_STATE];
    u8 legacy_state[AF_SAVE_STATE];memset(legacy_state,0x52,sizeof(legacy_state));
    CHECK(af_legacy_check(decoded,65536,af_save_current,legacy_state)==AF_SAVE_FORMAT);
    for(u32 i=0;i<AF_SAVE_STATE;i++)CHECK(legacy_state[i]==0x52);
    memcpy(legacy_canonical,decoded,65536);
    CHECK(af_legacy_pack(legacy_canonical,65536,af_save_runtime.working)==AF_SAVE_OK);
    CHECK(af_legacy_compress(legacy_disk,65536,legacy_canonical,65536,console_before,6528,
                            af_console_hash,AF_CZ_WORK_BYTES)>0);
    CHECK(af_v3_save_check(legacy_disk,65536,af_save_current,migrated)==AF_SAVE_OK);
    CHECK(!memcmp(migrated,af_save_runtime.working,AF_SAVE_CREATURE_OFFSET));
    for(u32 i=4;i<32;i++)CHECK(migrated[AF_SAVE_CREATURE_OFFSET+i]==0);
    memcpy(working_before,af_save_runtime.working,AF_SAVE_STATE);
    working_before[AF_SAVE_CREATURE_OFFSET+21]=6;
    memcpy(legacy_canonical,bank,65536);
    CHECK(af_console_canonical_pack(legacy_canonical,65536,working_before)==AF_SAVE_CATALOGUE_INVALID);
    CHECK(!memcmp(legacy_canonical,bank,65536));
#endif
    // Player deletion preserves every other console record and the prior chain.
    for(u32 player=0;player<4;player++) {
        memcpy(af_console_storage.players,console_before,6528);
#ifdef AF_V3_CREATURE_PROFILE
        memcpy(af_save_runtime.working+AF_SAVE_CREATURE_OFFSET,creatures_before,32);
#endif
        af_v3_console_player_clear(af_console_players+player*0xBD0);
        for(u32 other=0;other<4;other++)for(u32 i=0;i<1632;i++)
            CHECK(af_console_storage.players[other*1632+i]==(other==player?0:console_before[other*1632+i]));
#ifdef AF_V3_CREATURE_PROFILE
        for(u32 other=0;other<4;other++)for(u32 i=0;i<4;i++)
            CHECK(af_save_runtime.working[AF_SAVE_CREATURE_OFFSET+4+other*4+i]==
                (other==player?0:creatures_before[4+other*4+i]));
        CHECK(!memcmp(af_save_runtime.working+AF_SAVE_CREATURE_OFFSET+20,creatures_before+20,12));
#endif
    }
    CHECK(clears==4);
    // Existing synchronous save path writes only after complete preparation.
    memcpy(af_console_storage.players,console_before,6528);
    CHECK(af_v3_save_sync()==0);CHECK(erases==1 && writes==512);
    CHECK(af_v3_save_reset()==1);CHECK(af_v3_save_read(bank,0)==1);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    CHECK(af_save_sum(af_save_live,AF_SAVE_PAYLOAD)==0);
    // Old canonical and NAFJ banks migrate without inheriting console progress.
    memcpy(bank,decoded,65536);memset(af_console_storage.players,0x92,6528);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    for(u32 i=0;i<6528;i++)CHECK(af_console_storage.players[i]==0);
    memcpy(bank+4,"NAFJ",4);bank[18]=bank[19]=0;
    u32 balance=0u-af_save_sum(bank,AF_SAVE_PAYLOAD);bank[18]=balance>>8;bank[19]=balance;
    memset(bank+AF_SAVE_PAYLOAD,0xDA,AF_SAVE_CAPSULE);memset(af_console_storage.players,0x92,6528);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    for(u32 i=0;i<6528;i++)CHECK(af_console_storage.players[i]==0);
    CHECK(!memcmp(af_save_live+0xF844,bank+0xF844,0x26)); // original native game scores retained
    // New town clears old progress; clearing a temporary header does not.
    fill_console();af_save_live[0x2F69]=2;memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);
    af_v3_save_prepare(bank);CHECK(af_console_storage.town==0x3002);
    for(u32 i=0;i<6528;i++)CHECK(af_console_storage.players[i]==0);
    fill_console();af_v3_save_clear(bank);CHECK(!memcmp(console_before,af_console_storage.players,6528));
    af_v3_save_clear(af_save_live);for(u32 i=0;i<6528;i++)CHECK(!af_console_storage.players[i]);
    // Capacity failure leaves BOTH chip banks unchanged and makes no I/O calls.
    init();fill_console();u32 random=5;
    for(u32 i=20;i<AF_SAVE_PAYLOAD;i++){random=random*1664525u+1013904223u;af_save_live[i]=random>>24;}
    af_save_live[0x2F68]=0x30;af_save_live[0x2F69]=1;
    u32 old_erases=erases,old_writes=writes;u8 chip_before[131072];memcpy(chip_before,chip,131072);
    int error=setjmp(halted);if(!error){af_v3_save_sync();CHECK(0);}
    CHECK(error==-AF_SAVE_CAPACITY);CHECK(erases==old_erases && writes==old_writes);
    CHECK(!memcmp(chip,chip_before,131072));CHECK(!memcmp(af_console_storage.players,console_before,6528));
    // Missing profile cannot repair over an otherwise valid format-five town.
    init();af_save_current[29]=0;af_v3_save_reset();memcpy(chip,saved,65536);
    error=setjmp(halted);if(!error){af_v3_save_read(bank,0);CHECK(0);}
    CHECK(error==-AF_SAVE_PROFILE_MISSING && erases==old_erases && writes==old_writes);
    // Re-entry and workspace damage are rejected before state or device mutation.
    init();af_console_storage.busy=1;
    CHECK(af_v3_save_check(saved,65536,af_save_current,NULL)==AF_SAVE_ARGUMENT);
    af_console_storage.busy=0;af_console_scratch_guard[0]^=1;
    CHECK(af_v3_save_check(saved,65536,af_save_current,NULL)==AF_SAVE_ARGUMENT);
    printf("%u native-adapter host assertions: independent players, encoded probes, decoded commit, legacy migration, pre-I/O rejection\n",assertions);
    return 0;
}
