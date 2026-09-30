/* Exercise the actual saved-town owner. Physical FlashRAM is doubled, not
 * claimed as ordinary native gameplay or original-hardware persistence. */
#include "v3_carried_storage_test.c"
extern int af_v20_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v20_expand_cards(const u8 *,u32,u8 *,u32);
static u8 bank_expanded[AF_CZ_BANK_RAW],account_before[AF_BANK_BYTES];
u8 af_bank_storage[AF_BANK_BYTES];
u32 af_bank_storage_guard[4];
static int selected=TEST_BANK_MODE;
int af_bank_native_selected(void) {return selected;}
extern u8 *af_bank_native_account(void);
static void account_fill(u8 *p) {
    CHECK(af_bank_reset(p,AF_BANK_BYTES));CHECK(af_bank_bind(p,AF_BANK_BYTES,1));
    for(u32 slot=0;slot<4;slot++) {
        u32 amount=AF_BANK_MAX-slot*100000001u;u8 *row=p+16+slot*8;
        row[0]=amount>>24;row[1]=amount>>16;row[2]=amount>>8;row[3]=amount;
        row[4]=4u<<slot;
    }
    CHECK(af_bank_valid(p,AF_BANK_BYTES));
}
static int encode_version(unsigned version,const u8 *raw) {
    typedef int (*Encoder)(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
    const Encoder encoders[]={af_v14_compress_cards,af_old_compress_cards,
        af_v16_compress_cards,af_v17_compress_cards,af_v18_compress_cards,
        af_v19_compress_cards,af_v20_compress_cards};
    return encoders[version-1](bank,65536,raw,65536,raw+65536,6528,
        raw+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
}
int main(void) {
    profile(127);init();fill_console();
    CHECK(AF_CONSOLE_RAW==AF_CZ_CARD_RAW+48);
    CHECK(af_bank_native_account()==af_v3_bank_data());
    CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
    for(u32 i=0;i<4;i++) {
        af_bank_storage_guard[i]^=1;CHECK(!af_v3_console_storage_valid());af_bank_storage_guard[i]^=1;
    }
    if(selected)account_fill(af_v3_bank_data());
    for(u32 slot=0;slot<4;slot++) {
        AFHolidayCard card={{2026,7,27},slot+1};
        AFRewardBirthday gift={(u16)(0xE000+slot),(u16)(2026+slot)};
        CHECK(af_holiday_cards_set(af_v3_card_data(),slot,&card));
        CHECK(af_reward_birthday_set(af_v3_card_data(),slot,&gift));
        af_v3_diary_data()->bytes[AF_DIARY_HEADER+slot*AF_DIARY_PLAYER+AF_DIARY_CALENDAR]='A'+slot;
    }
    AFRewardGoodField good={{5,4,3,29,2,9,7,234},15};
    CHECK(af_reward_good_field_set(af_v3_card_data(),&good));
    CHECK(af_reward_mark_first_present(af_v3_card_data(),1));
    CHECK(af_reward_mark_first_present(af_v3_card_data(),2));
    CHECK(af_carried_quest_set_day(af_v3_card_data(),0x021D));
    CHECK(af_carried_quest_set_weeds(af_v3_card_data(),1));
    memcpy(account_before,af_v3_bank_data(),AF_BANK_BYTES);
    memcpy(card_before,af_v3_card_data(),AF_HC_BYTES);diary_before=*af_v3_diary_data();
    CHECK(af_v3_diary_preflight(&diary_before)>0);
    CHECK(af_v3_save_sync()==0 && chip[0xF985]==21);
    CHECK(erases==1 && writes==512);memcpy(saved,chip,65536);memcpy(chip+65536,saved,65536);
    CHECK(af_v20_expand_cards(saved,65536,expanded,sizeof(expanded))==AF_CZ_FORMAT);
    CHECK(af_v3_save_expand_cards(saved,65536,expanded,sizeof(expanded))==AF_CZ_FORMAT);
    CHECK(af_v3_save_expand_bank(saved,65536,bank_expanded,sizeof(bank_expanded))==0);
    CHECK(!memcmp(bank_expanded+AF_CZ_RAW+AF_CZ_CARD_EXTRA,account_before,AF_BANK_BYTES));
    CHECK(!memcmp(bank_expanded+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,card_before,AF_HC_BYTES));
    int measured=af_v3_save_measure_bank(bank_expanded,65536,bank_expanded+65536,
        6528,bank_expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES);
    CHECK(measured>0 && measured==af_v3_diary_preflight(&diary_before));
    CHECK(af_v3_save_reset()==1);
    CHECK(af_v3_save_read(bank,0)==1 && af_v3_save_read(bank,512)==1);
    /* Probing banks cannot adopt any saved account. */
    AFBankAccount a;
    for(u32 slot=0;slot<4;slot++)CHECK(af_bank_get(af_v3_bank_data(),AF_BANK_BYTES,slot,&a) && !a.balance && !a.received);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(af_v3_bank_data(),account_before,AF_BANK_BYTES));
    CHECK(!memcmp(af_v3_card_data(),card_before,AF_HC_BYTES));
    CHECK(!memcmp(af_v3_diary_data(),&diary_before,AF_DIARY_BYTES));
    CHECK(!memcmp(af_console_storage.players,console_before,6528));
    /* Deletion clears only that resident; required-bank support survives even
     * after all four accounts are empty, as do town-owned golden rewards. */
    for(u32 slot=0;slot<4;slot++) {
        af_v3_console_player_clear(af_console_players+slot*0xBD0);
        CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
        for(u32 other=0;other<4;other++) {
            CHECK(af_bank_get(af_v3_bank_data(),AF_BANK_BYTES,other,&a));
            CHECK(a.balance==(!selected || other<=slot?0:AF_BANK_MAX-other*100000001u));
            CHECK(a.received==(!selected || other<=slot?0:4u<<other));
        }
        CHECK(af_reward_first_present(af_v3_card_data(),3)==3);
    }
    CHECK(af_v3_save_check(saved,65536,af_save_current,NULL)==AF_SAVE_OK);
    af_v3_save_commit(saved,af_save_live,AF_SAVE_PAYLOAD);
    /* Mode removal rejects a supported bank before caller output, accounts,
     * town, consoles, or device writes can change. */
    u32 writes_before=writes,erases_before=erases;
    u8 *account=bank_expanded+AF_CZ_RAW+AF_CZ_CARD_EXTRA;
    account_fill(account);
    CHECK(af_v3_save_compress_bank(bank,65536,bank_expanded,65536,bank_expanded+65536,
        6528,bank_expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)>0);
    CHECK(bank[0xF985]==21);
    selected=0;CHECK(af_v3_save_reset()==1);
    u8 empty[AF_BANK_BYTES];memcpy(empty,af_v3_bank_data(),AF_BANK_BYTES);
    memcpy(town_before,af_save_live,AF_SAVE_PAYLOAD);memset(snapshot,0xA7,sizeof(snapshot));
    const u8 *logical=(const u8 *)1;
    CHECK(af_v3_save_check(bank,65536,af_save_current,snapshot)==AF_SAVE_PROFILE_MISSING);
    CHECK(af_v3_console_storage_commit(bank,af_save_current,snapshot,&logical)==AF_SAVE_PROFILE_MISSING);
    CHECK(logical==(const u8 *)1);
    for(u32 i=0;i<sizeof(snapshot);i++)CHECK(snapshot[i]==0xA7);
    CHECK(!memcmp(empty,af_v3_bank_data(),AF_BANK_BYTES));
    CHECK(!memcmp(town_before,af_save_live,AF_SAVE_PAYLOAD));
    CHECK(writes==writes_before && erases==erases_before);
    selected=TEST_BANK_MODE;CHECK(af_v3_save_reset()==1);
    /* Invalid account fields fail compression/preflight before output/writes. */
    memcpy(bank,saved,65536);account[21]=1;
    CHECK(af_v3_save_compress_bank(bank,65536,bank_expanded,65536,bank_expanded+65536,
        6528,bank_expanded+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)==AF_CZ_FORMAT);
    CHECK(!memcmp(bank,saved,65536));account[21]=0;
    /* Every card-era envelope migrates once, retaining full older records and
     * creating only the new account allocation, with no device writes. */
    for(unsigned version=1;version<=7;version++) {
        u8 *cards=bank_expanded+AF_CZ_RAW+AF_CZ_FISHING_EXTRA;
        memcpy(cards,card_before,AF_HC_BYTES);cards[4]=version;cards[7]=version>=2?3:0;
        if(version<3)memset(cards+8,0,8);
        if(version==3)memset(cards+13,0,3);
        if(version==4)cards[15]=0;
        if(version==5)cards[15]&=1;
        if(version<7)for(u32 slot=0;slot<4;slot++)memset(cards+16+slot*8+5,0,3);
        CHECK(encode_version(version,bank_expanded)>0 && bank[0xF985]==version+13);
        CHECK(af_v3_save_expand_bank(bank,65536,bank_expanded,sizeof(bank_expanded))==0);
        CHECK(af_bank_required(account,AF_BANK_BYTES)==0);
        CHECK(!memcmp(bank_expanded+AF_CZ_RAW,&diary_before,AF_DIARY_BYTES));
        CHECK(!memcmp(bank_expanded+AF_CZ_BANK,console_before,6528));
        for(u32 slot=0;slot<4;slot++)CHECK(!memcmp(cards+16+slot*8,card_before+16+slot*8,5));
        CHECK(af_v3_save_check(bank,65536,af_save_current,NULL)==AF_SAVE_OK);
        af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
        CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
        for(u32 slot=0;slot<4;slot++)CHECK(af_bank_get(af_v3_bank_data(),AF_BANK_BYTES,slot,&a) && !a.balance && !a.received);
        if(version==7)CHECK(!memcmp(af_v3_card_data(),card_before,AF_HC_BYTES));
    }
    CHECK(writes==writes_before && erases==erases_before);
    /* Earlier compressed/canonical towns have no account tail at all. */
    CHECK(af_v3_save_compress(bank,65536,bank_expanded,65536,bank_expanded+65536,
        6528,af_console_hash,AF_CZ_WORK_BYTES)>0 && bank[0xF985]==9);
    CHECK(af_v3_save_check(bank,65536,af_save_current,NULL)==AF_SAVE_OK);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    for(u32 slot=0;slot<4;slot++)CHECK(af_bank_get(af_v3_bank_data(),AF_BANK_BYTES,slot,&a) && !a.balance && !a.received);
    CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
    af_v3_save_commit(bank_expanded,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
    /* A new town does not inherit balances or acknowledgements. */
    if(selected)account_fill(af_v3_bank_data());
    af_save_live[0x2F69]=2;memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);
    af_v3_save_prepare(bank);
    CHECK(af_save_runtime.town==0x3002);
    for(u32 slot=0;slot<4;slot++)CHECK(af_bank_get(af_v3_bank_data(),AF_BANK_BYTES,slot,&a) && !a.balance && !a.received);
    CHECK(af_bank_required(af_v3_bank_data(),AF_BANK_BYTES)==selected);
    CHECK(writes==writes_before && erases==erases_before);
    printf("Bank mode %u: format-21 account save/read/adoption, both banks, all residents, deletion, new-town clearing, format-14..20 migrations, mode removal, and guarded preflight pass. Native I/O is doubled.\n",selected);
    return 0;
}
