/* Reuse the actual save transaction and existing native-I/O doubles. */
#define main retained_console_tests
#include "v3_console_storage_test.c"
#undef main
#undef state
#include "../overlays/v3/carried_items.h"
#include "../overlays/v3/carried_catalogue.c"
AFDiary af_diary_storage;
u32 af_diary_guard[4],af_test_event_item_profile;
u32 af_test_carried_profile[8],af_test_carried_header[8+8*AF_CARRY_COUNT];
u8 af_v3_fishing_state[AF_HF_BYTES],af_v3_card_state[AF_HC_BYTES],*af_test_carried_active;
static u8 expanded[AF_CZ_CARD_RAW],snapshot[AF_SAVE_STATE],card_before[AF_HC_BYTES];
static AFDiary diary_before;
static u32 prior_record,prior_owned;
static u32 native_paper_calls;
void af_test_carried_paper_init(PaperPreview *p,u32 item) {native_paper_calls++;p->style=item;}
int af_carried_prior_catalogue_bit(const u32 *bits,int index,NativeBit native) {return native(bits,index);}
static int native_bit(const u32 *bits,int index) {(void)bits;return index+20;}
extern void af_carried_record(u32);
extern int af_carried_owned(const u8 *,u32);
extern int af_old_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_old_expand_cards(const u8 *,u32,u8 *,u32);
extern int af_v14_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
#ifdef AF_V3_CARRIED_QUEST
extern int af_v16_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v16_expand_cards(const u8 *,u32,u8 *,u32);
#endif
#ifdef AF_V3_PAPER_PACKS
const u32 af_carried_paper_mode=TEST_PAPER_MODE;
extern int af_v17_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v17_expand_cards(const u8 *,u32,u8 *,u32);
#endif
#ifdef AF_V3_CARRIED_NPC
extern int af_v18_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v18_expand_cards(const u8 *,u32,u8 *,u32);
#endif
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
extern int af_v19_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v19_expand_cards(const u8 *,u32,u8 *,u32);
#endif
void af_carried_prior_record(u32 item) {prior_record=item;}
int af_carried_prior_owned(const u8 *player,u32 item) {(void)player;prior_owned=item;return 17;}
int af_carried_event_type(u32 item) {(void)item;return 0;}
u32 af_carried_prior_price(u32 item) {(void)item;return 0;}
static void profile(u32 mask) {
    u32 h[8]={0x41464350,1,26,32,127,mask,0,0};
    memcpy(af_test_carried_profile,h,sizeof(h));memcpy(af_test_carried_header,h,sizeof(h));
    af_test_event_item_profile=(mask>>2)&3;
    AFCarryItem *r=(AFCarryItem *)(af_test_carried_header+8);
    for(u32 i=0;i<4;i++)r[i]=(AFCarryItem){.item=0x2040+i,.source=0x2003+i*64,
        .parent=0x2040,.family=0,.state=i,.category=49,.price=40*(i+1),.icon=AF_CARRY_ICON+i*576};
}
int main(void) {
    profile(127);init();fill_console();
#ifdef AF_V3_PAPER_PACKS
    /* Native saved pockets retain every quantity, including partial packs.
     * This is the real town payload, not only a helper's returned item ID. */
    for(u32 player=0;player<4;player++)for(u32 slot=0;slot<15;slot++) {
        u32 item=af_carried_paper_with_quantity(0x2000+player*15+slot,
            TEST_PAPER_MODE?slot%4+1:1),at=0x20+player*0xBD0+0x14+slot*2;
        af_save_live[at]=item>>8;af_save_live[at+1]=item;
    }
#endif
#ifdef TEST_GOLDEN_PROFILE_BYTE
    af_save_current[TEST_GOLDEN_PROFILE_BYTE]|=TEST_GOLDEN_PROFILE_MASK;
    CHECK(af_v3_save_reset()==1);
    fill_console();
    for(u32 player=0;player<4;player++) {
        u32 at=0x20+player*0xBD0+0x14+14*2;
        af_save_live[at]=0x22;af_save_live[at+1]=0x3B;
        af_save_runtime.working[AF_SAVE_REWARD_OFFSET+player*12+8]=8;
    }
#endif
    CHECK(AF_CONSOLE_RAW+16==120304+AF_HC_BYTES && af_carried_save_enabled()==127);
    CHECK(af_v3_card_data()[4]==AF_HC_CARRIED_WIRE && af_v3_card_data()[7]==3 && af_v3_card_data()[8]==127);
#ifdef AF_V3_CARRIED_QUEST
    CHECK(af_carried_quest_day(af_v3_card_data())==0);
    CHECK(af_carried_quest_set_day(af_v3_card_data(),0x021D));
    CHECK(!af_carried_quest_set_day(af_v3_card_data(),0x021E));
    CHECK(!af_carried_quest_set_day(af_v3_card_data(),0x0D01));
    CHECK(!af_carried_quest_set_day(af_v3_card_data(),0x0100));
    CHECK(af_carried_quest_day(af_v3_card_data())==0x021D);
#endif
#ifdef AF_V3_CARRIED_NPC
    CHECK(!af_carried_quest_weeds(af_v3_card_data()));
    CHECK(af_carried_quest_set_weeds(af_v3_card_data(),1));
    CHECK(!af_carried_quest_set_weeds(af_v3_card_data(),2));
#endif
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    AFRewardGoodField good={{5,4,3,29,2,9,7,234},15},got_good;
    CHECK(af_reward_good_field_set(af_v3_card_data(),&good));
    CHECK(af_reward_good_field_get(af_v3_card_data(),&got_good) && got_good.days==15 && !memcmp(got_good.rtc,good.rtc,8));
    CHECK(!af_reward_first_present(af_v3_card_data(),3));
    CHECK(af_reward_mark_first_present(af_v3_card_data(),1));
    CHECK(af_reward_first_present(af_v3_card_data(),3)==1);
    CHECK(af_reward_mark_first_present(af_v3_card_data(),2));
    CHECK(af_reward_first_present(af_v3_card_data(),3)==3);
    CHECK(!af_reward_mark_first_present(af_v3_card_data(),4));
    for(u32 slot=0;slot<4;slot++) {
        AFRewardBirthday gift={(u16)(0xE000+slot),(u16)(2026+slot)},got;
        CHECK(af_reward_birthday_get(af_v3_card_data(),slot,&got) && !got.giver && !got.year);
        CHECK(af_reward_birthday_set(af_v3_card_data(),slot,&gift));
    }
    const AFRewardBirthday invalid[]={{0xE000,0},{0xEFFF,2026},{0xD090,2026},{0,1999},{0,2100}};
    memcpy(card_before,af_v3_card_data(),AF_HC_BYTES);
    for(u32 i=0;i<sizeof(invalid)/sizeof(*invalid);i++) {
        CHECK(!af_reward_birthday_set(af_v3_card_data(),0,invalid+i));
        CHECK(!memcmp(card_before,af_v3_card_data(),AF_HC_BYTES));
    }
#endif
    for(u32 p=0;p<4;p++) {
        AFHolidayCard card={{2026,7,27},p+1};
        CHECK(af_holiday_cards_set(af_v3_card_data(),p,&card));
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        AFRewardBirthday gift;
        CHECK(af_reward_birthday_get(af_v3_card_data(),p,&gift));
        CHECK(gift.giver==0xE000+p && gift.year==2026+p);
        CHECK(af_reward_first_present(af_v3_card_data(),3)==3);
#endif
        af_test_carried_active=af_console_players+p*0xBD0;
        CHECK(!af_carried_owned(af_test_carried_active,0x2040));
        af_carried_record(0x2040+p);
        for(u32 q=0;q<4;q++)CHECK(af_carried_owned(af_test_carried_active,0x2040+q)==1);
        const u32 *bits=(u32 *)(af_test_carried_active+0xB78);
        CHECK(af_carried_catalogue_bit(bits,67,native_bit)==1);
        CHECK(!af_carried_catalogue_bit(bits,64,native_bit));
        CHECK(!af_carried_catalogue_bit(bits,68,native_bit));
        CHECK(af_carried_catalogue_bit(bits,63,native_bit)==83);
        CHECK(af_carried_catalogue_bit((u32 *)af_test_carried_active,67,native_bit)==87);
        af_v3_diary_data()->bytes[AF_DIARY_HEADER+p*AF_DIARY_PLAYER+AF_DIARY_CALENDAR]='A'+p;
    }
    PaperPreview preview;memset(&preview,0xAB,sizeof(preview));
    for(u32 i=0;i<4;i++) {
        af_carried_paper_init(&preview,0x2040+i);
        CHECK(preview.style==64 && preview.type==1 && preview.price==40*(i+1));
        CHECK(!preview.profile && !preview.segment_offset && preview.buffer==0xABABABAB);
        CHECK(preview.height==-93.0f && preview.scale==0.28f);
    }
    CHECK(!native_paper_calls);af_carried_paper_init(&preview,0x2003);
    CHECK(native_paper_calls==1 && preview.style==0x2003);
    af_carried_record(0x2003);CHECK(prior_record==0x2003);
    CHECK(af_carried_owned(af_console_players,0x203F)==17 && prior_owned==0x203F);
    for(u32 i=0;i<14;i++){af_carried_record(0x2523+i);CHECK(!af_carried_owned(af_console_players,0x2523+i));}
    CHECK(prior_record==0x2003 && !af_carried_owned(af_console_players+1,0x2040));
    memcpy(card_before,af_v3_card_data(),AF_HC_BYTES);diary_before=*af_v3_diary_data();
    CHECK(af_v3_save_sync()==0 && chip[0xF985]==AF_HC_CARRIED_WIRE+13);
    memcpy(saved,chip,65536);u32 writes_before=writes,erases_before=erases;
    CHECK(af_old_expand_cards(saved,65536,expanded,sizeof(expanded)-AF_HC_BYTES+AF_HC_LEGACY_BYTES)==AF_CZ_FORMAT);
#ifdef AF_V3_CARRIED_QUEST
    CHECK(af_v16_expand_cards(saved,65536,expanded,sizeof(expanded)-AF_HC_BYTES+AF_HC_LEGACY_BYTES)==AF_CZ_FORMAT);
#endif
#ifdef AF_V3_PAPER_PACKS
    CHECK(af_v17_expand_cards(saved,65536,expanded,sizeof(expanded)-AF_HC_BYTES+AF_HC_LEGACY_BYTES)==AF_CZ_FORMAT);
#endif
#ifdef AF_V3_CARRIED_NPC
    CHECK(af_v18_expand_cards(saved,65536,expanded,sizeof(expanded)-AF_HC_BYTES+AF_HC_LEGACY_BYTES)==AF_CZ_FORMAT);
#endif
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    CHECK(af_v19_expand_cards(saved,65536,expanded,sizeof(expanded)-AF_HC_BYTES+AF_HC_LEGACY_BYTES)==AF_CZ_FORMAT);
#endif
    CHECK(af_v3_save_expand_cards(saved,65536,expanded,sizeof(expanded))==0);
    CHECK(!memcmp(expanded+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,card_before,AF_HC_BYTES));
    CHECK(af_holiday_cards_clear(af_v3_card_data(),2));
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
    for(u32 slot=0;slot<4;slot++) {
        AFRewardBirthday gift;
        CHECK(af_reward_birthday_get(af_v3_card_data(),slot,&gift));
        CHECK(gift.giver==(slot==2?0:0xE000+slot) && gift.year==(slot==2?0:2026+slot));
    }
    CHECK(af_reward_first_present(af_v3_card_data(),3)==3);
    u8 clearing[AF_HC_BYTES];memcpy(clearing,af_v3_card_data(),sizeof(clearing));
    CHECK(af_holiday_cards_clear(clearing,0));
    CHECK(af_holiday_cards_clear(clearing,1));
    CHECK(af_reward_first_present(clearing,3)==3);
    CHECK(af_reward_good_field_get(clearing,&got_good) && got_good.days==15 && !memcmp(got_good.rtc,good.rtc,8));
#endif
#ifdef AF_V3_CARRIED_QUEST
    CHECK(af_carried_quest_day(af_v3_card_data())==0x021D);
#endif
    CHECK(!af_v3_card_data()[11] && af_v3_card_data()[10] && af_v3_card_data()[12]);
    AFHolidayCard cleared;CHECK(af_holiday_cards_get(af_v3_card_data(),2,&cleared) && !cleared.days);
    CHECK(af_v3_save_read(bank,0)==1 && !af_v3_card_data()[11]);
    CHECK(af_v3_save_reset()==1);af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(card_before,af_v3_card_data(),AF_HC_BYTES));
    CHECK(!memcmp(&diary_before,af_v3_diary_data(),AF_DIARY_BYTES));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
