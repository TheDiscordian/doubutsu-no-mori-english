/* Current carried readers -> real profile codec -> format-eleven save adapter.
 * The FlashRAM device is a host double; this is not native gameplay evidence. */
#define main af_diary_retained_storage_tests
#include "v3_console_storage_test.c"
#undef main
#undef state
#include "../overlays/v3/diary_items.h"
#include "../overlays/v3/diary_native.h"
AFDiary af_diary_storage;
u32 af_diary_guard[4];
static AFDiary diary_copy,staging;
static AFDiaryDraft draft;
static u8 widths[256];
static int preflight(void *ctx,const AFDiary *d) {(void)ctx;return af_v3_diary_preflight(d);}
u32 af_test_diary_items[100],af_test_diary_icons[4];
u8 *af_test_diary_item_active;
#define STYLE(s) [63+(s)]={((1087+(s))>>8),((1087+(s))&255), \
    ((0x30FC+4*(s))>>8),((0x30FC+4*(s))&255),0,0,0,1}
const u8 af_diary_native_profiles[79][80]={
    STYLE(0),STYLE(1),STYLE(2),STYLE(3),STYLE(4),STYLE(5),STYLE(6),STYLE(7),
    STYLE(8),STYLE(9),STYLE(10),STYLE(11),STYLE(12),STYLE(13),STYLE(14),STYLE(15)};
static unsigned native_records;
void af_diary_prior_record(u32 item) {CHECK(item==0x2B00);native_records++;}
int af_diary_prior_owned(const u8 *p,u32 item) {(void)p;CHECK(item==0x2B00);return 9;}
extern void af_diary_item_record(u32);
extern int af_diary_item_owned(const u8 *,u32);

int main(void) {
    init();
    for(u32 s=0;s<16;s++)af_save_current[32+(63+s)/8]|=1u<<((63+s)&7);
    CHECK(af_v3_save_reset()==1);
    CHECK(af_diary_native_selected()==65535);
    af_test_diary_items[0]=0x41464449;af_test_diary_items[1]=1;
    af_test_diary_items[2]=16;af_test_diary_items[3]=24;
    AFDiaryItem *rows=(AFDiaryItem *)(af_test_diary_items+4);
    for(u32 s=0;s<16;s++)rows[s]=(AFDiaryItem){.item=0x2B10+s,
        .cover=0x30FC+s*4,.price=180,.category=44,.style=s};
    for(u32 p=0;p<4;p++) {
        af_test_diary_item_active=af_console_players+p*0xBD0;
        for(u32 s=0;s<16;s++) {
            CHECK(af_diary_item_owned(af_test_diary_item_active,0x2B10+s)==0);
            if(s%4==p)af_diary_item_record(0x2B10+s);
        }
    }
    af_diary_item_record(0x2B00);CHECK(native_records==1);
    CHECK(af_diary_item_owned(af_console_players,0x2B00)==9);
    memset(widths,6,sizeof(widths));
    for(u32 p=0;p<4;p++) {
        CHECK(af_diary_begin(&draft,af_v3_diary_data(),p,p,p,widths)==1);
        CHECK(af_diary_command(&draft,8,'A'+p,widths)==1);
        CHECK(af_diary_commit(af_v3_diary_data(),&draft,&staging,widths,preflight,0)==1);
    }
    diary_copy=af_diary_storage;
    memcpy(working_before,af_save_runtime.working,AF_SAVE_STATE);
    CHECK(af_v3_save_sync()==0);memcpy(saved,chip,sizeof(saved));
    CHECK(saved[0xF985]==11 && erases==1 && writes==512);
    CHECK(af_v3_save_reset()==1);CHECK(af_v3_save_read(bank,0)==1);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(&diary_copy,&af_diary_storage,sizeof(diary_copy)));
    CHECK(!memcmp(working_before,af_save_runtime.working,AF_SAVE_STATE));
    for(u32 p=0;p<4;p++)for(u32 s=0;s<16;s++) {
        CHECK(af_diary_item_owned(af_console_players+p*0xBD0,0x2B10+s)==(s%4==p));
        for(u32 r=0;r<4;r++)CHECK(af_diary_item_owned(af_console_players+p*0xBD0,0x30FC+s*4+r)==(s%4==p));
    }
    /* Both collected and uncollected selected styles are save dependencies.
     * Rejection must leave output, live town/pages, and the device untouched. */
    u8 smaller[AF_SAVE_PROFILE],untouched[AF_SAVE_STATE];
    memcpy(town_before,af_save_live,AF_SAVE_PAYLOAD);
    memset(untouched,0xA5,sizeof(untouched));
    for(u32 s=0;s<16;s++) {
        memcpy(smaller,af_save_current,sizeof(smaller));
        smaller[32+(63+s)/8]&=~(1u<<((63+s)&7));
        CHECK(af_v3_save_check(saved,65536,smaller,untouched)==AF_SAVE_PROFILE_MISSING);
        for(u32 i=0;i<sizeof(untouched);i++)assert(untouched[i]==0xA5);
    }
    CHECK(!memcmp(saved,chip,65536) && erases==1 && writes==512);
    CHECK(!memcmp(town_before,af_save_live,AF_SAVE_PAYLOAD));
    CHECK(!memcmp(&diary_copy,&af_diary_storage,sizeof(diary_copy)));
    af_v3_console_player_clear(af_console_players+0xBD0);
    for(u32 p=0;p<4;p++) {
        const u8 *page=af_diary_page(&af_diary_storage,p,p,p);
        CHECK(page && page[0]==(p==1?32:'A'+p));
    }
    printf("All sixteen diary parent/cover profiles, independent ownership, format-eleven reload, and missing-profile rejection pass (%u host assertions).\n",assertions);
    return 0;
}
