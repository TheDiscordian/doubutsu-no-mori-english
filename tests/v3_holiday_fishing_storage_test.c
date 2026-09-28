/* Exercise the changed complete save path; native FlashRAM remains doubled. */
#define main retained_console_tests
#include "v3_console_storage_test.c"
#undef main
AFDiary af_diary_storage;
u32 af_diary_guard[4];
u8 af_v3_fishing_state[AF_HF_BYTES];
static u8 expanded[AF_CZ_FISHING_RAW],fish_before[AF_HF_BYTES],snapshot[65536];
static AFDiary diary_before,candidate;
extern int af_old_compress_diary(u8 *,u32,const u8 *,u32,const u8 *,u32,const AFDiary *,u32 *,u32);
extern int af_old_expand_diary(const u8 *,u32,u8 *,u32);

static void records(unsigned int units) {
    AFHolidayFish fish;CHECK(af_holiday_fish_reset(&fish,units));
    for(u32 i=0;i<4;i++) {
        u8 *p=af_console_players+i*0xBD0;
        memset(p,32,16);p[0]='A'+i;p[6]='T';p[12]=0x12;p[13]=i;p[14]=0x30;p[15]=1;
    }
    for(u32 i=0;i<5;i++) {
        AFHFRecord *r=fish.fishRecord+i;
        af_holiday_fish_native_person(&r->pid,af_console_players+(i%4)*0xBD0);
        r->time=(AFHFTime){0,0,18,7+i*7,0,6,2026};
        if(i==4)r->time=(AFHFTime){0,0,18,1,0,11,2026};
        r->size=units==AF_HF_INCHES?21:54;
    }
    CHECK(af_holiday_fish_store(&fish,af_v3_fishing_data(),AF_HF_BYTES));
    memcpy(fish_before,af_v3_fishing_data(),AF_HF_BYTES);
}

int main(void) {
    for(u32 units=0;units<2;units++) {
        init();fill_console();records(units);
        AFDiary *d=af_v3_diary_data();
        for(u32 p=0;p<4;p++)d->bytes[AF_DIARY_HEADER+p*AF_DIARY_PLAYER+AF_DIARY_CALENDAR]='A'+p;
        diary_before=*d;
        CHECK(af_v3_console_storage_valid());
        CHECK(af_v3_save_sync()==0 && chip[0xF985]==13);
        memcpy(saved,chip,65536);
        CHECK(af_old_expand_diary(saved,65536,expanded,AF_CZ_DIARY_RAW)==AF_CZ_FORMAT);
        CHECK(af_v3_save_expand_fishing(saved,65536,expanded,sizeof(expanded))==0);
        CHECK(!memcmp(expanded+AF_CZ_RAW+AF_DIARY_BYTES,fish_before,AF_HF_BYTES));
        CHECK(af_v3_save_reset()==1 && af_v3_save_read(bank,0)==1);
        CHECK(!af_v3_fishing_data()[16]); /* Probe does not commit saved records. */
        af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
        CHECK(!memcmp(&diary_before,&af_diary_storage,sizeof(diary_before)));
        CHECK(!memcmp(console_before,af_console_storage.players,6528));
        CHECK(!memcmp(fish_before,af_v3_fishing_data(),AF_HF_BYTES));
        candidate=diary_before;candidate.bytes[120]='X';
        u32 writes_before=writes,erases_before=erases;
        CHECK(af_v3_diary_preflight(&candidate)>0);
        CHECK(writes==writes_before && erases==erases_before);
        CHECK(!memcmp(fish_before,af_v3_fishing_data(),AF_HF_BYTES));
        CHECK(af_old_compress_diary(bank,65536,expanded,65536,console_before,6528,
            &diary_before,af_console_hash,AF_CZ_WORK_BYTES)>0 && bank[0xF985]==12);
        CHECK(af_v3_save_check(bank,65536,af_save_current,0)>0);
        CHECK(!memcmp(fish_before,af_v3_fishing_data(),AF_HF_BYTES));
        af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
        CHECK(!memcmp(&diary_before,&af_diary_storage,sizeof(diary_before)));
        CHECK(af_v3_fishing_data()[5]==AF_HF_CM);
        for(u32 i=16;i<AF_HF_BYTES;i++)CHECK(!af_v3_fishing_data()[i]);
        memcpy(af_v3_fishing_data(),fish_before,AF_HF_BYTES);
        af_v3_console_player_clear(af_console_players);
        AFHolidayFish decoded;CHECK(af_holiday_fish_reset(&decoded,units));
        CHECK(af_holiday_fish_load(&decoded,af_v3_fishing_data(),AF_HF_BYTES,units));
        CHECK(!decoded.fishRecord[0].size && !decoded.fishRecord[4].size);
        for(u32 i=1;i<4;i++)CHECK(decoded.fishRecord[i].size);
        memcpy(af_v3_fishing_data(),fish_before,AF_HF_BYTES);
        memcpy(bank,saved,65536);bank[400]^=1;
        CHECK(af_v3_save_check(bank,65536,af_save_current,0)<0);
        CHECK(!memcmp(fish_before,af_v3_fishing_data(),AF_HF_BYTES));
        /* Invalid imported state cannot begin a device write or overwrite output. */
        memcpy(snapshot,bank,65536);af_v3_fishing_data()[7]=31;
        CHECK(af_v3_save_pack(bank,65536,af_save_runtime.working)==AF_SAVE_ARGUMENT);
        CHECK(!memcmp(snapshot,bank,65536) && writes==writes_before && erases==erases_before);
    }
    printf("Fishing format-13 save/reload, both units, complete records, diary/console preservation, format-12 migration, old-reader rejection, player deletion, and failure-before-write pass. Native I/O is doubled.\n");
    return 0;
}
