#include "../overlays/v3/travel_native.h"
#define AF_TEST_REAL_TRAVEL 1
#define main old_note_test_main
#include "v3_pak_native_test.c"
#undef main
AFTravelVisitor af_travel_test_visitor;
u8 af_travel_test_players[4*0xBD0],af_travel_test_foreign[0xBD0];
static u8 *active;
struct TownRecords {
    u8 players[4*0xBD0],working[AF_SAVE_STATE],console[6528];
    u8 cards[AF_HC_BYTES],accounts[AF_BANK_BYTES];AFDiary diary;
};
static struct TownRecords live,home,host_before;
static AFTravelSelection settings;
static u8 animal[0x528],animal_out[0x528],cache_before[AF_TP_BYTES],foreign_before[0xBD0];
static int completed,staged;
int af_travel_storage_idle(void) {return !busy;}
u8 *af_travel_active(void) {return active;}
int af_travel_town(AFTravelTown *t,AFTravelSelection *s) {
    assert(!busy);t->players=af_travel_test_players;t->working=live.working;
    t->console=live.console;t->cards=live.cards;t->accounts=live.accounts;t->diary=&live.diary;
    memcpy(s,&settings,sizeof(*s));return 1;
}
int af_pak_check_private(const u8 *p) {return !af_pi_null_identity(p);}
void af_pak_set_kind(void *p,unsigned kind) {
    assert(p==info);put(info+STATE,kind?AF_PAK_BACKUP_NOTE:AF_PAK_PRIVATE_NOTE);
    info[STATE+EXT]=(u8)(0x1A+kind);info[STATE+EXT+1]=info[STATE+EXT+2]=info[STATE+EXT+3]=0;
}
void af_pak_clear_private(u8 *p) {memset(p,0,0xBD0);}
void af_pak_clear_animal(u8 *p) {memset(p,0,0x528);}
void af_cw_passport_stage(u8 *p) {assert(p==af_pi_passport+8);staged++;}
void af_cw_passport_complete(u8 *p,int result) {assert(p && result>=0);if(result)completed++;}
void af_v3_save_halt(int error) {fprintf(stderr,"Unexpected traveller halt %d\n",error);assert(0);__builtin_trap();}
static void cache_reset(void) {
    memset(&af_travel_test_visitor,0,sizeof(af_travel_test_visitor));
    af_travel_test_visitor.magic=AF_TRAVEL_MAGIC;
    for(unsigned i=0;i<4;i++)af_travel_test_visitor.guard[i]=AF_TRAVEL_GUARD;
}
static void live_snapshot(struct TownRecords *to) {
    memcpy(live.players,af_travel_test_players,sizeof(live.players));*to=live;
}
static void live_restore(const struct TownRecords *from) {
    live=*from;memcpy(af_travel_test_players,from->players,sizeof(from->players));
}
static void town_init(void) {
    static const u8 binding[32]="AFV3-PASSPORT-PLAYER-1";
    memcpy(bound,binding,sizeof(bound));
    memset(&live,0,sizeof(live));memset(&settings,0,sizeof(settings));
    memset(settings.bytes,255,258);settings.bytes[258]=1;
    settings.bytes[260]=settings.bytes[261]=255;settings.bytes[262]=127;settings.bytes[264]=1;
    memcpy(live.working,settings.bytes,192);
    memcpy(live.working+AF_SAVE_SURFACE_OFFSET,settings.bytes+192,64);
    memcpy(live.working+AF_SAVE_CREATURE_OFFSET,settings.bytes+256,4);
    af_holiday_cards_reset(live.cards);live.cards[4]=7;live.cards[7]=3;live.cards[8]=127;
    assert(af_bank_reset(live.accounts,sizeof(live.accounts)));live.accounts[8]=1;
    af_diary_reset(&live.diary);
    assert(af_holiday_cards_valid(live.cards));
    assert(af_bank_valid(live.accounts,sizeof(live.accounts)));
    assert(af_diary_valid(&live.diary));
    for(unsigned slot=0;slot<4;slot++) {
        u8 *p=af_travel_test_players+slot*0xBD0;
        for(unsigned i=0;i<0xBD0;i++)p[i]=(u8)(i+slot*23+17);
        live.working[AF_SAVE_PROFILE+slot*128+3]=(u8)(1u<<slot);
        live.working[AF_SAVE_REWARD_OFFSET+slot*12+3]=(u8)(1u<<slot);
        live.diary.bytes[AF_DIARY_HEADER+slot*AF_DIARY_PLAYER+AF_DIARY_CALENDAR]=(u8)('A'+slot);
        live.console[slot*1632+23]=(u8)(slot+10);
    }
    memset(animal,0x63,sizeof(animal));staged=completed=0;cache_reset();
}
static void checksum_seal(u8 *p,unsigned n) {
    unsigned sum=0;p[0]=p[1]=0;
    for(unsigned i=0;i<n;i+=2)sum+=(unsigned)p[i]*256+p[i+1];
    sum=(-sum)&65535;p[0]=(u8)(sum>>8);p[1]=(u8)sum;
}
static void complete_visit(unsigned slot) {
    reset(0);town_init();active=af_travel_test_players+slot*0xBD0;
    live_snapshot(&home);
    assert(af_v3_travel_prepare());
    AFTravelTown checked;AFTravelSelection profile;
    assert(af_travel_town(&checked,&profile));
    int exported=af_v3_player_export(records,sizeof(records),&checked,slot,&profile);
    if(exported!=AF_SAVE_OK)fprintf(stderr,"Player export rejected fixture: %d\n",exported);
    assert(exported==AF_SAVE_OK);
    assert(af_v3_travel_passport_save(active,animal,info)==1 && completed==1);
    assert(!memcmp(af_travel_test_players,home.players,sizeof(home.players)));
    /* Another town has the same build/profile, distinct residents, and
     * unrelated shared progress. Arrival may change none of those records. */
    for(unsigned i=0;i<sizeof(af_travel_test_players);i++)af_travel_test_players[i]^=0x40;
    live.cards[13]=4;live.cards[14]=2;live.working[AF_SAVE_CREATURE_OFFSET+20]=7;
    live_snapshot(&host_before);active=af_travel_test_foreign;
    assert(af_v3_travel_passport_load(active,animal_out,info)==1);
    assert(!memcmp(af_travel_test_players,host_before.players,sizeof(host_before.players)));
    assert(!memcmp(&live,&host_before,sizeof(live)));
    assert(!memcmp(active,home.players+slot*0xBD0,0xBD0) && !memcmp(animal,animal_out,sizeof(animal)));
    assert(af_travel_test_visitor.ready==1);
    const unsigned acquired[]={0x3224,0x34BF,0x2649,0x2749,0x2328,0x2D27};
    for(unsigned i=0;i<sizeof(acquired)/sizeof(*acquired);i++)
        assert(af_v3_travel_visitor_collect(active,acquired[i],1)==1);
    assert(af_v3_travel_visitor_paper(active,1)==1);
    af_travel_test_visitor.record[AF_TP_DIARY+AF_DIARY_CALENDAR+17]='Z';
    af_travel_test_visitor.record[AF_TP_CONSOLE+23]=0xAE;
    memcpy(cache_before,af_travel_test_visitor.record,AF_TP_BYTES);
    int status=-1;assert(af_v3_pak_native_status(&status,0,info,0)==1 && status==0);
    assert(!memcmp(cache_before,af_travel_test_visitor.record,AF_TP_BYTES));
    af_pi_passport[0x1100]=13;af_pi_passport[0x1101]=9;checksum_seal(af_pi_passport,0x1200);
    assert(af_v3_pak_native_write(info,af_pi_passport)==1);
    assert(!memcmp(cache_before,af_travel_test_visitor.record,AF_TP_BYTES));
    assert(af_v3_pak_native_read(info,af_pi_passport)==1 && af_pi_passport[0x1100]==13);
    assert(!memcmp(cache_before,af_travel_test_visitor.record,AF_TP_BYTES));
    assert(!memcmp(&live,&host_before,sizeof(live)));
    /* A failed departure does not change live inventory, resident state, or
     * the visitor's newly acquired records. */
    memcpy(foreign_before,active,0xBD0);save_calls=0;fail_save=2;
    assert(!af_v3_travel_passport_save(active,animal,info));fail_save=0;
    assert(!memcmp(cache_before,af_travel_test_visitor.record,AF_TP_BYTES));
    assert(!memcmp(foreign_before,active,0xBD0) && !memcmp(&live,&host_before,sizeof(live)));
    assert(af_v3_travel_passport_save(active,animal,info)==1);
    live_restore(&home);
    /* Native arrival always loads the foreign private first, then copies to
     * the matched home resident. Exercise that same sequence for each slot. */
    assert(af_v3_travel_passport_load(af_travel_test_foreign,animal_out,info)==1);
    af_v3_travel_private_copy(af_travel_test_players+slot*0xBD0,af_travel_test_foreign);
    assert(!memcmp(af_travel_test_players,home.players,sizeof(home.players)));
    assert(live.console[slot*1632+23]==0xAE);
    assert(live.diary.bytes[AF_DIARY_HEADER+slot*AF_DIARY_PLAYER+AF_DIARY_CALENDAR+17]=='Z');
    assert(live.cards[9+slot]==1);
    assert(live.working[AF_SAVE_PROFILE+slot*128+(0x224>>2)/8]&(1u<<((0x224>>2)&7)));
    for(unsigned other=0;other<4;other++)if(other!=slot) {
        assert(!memcmp(live.console+other*1632,home.console+other*1632,1632));
        assert(!memcmp(live.diary.bytes+16+other*AF_DIARY_PLAYER,
            home.diary.bytes+16+other*AF_DIARY_PLAYER,AF_DIARY_PLAYER));
        assert(!memcmp(live.working+AF_SAVE_PROFILE+other*128,
            home.working+AF_SAVE_PROFILE+other*128,128));
    }
    assert(live.cards[13]==home.cards[13] && live.cards[14]==home.cards[14]);
    assert(live.working[AF_SAVE_CREATURE_OFFSET+20]==home.working[AF_SAVE_CREATURE_OFFSET+20]);
}
static void legacy_return(void) {
    reset(0);town_init();active=af_travel_test_foreign;live_snapshot(&home);
    memset(af_pi_passport,0,sizeof(af_pi_passport));
    memcpy(af_pi_passport+8,af_travel_test_players+0xBD0,0xBD0);
    checksum_seal(af_pi_passport,0x1200);
    files[0].used=1;files[0].size=0x1200;memcpy(files[0].name,info+STATE+4,26);
    memcpy(files[0].bytes,af_pi_passport,0x1200);
    assert(af_v3_travel_passport_load(active,animal_out,info)==1 && af_travel_test_visitor.ready==2);
    af_v3_travel_private_copy(af_travel_test_players+0xBD0,active);
    assert(!memcmp(live.diary.bytes,home.diary.bytes,AF_DIARY_BYTES));
    assert(!memcmp(live.console,home.console,sizeof(live.console)));
    /* Conversion/departure must preserve missing-record provenance as well:
     * returning the new frame cannot erase records absent from the old note. */
    assert(af_v3_travel_visitor_collect(active,0x3224,1)==1);
    /* Depart from another town, not the home town whose resident already has
     * the complete editable records. Home departure can export that full row. */
    for(unsigned slot=0;slot<4;slot++)af_travel_test_players[slot*0xBD0]^=0x40;
    assert(af_v3_travel_passport_save(active,animal,info)==1);
    memcpy(af_travel_test_players,home.players,sizeof(home.players));
    assert(af_v3_travel_passport_load(active,animal_out,info)==1 && af_travel_test_visitor.ready==2);
    af_v3_travel_private_copy(af_travel_test_players+0xBD0,active);
    assert(!memcmp(live.diary.bytes,home.diary.bytes,AF_DIARY_BYTES));
    assert(!memcmp(live.console,home.console,sizeof(live.console)));
    assert(!memcmp(live.accounts,home.accounts,sizeof(live.accounts)));
    assert(!memcmp(live.cards,home.cards,sizeof(live.cards)));
    assert(live.working[AF_SAVE_PROFILE+128+(0x224>>2)/8]&(1u<<((0x224>>2)&7)));
    /* An unrelated destination resident cannot accept the legacy identity. */
    u8 before_private[0xBD0];memcpy(before_private,af_travel_test_players,0xBD0);
    assert(!af_v3_travel_passport_load(af_travel_test_players,animal_out,info));
    assert(!memcmp(before_private,af_travel_test_players,0xBD0));
}
int main(void) {
    for(unsigned slot=0;slot<4;slot++)complete_visit(slot);
    legacy_return();
    puts("Connected native departure/arrival/acquisition/nonce/status/return lifecycle passes for all four identities; legacy return retains editable progress; device I/O is doubled");
    return 0;
}
