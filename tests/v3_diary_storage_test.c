/* Reuse the existing native save-I/O doubles, without replaying its old tests. */
#define main af_console_retained_tests
#include "v3_console_storage_test.c"
#undef main
AFDiary af_diary_storage;
u32 af_diary_guard[4];
static AFDiary diary_copy,candidate,staging;
static AFDiaryDraft draft;
static u8 expanded[AF_CZ_DIARY_RAW],widths[256];
static int preflight(void *ctx,const AFDiary *d) {(void)ctx;return af_v3_diary_preflight(d);}

int main(void) {
    init();fill_console();CHECK(af_diary_valid(af_v3_diary_data()));
    memset(widths,6,sizeof(widths));
    for(u32 p=0;p<4;p++)for(u32 m=0;m<12;m++) {
        CHECK(af_diary_begin(&draft,af_v3_diary_data(),p,p,m,widths)==1);
        CHECK(af_diary_command(&draft,8,'A'+p,widths)==1);
        CHECK(af_diary_command(&draft,8,'a'+m,widths)==1);
        CHECK(af_diary_commit(af_v3_diary_data(),&draft,&staging,widths,preflight,0)==1);
    }
    CHECK(erases==0 && writes==0 && !af_save_runtime.ready && !af_console_storage.ready);
    diary_copy=af_diary_storage;
    CHECK(af_v3_save_sync()==0);CHECK(erases==1 && writes==512);
    memcpy(saved,chip,sizeof(saved));CHECK(saved[0xF985]==11);
    CHECK(af_v3_save_expand_diary(saved,65536,expanded,sizeof(expanded))==0);
    CHECK(!memcmp(expanded+AF_CZ_RAW,&diary_copy,sizeof(diary_copy)));
    CHECK(!memcmp(expanded+65536,console_before,6528));
    /* Probes must not publish any decoded pages to live state. */
    CHECK(af_diary_player_clear(&af_diary_storage,0)==1);
    candidate=af_diary_storage;memcpy(working_before,af_save_runtime.working,AF_SAVE_STATE);
    CHECK(af_v3_save_read(bank,0)==1);
    CHECK(!memcmp(&candidate,&af_diary_storage,sizeof(candidate)));
    CHECK(!memcmp(working_before,af_save_runtime.working,AF_SAVE_STATE));
    CHECK(af_v3_save_reset()==1);memset(af_save_live,0,sizeof(af_save_live));
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(&diary_copy,&af_diary_storage,sizeof(diary_copy)));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    CHECK(!memcmp(expanded,af_save_live,AF_SAVE_PAYLOAD));
    /* Changed profile or corrupt envelope cannot commit diary/town state. */
    memcpy(town_before,af_save_live,AF_SAVE_PAYLOAD);candidate=af_diary_storage;
    bank[400]^=1;
    CHECK(af_v3_save_check(bank,65536,af_save_current,0)<0);
    CHECK(!memcmp(&candidate,&af_diary_storage,sizeof(candidate)));
    CHECK(!memcmp(town_before,af_save_live,AF_SAVE_PAYLOAD));bank[400]^=1;
    af_v3_console_player_clear(af_console_players+0xBD0);
    for(u32 p=0;p<4;p++)for(u32 m=0;m<12;m++) {
        const u8 *text=af_diary_page(&af_diary_storage,p,p,m);CHECK(text);
        CHECK(text[0]==(p==1?32:'A'+p) && text[1]==(p==1?32:'a'+m));
    }
    /* Forward migration initializes diary-only state while retaining the town,
     * profiles, fish/insect season fields, and complete console records. */
    CHECK(af_v3_save_compress(bank,65536,expanded,65536,console_before,6528,
        af_console_hash,AF_CZ_WORK_BYTES)>0);
    af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);af_diary_reset(&candidate);
    CHECK(!memcmp(&candidate,&af_diary_storage,sizeof(candidate)));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    /* A rejected edit keeps its draft and existing live/save data, without
     * going through the fatal save path or calling erase/write. */
    CHECK(af_diary_begin(&draft,&af_diary_storage,0,0,0,widths)==1);
    CHECK(af_diary_command(&draft,8,'X',widths)==1);
    u32 random=5,old_erases=erases,old_writes=writes;
    for(u32 i=20;i<AF_SAVE_PAYLOAD;i++){random=random*1664525u+1013904223u;af_save_live[i]=random>>24;}
    af_save_live[0x2F68]=0x30;af_save_live[0x2F69]=1;
    CHECK(af_diary_commit(&af_diary_storage,&draft,&staging,widths,preflight,0)==AF_DIARY_CAPACITY);
    CHECK(!memcmp(&candidate,&af_diary_storage,sizeof(candidate)));
    CHECK(draft.length==1 && draft.text[0]=='X' && !af_save_runtime.error);
    CHECK(erases==old_erases && writes==old_writes && !memcmp(saved,chip,65536));
    /* Full-state reset/new player/town boundaries and independent guards. */
    CHECK(af_v3_save_reset()==1);af_diary_guard[3]^=1;
    CHECK(!af_v3_console_storage_valid());CHECK(af_v3_save_check(saved,65536,af_save_current,0)==AF_SAVE_ARGUMENT);
    CHECK(af_v3_save_reset()==1);CHECK(af_v3_console_storage_valid());
    printf("%u diary/native-save adapter assertions; erase/write order, migration, and failed-edit retention pass.\n",assertions);
    return 0;
}