#ifdef AF_V3_PAPER_PACKS
    CHECK((af_v3_card_data()[15]&1)==TEST_PAPER_MODE);
#ifdef AF_V3_CARRIED_NPC
    CHECK(af_carried_quest_weeds(af_v3_card_data())==1);
#endif
    for(u32 player=0;player<4;player++)for(u32 slot=0;slot<15;slot++) {
        u32 at=0x20+player*0xBD0+0x14+slot*2;
#ifdef TEST_GOLDEN_PROFILE_BYTE
        if(slot==14) {
            CHECK(af_save_live[at]==0x22 && af_save_live[at+1]==0x3B);
            CHECK(af_save_runtime.working[AF_SAVE_REWARD_OFFSET+player*12+8]==8);
            continue;
        }
#endif
        CHECK(((u32)af_save_live[at]<<8|af_save_live[at+1])==af_carried_paper_with_quantity(
            0x2000+player*15+slot,TEST_PAPER_MODE?slot%4+1:1));
    }
    /* A syntactically valid pack save must fail transactionally in singles
     * mode, before output publication, state adoption, erasure, or writing. */
    if(!TEST_PAPER_MODE) {
        u8 *mode=expanded+AF_CZ_RAW+AF_CZ_FISHING_EXTRA+15;*mode=1;
        CHECK(af_v3_save_compress_cards(bank,65536,expanded,65536,expanded+65536,
            6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)>0);
        memcpy(town_before,af_save_live,AF_SAVE_PAYLOAD);
        memset(snapshot,0xA7,sizeof(snapshot));
        const u8 *logical=(const u8 *)1;
        CHECK(af_v3_save_check(bank,65536,af_save_current,snapshot)==AF_SAVE_PROFILE_MISSING);
        CHECK(af_v3_console_storage_commit(bank,af_save_current,snapshot,&logical)==AF_SAVE_PROFILE_MISSING);
        CHECK(logical==(const u8 *)1);
        for(u32 i=0;i<sizeof(snapshot);i++)CHECK(snapshot[i]==0xA7);
        CHECK(!memcmp(town_before,af_save_live,AF_SAVE_PAYLOAD));
        CHECK(!memcmp(card_before,af_v3_card_data(),AF_HC_BYTES));
        CHECK(!memcmp(&diary_before,af_v3_diary_data(),AF_DIARY_BYTES));
        CHECK(!memcmp(console_before,af_console_storage.players,6528));
        CHECK(writes==writes_before && erases==erases_before);*mode=0;
    }
