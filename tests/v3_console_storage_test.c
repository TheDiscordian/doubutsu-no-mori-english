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
    memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);af_v3_save_prepare(bank);
    CHECK(bank[AF_SAVE_PAYLOAD+5]==5 && af_save_sum(bank,AF_SAVE_PAYLOAD)==0);
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
    // Player deletion preserves every other console record and the prior chain.
    for(u32 player=0;player<4;player++) {
        memcpy(af_console_storage.players,console_before,6528);
        af_v3_console_player_clear(af_console_players+player*0xBD0);
        for(u32 other=0;other<4;other++)for(u32 i=0;i<1632;i++)
            CHECK(af_console_storage.players[other*1632+i]==(other==player?0:console_before[other*1632+i]));
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
