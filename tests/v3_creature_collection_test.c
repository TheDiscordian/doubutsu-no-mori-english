#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/creature_collection.c"
#include "../overlays/v3/creature_icon.c"

#define ICON(i) [4+(i)*2]=0x8064F000, [5+(i)*2]=0x8064F100
const u32 af_creature_icons[]={0x41464350,1,17,8,
    ICON(0),ICON(1),ICON(2),ICON(3),ICON(4),ICON(5),ICON(6),ICON(7),ICON(8),
    ICON(9),ICON(10),ICON(11),ICON(12),ICON(13),ICON(14),ICON(15),ICON(16)};
#undef ICON

struct AfSaveRuntime af_creature_collection_state;
u8 af_creature_players[4*0xBD0],*af_creature_active;
static unsigned mask;
static jmp_buf failure;
static int expected_error;
int af_creature_item_type(u32 id) {
    unsigned i=id<0x2D00 ? id-0x2320 : id-0x2D20+9;
    return i<17 && (mask&(1u<<i)) ? (i<9 ? 8 : 18) : 0;
}
void af_v3_require_save_state(void) {
    for (unsigned i=0;i<4;i++) assert(state->working[AF_SAVE_CREATURE_OFFSET+i]==((mask>>(8*i))&255));
}
void af_v3_save_halt(int reason) {
    assert(expected_error && reason==expected_error);longjmp(failure,1);
}
static void profile(unsigned bits) {
    mask=bits;
    for (unsigned i=0;i<4;i++) state->working[AF_SAVE_CREATURE_OFFSET+i]=(u8)(mask>>(8*i));
}
int main(void) {
    u8 actor[0x13E0],untouched[4*0xBD0];
    memset(players,0x5A,sizeof(af_creature_players));
    for (unsigned p=0;p<4;p++) {
        write_word(players+p*0xBD0+0xABC,0);write_word(players+p*0xBD0+0xAC0,0);
    }
    memcpy(untouched,players,sizeof(untouched));
    profile(0x1FFFF);
    for (unsigned i=0;i<17;i++) {
        unsigned id=i<9 ? 0x2320+i : 0x2D20+i-9;
        assert(af_v3_creature_icon(id)==af_creature_icons+4+i*2);
    }
    assert(!af_v3_creature_icon(0x2301) && !af_v3_creature_icon(0x2329) && !af_v3_creature_icon(0x2D28));
    /* Every species records for every player; added catches never alias a
     * native bit, another player's data, or the independent insect category. */
    for (unsigned p=0;p<4;p++) {
        af_creature_active=players+p*0xBD0;
        for (unsigned i=36;i<45;i++) {
            memset(actor,0,sizeof(actor));af_v3_creature_notice_fish(actor,(int)i);
            assert(af_v3_creature_collected(active,0,i-4,0));
            assert(!read_word(actor+0xD24));
        }
        for (unsigned i=32;i<40;i++) {
            assert(af_v3_creature_last_insect(actor,(int)i)==actor && !read_word(actor+0xD14));
            assert(af_v3_creature_notice_insect(actor,(int)i)==actor);
            assert(af_v3_creature_collected(active,1,i,0));
        }
        assert(!memcmp(players,untouched,sizeof(untouched)));
        for (unsigned q=0;q<4;q++) {
            u8 *bits=state->working+AF_SAVE_CREATURE_OFFSET+4+q*4;
            assert(read_word(bits)==(q<=p ? 0xFFFF0100u : 0));
        }
    }
    af_creature_active=players;
    memset(state->working+AF_SAVE_CREATURE_OFFSET+4,0,16);
    /* A full native collection is not complete until selected additions are
     * caught. The prospective final catch triggers once, without early writes. */
    for (unsigned kind=0;kind<2;kind++) {
        write_word(active+0xABC+kind*4,0xFFFFFFFFu);
        unsigned end=kind ? 40 : 41;
        assert(!af_v3_creature_complete(active,kind,-1));
        for (unsigned i=32;i<end;i++) {
            assert(last_catch(kind,i)==(i==end-1));
            assert(!af_v3_creature_collected(active,kind,i,0));
            assert(af_v3_creature_collected(active,kind,i,1));
            assert(!last_catch(kind,i));
        }
        assert(af_v3_creature_complete(active,kind,-1));
    }
    active[0xAEC]=0;
    assert(af_v3_creature_fish_talk() && af_v3_creature_insect_talk());
    af_v3_creature_start_complete();assert(active[0xAEC]==5);
    assert(af_v3_creature_fish_talk() && af_v3_creature_insect_talk());
    active[0xAEC]|=10;assert(!af_v3_creature_fish_talk() && !af_v3_creature_insect_talk());
    /* Native final catches still trigger correctly, including the high bit. */
    write_word(active+0xABC,0x7FFFFFFFu);af_v3_creature_notice_fish(actor,31);
    assert(read_word(actor+0xD24)==1 && read_word(active+0xABC)==0xFFFFFFFFu);
    af_v3_creature_notice_fish(actor,31);assert(read_word(actor+0xD24)==0);
    write_word(active+0xAC0,0x7FFFFFFFu);af_v3_creature_last_insect(actor,31);
    assert(read_word(actor+0xD14)==1 && read_word(active+0xAC0)==0x7FFFFFFFu);
    af_v3_creature_notice_insect(actor,31);assert(read_word(active+0xAC0)==0xFFFFFFFFu);
    /* Disabled species do not become necessary for completion or writable. */
    profile(1u<<8);memset(state->working+AF_SAVE_CREATURE_OFFSET+4,0,16);
    assert(!af_v3_creature_complete(active,0,-1) && af_v3_creature_complete(active,1,-1));
    af_v3_creature_notice_fish(actor,44);assert(read_word(actor+0xD24)==1);
    u8 saved[AF_SAVE_STATE];memcpy(saved,state->working,sizeof(saved));
    for (int i=-1;i<=45;i++) if (i<0 || (i>=32 && i!=35 && i!=44)) af_v3_creature_notice_fish(actor,i);
    for (int i=-1;i<=40;i++) if (i<0 || i>=32) af_v3_creature_notice_insect(actor,i);
    assert(!memcmp(saved,state->working,sizeof(saved)));
    profile(0);assert(af_v3_creature_complete(active,0,-1));
    for (unsigned i=0;i<17;i++) assert(!af_v3_creature_icon(i<9 ? 0x2320+i : 0x2D20+i-9));
    /* A foreign private block can retain native records, but cannot silently
     * write added catches into a resident's extended save. */
    u8 visitor[0xBD0]={0};af_creature_active=visitor;profile(1);
    assert(!af_v3_creature_collected(active,0,32,0));
    memcpy(saved,state->working,sizeof(saved));
    expected_error=AF_SAVE_ARGUMENT;
    if (!setjmp(failure)) {af_v3_creature_notice_fish(actor,36);abort();}
    assert(!memcmp(saved,state->working,sizeof(saved)));
    puts("pass: all 17 species, four players, native bits, final catches, completion dialogue, disabled and foreign records");
}