#endif
#ifdef TEST_GOLDEN_PROFILE_BYTE
    af_save_current[TEST_GOLDEN_PROFILE_BYTE]&=~TEST_GOLDEN_PROFILE_MASK;
    memset(snapshot,0xA7,sizeof(snapshot));
    const u8 *golden_logical=(const u8 *)1;
    CHECK(af_v3_save_check(saved,65536,af_save_current,snapshot)==AF_SAVE_PROFILE_MISSING);
    CHECK(af_v3_console_storage_commit(saved,af_save_current,snapshot,&golden_logical)==AF_SAVE_PROFILE_MISSING);
    CHECK(golden_logical==(const u8 *)1);
    for(u32 i=0;i<sizeof(snapshot);i++)CHECK(snapshot[i]==0xA7);
    CHECK(writes==writes_before && erases==erases_before);
    af_save_current[TEST_GOLDEN_PROFILE_BYTE]|=TEST_GOLDEN_PROFILE_MASK;
    CHECK(af_v3_save_check(saved,65536,af_save_current,snapshot)==1);
    puts("Golden shovel and celebration flags survive all four players' save transactions; removing its actual profile bit rejects before publication/writes.");
#endif
    /* Every removed family fails before publishing output or changing live data. */
    for(u32 bit=0;bit<7;bit++) {
        profile(127u^(1u<<bit));CHECK(af_v3_save_reset()==1);
        u8 cards[AF_HC_BYTES];memcpy(cards,af_v3_card_data(),sizeof(cards));
        memset(snapshot,0xA7,sizeof(snapshot));
        CHECK(af_v3_save_check(saved,65536,af_save_current,snapshot)==AF_SAVE_PROFILE_MISSING);
        for(u32 i=0;i<sizeof(snapshot);i++)CHECK(snapshot[i]==0xA7);
        CHECK(!memcmp(cards,af_v3_card_data(),sizeof(cards)));
        const u8 *logical=(const u8 *)1;
        CHECK(af_v3_console_storage_commit(saved,af_save_current,snapshot,&logical)==AF_SAVE_PROFILE_MISSING);
        CHECK(logical==(const u8 *)1 && !memcmp(cards,af_v3_card_data(),sizeof(cards)));
        CHECK(writes==writes_before && erases==erases_before);
    }
    profile(127);CHECK(af_v3_save_reset()==1);
    CHECK(af_v3_save_expand_cards(saved,65536,expanded,sizeof(expanded))==0);
    /* Build old wire formats using the same codec's old configuration, never an
     * old ROM. Migration retains all card stamps and initializes only new bits. */
    u8 *cards=expanded+AF_CZ_RAW+AF_CZ_FISHING_EXTRA;
    for(u32 version=1;version<AF_HC_CARRIED_WIRE;version++) {
        memcpy(cards,card_before,AF_HC_BYTES);cards[4]=version;cards[7]=version==2?3:0;
        memset(cards+8,0,8);
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        for(u32 slot=0;slot<4;slot++)memset(cards+16+slot*8+5,0,3);
        memset(cards+AF_HC_LEGACY_BYTES,0xA5,AF_HC_BYTES-AF_HC_LEGACY_BYTES);
#endif
#ifdef AF_V3_CARRIED_QUEST
        if(version==3) {cards[7]=3;cards[8]=127;cards[9]=1;cards[12]=1;}
#endif
        int size=version==2 ? af_old_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES) :
            af_v14_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
