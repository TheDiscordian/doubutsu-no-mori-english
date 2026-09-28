#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/diary_items.h"
#include "../overlays/v3/save_runtime.h"
typedef unsigned int u32;
typedef unsigned char u8;
u32 af_test_diary_items[100],af_test_diary_icons[4];
struct AfSaveRuntime af_test_diary_item_state;
u8 af_test_diary_item_players[4*0xBD0],*af_test_diary_item_active;
static unsigned short selected;
static unsigned fallback,checks,marks[4],query_count;
static u32 expected_cover,expected_player;
extern void af_diary_item_record(u32);
extern int af_diary_item_owned(const u8 *,u32);
unsigned short af_diary_native_selected(void) {return selected;}
int af_diary_prior_name(u8 *p,u32 n,u32 i) {(void)p;(void)n;(void)i;fallback++;return 99;}
int af_diary_prior_type(u32 i) {(void)i;fallback++;return 21;}
u32 af_diary_prior_price(u32 i) {(void)i;fallback++;return 777;}
unsigned short af_diary_prior_display(u32 i) {fallback++;return i;}
unsigned short af_diary_prior_pocket(u32 i) {fallback++;return i;}
void af_diary_prior_record(u32 i) {(void)i;fallback++;}
int af_diary_prior_owned(const u8 *p,u32 i) {(void)p;(void)i;fallback++;return 7;}
void af_v3_require_save_state(void) {checks++;}
void af_v3_save_halt(int error) {fprintf(stderr,"unexpected save error %d\n",error);abort();}
int af_v3_save_collect(u8 *data,u32 player,u32 item,u32 mark) {
    assert(data==af_test_diary_item_state.working && player==expected_player && item==expected_cover);
    assert(mark<=1);query_count++;if(mark)marks[player]++;return 1;
}
int main(void) {
    af_test_diary_items[0]=0x41464449;af_test_diary_items[1]=1;
    af_test_diary_items[2]=16;af_test_diary_items[3]=24;
    af_test_diary_icons[0]=0x806E2320;af_test_diary_icons[1]=0x806E2340;
    AFDiaryItem *rows=(AFDiaryItem *)(af_test_diary_items+4);
    for(unsigned i=0;i<16;i++) {
        rows[i]=(AFDiaryItem){.item=0x2B10+i,.cover=0x30FC+4*i,.price=180+i,.category=44,.style=i};
        memset(rows[i].name,'A'+i,16);
    }
    u8 text[18];memset(text,0xA5,sizeof(text));
    for(unsigned i=0;i<16;i++) {
        selected=1u<<i;u32 item=0x2B10+i,cover=0x30FC+4*i;
        assert(af_diary_item_name(text+1,16,item)==1 && !memcmp(text+1,rows[i].name,16));
        assert(text[0]==0xA5 && text[17]==0xA5);
        assert(!af_diary_item_name(text,15,item) && !af_diary_item_name(NULL,16,item));
        assert(af_diary_item_type(item)==44 && af_diary_item_price(item)==180+i);
        assert(af_diary_item_type(0xFFFF0000|item)==44);
        assert(af_diary_item_icon(item)==0x806E2300 && !af_diary_item_icon(cover));
        assert(af_diary_item_display(item)==item && af_diary_item_pocket(item)==item);
        assert(af_diary_item_collection(item)==cover);
        for(unsigned rotation=0;rotation<4;rotation++) {
            assert(af_diary_item_type(cover+rotation)==10);
            assert(af_diary_item_price(cover+rotation)==180+i);
            assert(af_diary_item_pocket(cover+rotation)==item);
            assert(af_diary_item_display(cover+rotation)==item);
            assert(af_diary_item_collection(cover+rotation)==cover);
            assert(af_diary_item_name(text+1,16,cover+rotation)==1);
        }
        for(unsigned player=0;player<4;player++) {
            af_test_diary_item_active=af_test_diary_item_players+player*0xBD0;
            expected_player=player;expected_cover=cover;
            af_diary_item_record(item);assert(af_diary_item_owned(af_test_diary_item_active,item)==1);
            af_diary_item_record(cover);assert(af_diary_item_owned(af_test_diary_item_active,cover+3)==1);
        }
        assert(!af_diary_item_owned(NULL,item));
        selected=0;unsigned calls=query_count,old_checks=checks;
        assert(!af_diary_item_type(item) && !af_diary_item_price(item) && !af_diary_item_icon(item));
        assert(!af_diary_item_display(item) && !af_diary_item_pocket(cover+3));
        assert(!af_diary_item_collection(item) && !af_diary_item_owned(af_test_diary_item_active,item));
        af_diary_item_record(item);assert(query_count==calls && checks==old_checks);
    }
    assert(!fallback && checks==256 && query_count==256);
    for(unsigned p=0;p<4;p++)assert(marks[p]==32);
    selected=65535;
    const u32 retained[]={0x2B00,0x2B0F,0x2B20,0x30FB,0x313C,0x2301,0x2328,0x24FF,0xFFFF};
    for(unsigned i=0;i<sizeof(retained)/sizeof(*retained);i++) {
        u32 item=retained[i];
        assert(af_diary_item_name(text,16,item)==99 && af_diary_item_type(item)==21);
        assert(af_diary_item_price(item)==777 && af_diary_item_display(item)==item);
        assert(af_diary_item_pocket(item)==item && !af_diary_item_collection(item));
        af_diary_item_record(item);assert(af_diary_item_owned(NULL,item)==7);
    }
    assert(fallback==7*sizeof(retained)/sizeof(*retained));
    af_test_diary_items[2]=17;assert(!af_diary_item_type(0x2B10));af_test_diary_items[2]=16;
    rows[0].style=1;assert(!af_diary_item_type(0x2B10));rows[0].style=0;
    af_test_diary_icons[1]++;assert(!af_diary_item_icon(0x2B10));
    puts("all sixteen diary identities, rotations, disabled gates, and four-player collection routing pass");
}
