#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/held_selection.c"
u32 af_test_held_selection[188];
u8 af_test_held_profile[192];
#undef header
#undef profile
#define AF_V3_HELD_COLLECTION
#include "../overlays/v3/held_items.c"
u32 af_test_held_items[340];
int af_test_held_selected(u32 item) { return af_v3_player_selected_equipment(item); }
#include "../overlays/v3/held_collection.c"
struct AfSaveRuntime af_collection_state;
u8 af_collection_players[4*0xBD0], *af_collection_active;
static u32 native_calls,native_argument,checked,cleared;
static int failure;
static jmp_buf warning;
void af_v3_require_save_state(void) { assert(state->ready);++checked; }
void af_v3_save_halt(int error) { failure=error;longjmp(warning,1); }
void af_v3_original_collect(u32 arg) { ++native_calls;native_argument=arg; }
void af_v3_original_private_clear(u8 *p) { ++cleared;memset(p,0,0xBD0); }
int af_v3_item_type(u32 item) { return item==0x34BF || item==0x3224; }
extern void af_v3_catalogue_clear(u8 *);

int main(void) {
    af_test_held_selection[0]=0x41464853u;af_test_held_selection[1]=1;
    af_test_held_selection[2]=92;af_test_held_selection[3]=8;
    header[0]=0x41464849;header[1]=1;header[2]=56;header[3]=24;
    Entry *selectors=(Entry *)(af_test_held_selection+4);
    HeldItem *parents=(HeldItem *)(header+4);
    for (u32 i=0;i<8;++i) {
        u32 item=0x2254+i,display=0x314C+i*4,index=(display&0xFFF)>>2;
        selectors[item-0x2200]=(Entry){item,107+i,1,32+index/8,1u<<(index%8),1};
        parents[item-0x2224]=(HeldItem){item,600,display,107+i,43,{0}};
        af_test_held_profile[32+index/8]|=1u<<(index%8);
    }
    af_test_held_profile[160+0xBF/8]|=1u<<(0xBF%8);
    af_test_held_profile[32+(0x224/4)/8]|=1u<<((0x224/4)%8);
    state->ready=1;memcpy(state->working,af_test_held_profile,192);
    u8 snapshot[AF_SAVE_STATE];
    for (u32 p=0;p<4;++p) {
        active=players+p*0xBD0;
        for (u32 i=0;i<8;++i) {
            u32 item=0x2254+i,display=0x314C+i*4;
            assert(af_v3_held_item_collection(item)==display);
            assert(!af_v3_held_catalogue_owned(active,item));
            af_v3_held_catalogue_record(item|0x10000u);
            memcpy(snapshot,state->working,sizeof(snapshot));
            for (u32 r=0;r<4;++r) {
                assert(af_v3_held_item_collection(display+r)==display);
                assert(af_v3_held_catalogue_owned(active,display+r)==1);
            }
            assert(af_v3_held_catalogue_owned(active,item)==1);
            af_v3_held_catalogue_record(display+3);
            assert(!memcmp(snapshot,state->working,sizeof(snapshot)));
            if (p<3) assert(!af_v3_held_catalogue_owned(players+(p+1)*0xBD0,item));
        }
        af_v3_held_catalogue_record(0x34BF);af_v3_held_catalogue_record(0x3224);
        assert(af_v3_held_catalogue_owned(active,0x34BF)==1);
        assert(af_v3_held_catalogue_owned(active,0x3224)==1);
    }
    assert(!native_calls && checked);
    /* Persist every parent-derived bit through the actual format-2 codec. */
    u8 *bank=calloc(1,AF_SAVE_BANK),decoded[AF_SAVE_STATE];assert(bank);
    bank[8]=bank[0x2F68]=0x30;bank[9]=bank[0x2F69]=1;
    assert(af_v3_save_pack(bank,AF_SAVE_BANK,state->working)==AF_SAVE_OK);
    assert(af_v3_save_check(bank,AF_SAVE_BANK,af_test_held_profile,decoded)==AF_SAVE_OK);
    assert(!memcmp(decoded,state->working,AF_SAVE_STATE));
    u8 subset[192];memcpy(subset,af_test_held_profile,192);subset[42]&=~8;
    memset(decoded,0xA5,sizeof(decoded));
    assert(af_v3_save_check(bank,AF_SAVE_BANK,subset,decoded)==AF_SAVE_PROFILE_MISSING);
    for (u32 i=0;i<sizeof(decoded);++i) assert(decoded[i]==0xA5);
    free(bank);
    memcpy(snapshot,state->working,sizeof(snapshot));
    /* Disabled, unavailable, malformed, oversized, and invalid-player queries. */
    for (u32 i=0;i<8;++i) {
        Entry *s=selectors+84+i;u8 selected=af_test_held_profile[s->profile_byte];
        af_test_held_profile[s->profile_byte]&=~s->mask;
        assert(!af_v3_held_catalogue_owned(active,0x2254+i));
        assert(!af_v3_held_catalogue_owned(active,0x314C+i*4));
        af_v3_held_catalogue_record(0x2254+i);
        af_test_held_profile[s->profile_byte]=selected;
    }
    selectors[84].ready=0;assert(!af_v3_held_item_collection(0x2254));selectors[84].ready=1;
    for (u32 i=0;i<4;++i) {
        u32 old=header[i];header[i]^=1;
        assert(!af_v3_held_item_collection(0x2254));assert(!af_v3_held_item_collection(0x314C));
        header[i]=old;
    }
    assert(!af_v3_held_item_collection(0x12254));assert(!af_v3_held_item_collection(0xFFFFFFFF));
    assert(!af_v3_held_catalogue_owned(players+1,0x2254));
    assert(!memcmp(snapshot,state->working,sizeof(snapshot)));
    af_v3_held_catalogue_record(0x10002200);assert(native_calls==1 && native_argument==0x10002200);
    u8 *foreign=calloc(1,0xBD0);assert(foreign);active=foreign;
    if (!setjmp(warning)) { af_v3_held_catalogue_record(0x2254);assert(0); }
    assert(failure==AF_SAVE_ARGUMENT && !memcmp(snapshot,state->working,sizeof(snapshot)));
    active=players;state->working[42]&=~8;
    if (!setjmp(warning)) { af_v3_held_catalogue_record(0x2254);assert(0); }
    assert(failure==AF_SAVE_PROFILE_MISSING);state->working[42]|=8;
    af_v3_catalogue_clear(foreign);assert(!memcmp(snapshot,state->working,sizeof(snapshot)));
    for (u32 p=0;p<4;++p) {
        af_v3_catalogue_clear(players+p*0xBD0);
        for (u32 q=0;q<4;++q) assert(af_v3_held_catalogue_owned(players+q*0xBD0,0x2254)==(q>p));
    }
    assert(cleared==5);free(foreign);
    puts("Shared parent/display collection, actual codec, four players, clearing, guards, and fallbacks pass");
}