#ifdef AF_V3_CARRIED_QUEST
        if(version==3)size=af_v16_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
#endif
#ifdef AF_V3_PAPER_PACKS
        if(version==4)size=af_v17_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
#endif
#ifdef AF_V3_CARRIED_NPC
        if(version==5)size=af_v18_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
#endif
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        if(version==6)size=af_v19_compress_cards(bank,65536,expanded,65536,
            expanded+65536,6528,expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
#endif
        CHECK(size>0 && bank[0xF985]==13+version);
        CHECK(af_v3_save_check(bank,65536,af_save_current,0)>0);
        af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
        CHECK(af_v3_card_data()[4]==AF_HC_CARRIED_WIRE && af_v3_card_data()[8]==127);
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        CHECK(af_reward_good_field_get(af_v3_card_data(),&got_good) && !got_good.days);
        for(unsigned i=0;i<8;i++)CHECK(!got_good.rtc[i]);
#endif
#ifdef AF_V3_PAPER_PACKS
        CHECK(af_v3_card_data()[15]==TEST_PAPER_MODE);
#endif
        for(u32 p=0;p<4;p++)CHECK(af_v3_card_data()[9+p]==(version==3 && (p==0 || p==3)));
#ifdef AF_V3_CARRIED_QUEST
        CHECK(!af_carried_quest_day(af_v3_card_data()));
#endif
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        CHECK(!af_reward_first_present(af_v3_card_data(),3));
        for(u32 slot=0;slot<4;slot++) {
            AFRewardBirthday gift;
            CHECK(!memcmp(af_v3_card_data()+16+slot*8,card_before+16+slot*8,5));
            CHECK(af_reward_birthday_get(af_v3_card_data(),slot,&gift) && !gift.giver && !gift.year);
        }
#else
        CHECK(!memcmp(af_v3_card_data()+16,card_before+16,32));
#endif
        CHECK(!memcmp(&diary_before,af_v3_diary_data(),AF_DIARY_BYTES));
        CHECK(!memcmp(console_before,af_console_storage.players,6528));
    }
    af_carried_record(0x2043);CHECK(af_v3_card_data()[12]);
    af_v3_console_player_clear(af_console_players+3*0xBD0);
    CHECK(!af_v3_card_data()[12] && !af_v3_card_data()[16+3*8+4]);
    /* A profile addition keeps existing paper ownership; a disabled family can
     * neither reach native storage nor claim ownership. */
    u8 wire[AF_HC_BYTES];af_holiday_cards_reset(wire);
    CHECK(af_carried_save_bind(wire,0,1) && af_carried_paper_collect(wire,1,1)==1);
    CHECK(af_carried_save_bind(wire,3,127) && wire[10]==1);
    CHECK(!af_carried_save_bind(wire,0,1) && wire[10]==1 && wire[8]==127);
    profile(126);CHECK(af_v3_save_reset()==1);af_carried_record(0x2040);
    CHECK(!af_carried_owned(af_console_players,0x2040) && prior_record==0x2003);
    af_carried_paper_init(&preview,0x2043);
    CHECK(preview.type==5 && !preview.price && native_paper_calls==1);
    /* Damaged headers, ownership outside selection, and current mask mismatch
     * are rejected before erasing/writing or changing the output bank. */
    profile(127);CHECK(af_v3_save_reset()==1);memcpy(bank,saved,65536);
    af_v3_card_data()[9]=2;
    CHECK(af_v3_save_pack(bank,65536,af_save_runtime.working)==AF_SAVE_ARGUMENT);
    CHECK(!memcmp(bank,saved,65536) && writes==writes_before && erases==erases_before);
    CHECK(af_v3_save_reset()==1);
    for(u32 i=0;i<8;i++) {
        u32 before=af_test_carried_profile[i];af_test_carried_profile[i]=0xFFFFFFFF;
        CHECK(af_carried_save_enabled()==0xFFFFFFFF && !af_v3_console_storage_valid());
        af_test_carried_profile[i]=before;
    }
    af_test_event_item_profile=0;CHECK(af_carried_save_enabled()==0xFFFFFFFF);
    printf("Format-%u save transaction, all seven profile removals, prior-format migration, four-player paper ownership/clear, retained diary/console/card state, and rejection before write pass. Native I/O is doubled.\n",AF_HC_CARRIED_WIRE+13);
    return 0;
}
