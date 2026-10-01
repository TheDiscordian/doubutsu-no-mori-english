#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/travel_player.h"
#include "../overlays/v3/pak_codec.h"
typedef unsigned char u8;
typedef unsigned int u32;
struct Buffers {
    u8 players[4*0xBD0],working[AF_SAVE_STATE],console[4*AF_TP_CONSOLE_BYTES];
    u8 cards[AF_HC_BYTES],accounts[AF_BANK_BYTES];
    AFDiary diary;
};
static struct Buffers town,before,expected;
static AFTravelSelection selection;
static AFTravelTown refs;
static u8 record[AF_TP_BYTES],record_before[AF_TP_BYTES],native[AF_PAK_PRIVATE_NOTE];
static u8 note[AF_PAK_MAX_NOTE],raw[AF_PAK_PRIVATE_NOTE+AF_TP_BYTES];
static u32 hash[AF_PAK_HASH_WORDS];
static void setup(void) {
    memset(&town,0,sizeof(town));memset(&selection,0,sizeof(selection));
    refs=(AFTravelTown){town.players,town.working,town.console,town.cards,town.accounts,&town.diary};
    memset(selection.bytes,255,256);selection.bytes[256]=selection.bytes[257]=255;selection.bytes[258]=1;
    selection.bytes[260]=selection.bytes[261]=255;selection.bytes[262]=127;selection.bytes[264]=1;
    memcpy(town.working,selection.bytes,192);
    memcpy(town.working+AF_SAVE_SURFACE_OFFSET,selection.bytes+192,64);
    memcpy(town.working+AF_SAVE_CREATURE_OFFSET,selection.bytes+256,4);
    /* Host seasonal state must not leak into the travelling record or be
     * overwritten on return, even though collections share this allocation. */
    town.working[AF_SAVE_CREATURE_OFFSET+20]=11;
    town.working[AF_SAVE_CREATURE_OFFSET+21]=3;
    town.working[AF_SAVE_CREATURE_OFFSET+22]=1;
    af_diary_reset(&town.diary);af_holiday_cards_reset(town.cards);
    town.cards[4]=7;town.cards[7]=3;town.cards[8]=127;
    town.cards[13]=2;town.cards[14]=28;town.cards[15]=2;
    assert(af_bank_reset(town.accounts,sizeof(town.accounts)));town.accounts[8]=1;
    for(u32 slot=0;slot<4;slot++) {
        u8 *id=town.players+slot*0xBD0;
        for(u32 i=0;i<16;i++)id[i]=(u8)(17+i+slot*23);
        for(u32 i=16;i<0xBD0;i++)id[i]=(u8)(slot+i);
        town.working[AF_SAVE_PROFILE+slot*128+3]=(u8)(1u<<slot);
        town.working[AF_SAVE_PROFILE+512+slot*32+7]=(u8)(1u<<slot);
        town.working[AF_SAVE_SURFACE_OFFSET+64+slot*64+11]=(u8)(1u<<slot);
        town.working[AF_SAVE_CREATURE_OFFSET+4+slot*4]=(u8)(1u<<slot);
        town.working[AF_SAVE_REWARD_OFFSET+slot*12+3]=(u8)(1u<<slot);
        town.cards[9+slot]=0;
        u8 *c=town.cards+16+slot*8;
        c[0]=7;c[1]=234;c[2]=8;c[3]=15;c[4]=(u8)(7+slot);
        c[5]=(u8)(27+(slot<2?128:0));c[6]=0xE0;c[7]=(u8)(slot+1);
        u8 *a=town.accounts+16+slot*8;
        a[2]=(u8)(slot+1);a[4]=4;
        u8 *diary=town.diary.bytes+16+slot*AF_DIARY_PLAYER;
        diary[0]=1;diary[98]=(u8)(slot&1);diary[100]=7;diary[101]=234;diary[102]=8;
        for(u32 i=AF_DIARY_CALENDAR;i<AF_DIARY_PLAYER;i++)diary[i]=(u8)('A'+slot);
        for(u32 i=0;i<AF_TP_CONSOLE_BYTES;i++)town.console[slot*AF_TP_CONSOLE_BYTES+i]=(u8)(slot+i*17);
    }
    assert(af_holiday_cards_valid(town.cards));assert(af_diary_valid(&town.diary));
    assert(af_bank_valid(town.accounts,sizeof(town.accounts)));
    memset(record,0xA5,sizeof(record));before=town;
}
static void fails(u32 slot,int error) {
    before=town;
    assert(af_v3_player_restore(&refs,slot,record,sizeof(record),&selection)==error);
    assert(!memcmp(&town,&before,sizeof(town)));
}
int main(void) {
    for(u32 slot=0;slot<4;slot++) {
        setup();
        assert(af_v3_player_export(record,sizeof(record),&refs,slot,&selection)==AF_SAVE_OK);
        assert(!memcmp(&town,&before,sizeof(town)));
        assert(af_v3_player_records_valid(record,sizeof(record),&selection)==AF_SAVE_OK);
        assert(!memcmp(record+16,town.players+slot*0xBD0,16));
        assert(!(record[AF_TP_CARD+5]&128));
        assert(!memcmp(record+AF_TP_DIARY,town.diary.bytes+16+slot*AF_DIARY_PLAYER,AF_DIARY_PLAYER));
        assert(!memcmp(record+AF_TP_CONSOLE,town.console+slot*AF_TP_CONSOLE_BYTES,AF_TP_CONSOLE_BYTES));
        memcpy(record_before,record,sizeof(record));
        const u8 *identity=town.players+slot*0xBD0;
        const u32 acquired[]={0x3224,0x34BF,0x2649,0x2749,0x2328,0x2D27};
        for(u32 i=0;i<sizeof(acquired)/sizeof(acquired[0]);i++) {
            assert(af_v3_player_collect(record,sizeof(record),identity,acquired[i],0,&selection)==0);
            assert(af_v3_player_collect(record,sizeof(record),identity,acquired[i],1,&selection)==1);
            assert(af_v3_player_collect(record,sizeof(record),identity,acquired[i],0,&selection)==1);
        }
        assert(af_v3_player_collect(record,sizeof(record),identity,0x3227,0,&selection)==1);
        assert(af_v3_player_paper(record,sizeof(record),identity,1,&selection)==1);
        assert(!memcmp(&town,&before,sizeof(town)));
        u8 wrong[16];memcpy(wrong,identity,16);wrong[15]^=1;
        assert(af_v3_player_collect(record,sizeof(record),wrong,0x3224,1,&selection)==AF_SAVE_BINDING);
        assert(af_v3_player_collect(record,sizeof(record),identity,0x1000,1,&selection)==AF_SAVE_ARGUMENT);
        record[AF_TP_DIARY+AF_DIARY_CALENDAR+17]='Z';
        record[AF_TP_CONSOLE+23]^=0x55;
        record[AF_TP_CARD+4]=12;record[AF_TP_CARD+5]=28;
        record[AF_TP_ACCOUNT+2]=7;record[AF_TP_REWARDS+3]|=128;
        /* Complete real player record passes through the shared note codec. */
        memset(native,0,sizeof(native));memcpy(native+8,identity,16);
        AFPakInput input={native,record,0,sizeof(native),sizeof(record),{0},{0}};
        memcpy(input.identity,identity,16);AFPakView view;
        int bytes=af_v3_pak_encode(note,sizeof(note),&input,hash,sizeof(hash));assert(bytes>0);
        assert(af_v3_pak_decode(note,(u32)bytes,input.binding,identity,raw,sizeof(raw),&view)==1);
        assert(view.record_bytes==sizeof(record) && !memcmp(view.records,record,sizeof(record)));
        /* Unrelated home-side updates are retained alongside visiting updates. */
        town.working[AF_SAVE_PROFILE+slot*128+99]|=4;
        town.diary.bytes[6]=1;town.cards[13]=3;town.cards[14]=1;
        before=town;expected=town;
        for(u32 i=0;i<128;i++)expected.working[AF_SAVE_PROFILE+slot*128+i]|=record[AF_TP_FURNITURE+i];
        for(u32 i=0;i<32;i++)expected.working[AF_SAVE_PROFILE+512+slot*32+i]|=record[AF_TP_CLOTHING+i];
        for(u32 i=0;i<64;i++)expected.working[AF_SAVE_SURFACE_OFFSET+64+slot*64+i]|=record[AF_TP_SURFACES+i];
        for(u32 i=0;i<4;i++)expected.working[AF_SAVE_CREATURE_OFFSET+4+slot*4+i]|=record[AF_TP_CREATURES+i];
        for(u32 i=0;i<12;i++)expected.working[AF_SAVE_REWARD_OFFSET+slot*12+i]|=record[AF_TP_REWARDS+i];
        expected.cards[9+slot]=1;
        u8 first=expected.cards[21+slot*8]&128;
        memcpy(expected.cards+16+slot*8,record+AF_TP_CARD,8);expected.cards[21+slot*8]|=first;
        memcpy(expected.accounts+16+slot*8,record+AF_TP_ACCOUNT,8);
        memcpy(expected.console+slot*AF_TP_CONSOLE_BYTES,record+AF_TP_CONSOLE,AF_TP_CONSOLE_BYTES);
        memcpy(expected.diary.bytes+16+slot*AF_DIARY_PLAYER,record+AF_TP_DIARY,AF_DIARY_PLAYER);
        assert(af_v3_player_restore(&refs,slot,view.records,view.record_bytes,&selection)==AF_SAVE_OK);
        assert(!memcmp(&town,&expected,sizeof(town)));
        assert(af_holiday_cards_valid(town.cards));assert(af_diary_valid(&town.diary));
        assert(af_bank_valid(town.accounts,sizeof(town.accounts)));
        fails((slot+1)%4,AF_SAVE_BINDING);
        record[0]^=1;fails(slot,AF_SAVE_FORMAT);record[0]^=1;
        record[12]=1;fails(slot,AF_SAVE_FORMAT);record[12]=0;
        record[AF_TP_ACCOUNT+8]=1;fails(slot,AF_SAVE_FORMAT);record[AF_TP_ACCOUNT+8]=0;
        record[AF_TP_DIARY+98]=2;fails(slot,AF_SAVE_FORMAT);record[AF_TP_DIARY+98]=(u8)(slot&1);
        record[AF_TP_REWARDS]=128;fails(slot,AF_SAVE_REWARD_INVALID);record[AF_TP_REWARDS]=0;
        record[AF_TP_PAPER]=2;fails(slot,AF_SAVE_CATALOGUE_INVALID);record[AF_TP_PAPER]=1;
        record[AF_TP_CARD+5]=128;fails(slot,AF_SAVE_FORMAT);record[AF_TP_CARD+5]=28;
        record[AF_TP_ACCOUNT+5]=1;fails(slot,AF_SAVE_FORMAT);record[AF_TP_ACCOUNT+5]=0;
        selection.bytes[32+17]=0;fails(slot,AF_SAVE_ARGUMENT);
        /* Keep host profile coherent, but reject incoming required content. */
        town.working[32+17]=0;fails(slot,AF_SAVE_PROFILE_MISSING);
        assert(af_v3_player_restore(&refs,4,record,sizeof(record),&selection)==AF_SAVE_ARGUMENT);
    }
    setup();
    selection.bytes[32+17]=0;town.working[32+17]=0;
    town.working[AF_SAVE_PROFILE+17]=1;
    memcpy(record_before,record,sizeof(record));before=town;
    assert(af_v3_player_export(record,sizeof(record),&refs,0,&selection)==AF_SAVE_CATALOGUE_INVALID);
    assert(!memcmp(record,record_before,sizeof(record)) && !memcmp(&town,&before,sizeof(town)));
    setup();
    assert(af_v3_player_export(town.working,sizeof(record),&refs,0,&selection)==AF_SAVE_ARGUMENT);
    assert(af_v3_player_export(record,sizeof(record)-1,&refs,0,&selection)==AF_SAVE_ARGUMENT);
    assert(!memcmp(&town,&before,sizeof(town)));
    puts("pass: four identity-bound players, visitor collection in every ownership family, full diary/console note transport, exact isolated return merge, shared town state preservation, and transactional rejection");
}
