/* Existing guarded storage services are queried before the scratch/hash loan.
 * The player/native layout is unchanged; no host data is borrowed as a visitor
 * row and no town-wide event state enters a travelling player record. */
#include "travel_native.h"
#include "console_storage.h"
#include "save_runtime.h"
extern void af_v3_require_save_state(void);
extern unsigned short af_diary_native_selected(void);
#ifdef __mips__
#define native_players ((unsigned char *)0x80126EC0u)
#define runtime ((struct AfSaveRuntime *)0x8046C000u)
#define active (*(unsigned char *volatile *)0x80136FD8u)
#else
extern unsigned char af_travel_test_players[4*0xBD0],*af_travel_test_active;
extern struct AfSaveRuntime af_save_runtime;
#define native_players af_travel_test_players
#define runtime (&af_save_runtime)
#define active af_travel_test_active
#endif
int af_travel_storage_idle(void) {return af_v3_console_storage_valid();}
unsigned char *af_travel_active(void) {return active;}
int af_travel_town(AFTravelTown *t,AFTravelSelection *s) {
    if(!t || !s || !af_travel_storage_idle())return 0;
    af_v3_require_save_state();
    t->players=native_players;t->working=runtime->working;
    t->console=af_v3_console_player_data();t->cards=af_v3_card_data();
    t->accounts=af_v3_bank_data();t->diary=af_v3_diary_data();
    for(unsigned i=0;i<AF_TP_PROFILE;i++)s->bytes[i]=0;
    for(unsigned i=0;i<192;i++)s->bytes[i]=t->working[i];
    for(unsigned i=0;i<64;i++)s->bytes[192+i]=t->working[AF_SAVE_SURFACE_OFFSET+i];
    for(unsigned i=0;i<4;i++)s->bytes[256+i]=t->working[AF_SAVE_CREATURE_OFFSET+i];
    unsigned selected=af_diary_native_selected();s->bytes[260]=selected>>8;s->bytes[261]=selected;
    s->bytes[262]=t->cards[8];s->bytes[263]=t->cards[15]&1;s->bytes[264]=t->accounts[8];
    return 1;
}
