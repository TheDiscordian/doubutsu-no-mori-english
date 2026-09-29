/* Use the real complete bank transaction; only FlashRAM/native I/O is doubled. */
#define AF_CARRIED_STORAGE_MAIN retained_carried_storage_tests
#include "v3_carried_storage_test.c"
#include "design_templates.h"
AFDesigns af_v3_design_state;
static AFDesigns designs_before,candidate;
static _Alignas(32) u8 full[AF_CZ_DESIGN_RAW],migrated[AF_CZ_DESIGN_RAW];
static u8 chip_before[sizeof(chip)];
extern int af_v19_compress_cards(u8 *,u32,const u8 *,u32,const u8 *,u32,const u8 *,u32 *,u32);
extern int af_v19_expand_cards(const u8 *,u32,u8 *,u32);
int main(void) {
    volatile unsigned phase=0;
    int error=setjmp(halted);
    if(error){fprintf(stderr,"Unexpected save halt %d at phase %u\n",error,phase);return 1;}
    profile(127);init();fill_console();
    CHECK(AF_CONSOLE_RAW==137792 && af_design_valid(af_v3_design_data()));
    for(u32 p=0;p<4;p++)for(u32 i=0;i<8;i++) {
        AFDesign *d=&af_v3_design_data()->patterns[p][i];
        CHECK(!memcmp(d,af_design_templates+i,sizeof(*d)));
        d->palette=(p*8+i)%16;
        for(u32 y=0;y<32;y++)for(u32 x=0;x<32;x++)af_design_paint(d,x,y,(x*3+y*5+p+i)&15);
        af_v3_design_data()->order[p][i]=7-i;
        CHECK(af_design_name(d,(const u8 *)"new pattern",11)>=0);
    }
    designs_before=*af_v3_design_data();diary_before=*af_v3_diary_data();
    memcpy(card_before,af_v3_card_data(),AF_HC_BYTES);
    phase=1;CHECK(af_v3_save_sync()==0 && chip[0xF985]==20 && writes==512 && erases==1);
    memcpy(saved,chip,65536);
    CHECK(af_v3_save_expand_designs(saved,65536,full,sizeof(full))==0);
    CHECK(!memcmp(full+AF_CZ_RAW+AF_CZ_DESIGN_OFFSET,&designs_before,AF_DESIGN_BYTES));
    CHECK(!memcmp(full+65536,console_before,6528));
    CHECK(!memcmp(full+AF_CZ_RAW,&diary_before,AF_DIARY_BYTES));
    CHECK(!memcmp(full+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,card_before,AF_HC_BYTES));
    CHECK(af_v19_expand_cards(saved,65536,expanded,sizeof(expanded))==AF_CZ_FORMAT);
    CHECK(af_v3_save_expand_cards(saved,65536,expanded,sizeof(expanded))==AF_CZ_FORMAT);
    phase=2;CHECK(af_v3_save_reset()==1);CHECK(af_v3_save_read(bank,0)==1);
    CHECK(memcmp(&designs_before,af_v3_design_data(),AF_DESIGN_BYTES));
    phase=3;af_v3_save_commit(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(!memcmp(&designs_before,af_v3_design_data(),AF_DESIGN_BYTES));
    CHECK(!memcmp(console_before,af_console_storage.players,6528));
    /* Format nineteen keeps existing town/card/diary/console bytes and acquires
     * donor templates; migration cannot inherit a different town's designs. */
    CHECK(af_v19_compress_cards(bank,65536,full,65536,full+65536,6528,
        full+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)>0 && bank[0xF985]==19);
    CHECK(af_v3_save_expand_designs(bank,65536,migrated,sizeof(migrated))==0);
    for(u32 p=0;p<4;p++)for(u32 i=0;i<8;i++) {
        const AFDesigns *s=(const AFDesigns *)(migrated+AF_CZ_RAW+AF_CZ_DESIGN_OFFSET);
        CHECK(!memcmp(&s->patterns[p][i],af_design_templates+i,sizeof(AFDesign)) && s->order[p][i]==i);
    }
    CHECK(!memcmp(full,migrated,AF_CZ_CARD_RAW));
    /* Player deletion clears only the requested design records/order. */
    phase=4;af_v3_console_player_clear(af_console_players+2*0xBD0);
    CHECK(af_design_reset_player(&designs_before,2,af_design_templates)==1);
    CHECK(!memcmp(&designs_before,af_v3_design_data(),AF_DESIGN_BYTES));
    phase=5;af_v3_save_commit(saved,af_save_live,AF_SAVE_PAYLOAD);designs_before=*af_v3_design_data();
    candidate=designs_before;af_design_paint(&candidate.patterns[3][7],31,31,2);
    u32 ew=writes,ee=erases;
    CHECK(af_v3_design_measure(full,af_save_runtime.working,&candidate)>0);
    CHECK(!memcmp(&designs_before,af_v3_design_data(),AF_DESIGN_BYTES) && ew==writes && ee==erases);
    /* Structural corruption fails before output mutation. */
    u8 original_bank[65536];memcpy(original_bank,bank,sizeof(bank));
    AFDesigns *s=(AFDesigns *)(full+AF_CZ_RAW+AF_CZ_DESIGN_OFFSET);
    s->order[0][0]=s->order[0][1];
    CHECK(af_v3_save_compress_designs(bank,65536,full,65536,full+65536,6528,
        full+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)==AF_CZ_FORMAT);
    CHECK(!memcmp(original_bank,bank,sizeof(bank)));*s=designs_before;
    full[AF_CZ_CARD_RAW]=1;
    CHECK(af_v3_save_compress_designs(bank,65536,full,65536,full+65536,6528,
        full+AF_CZ_RAW,af_console_hash,AF_CZ_WORK_BYTES)==AF_CZ_FORMAT);
    full[AF_CZ_CARD_RAW]=0;
    /* Random/incompressible town plus full pattern data must not write a
     * partial bank, discard pixels, or erase either FlashRAM bank. */
    u32 random=7;
    for(u32 i=20;i<AF_SAVE_PAYLOAD;i++){random=random*1664525u+1013904223u;af_save_live[i]=random>>24;}
    af_save_live[0x2F68]=0x30;af_save_live[0x2F69]=1;
    /* Full-size preflight uses a bank, not the shorter live payload. */
    memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);
    CHECK(af_v3_design_measure(bank,af_save_runtime.working,&candidate)==AF_SAVE_CAPACITY);
    memcpy(chip_before,chip,sizeof(chip));
    error=setjmp(halted);if(!error){af_v3_save_sync();CHECK(0);}
    CHECK(error==-AF_SAVE_CAPACITY && ew==writes && ee==erases);
    CHECK(!memcmp(chip_before,chip,sizeof(chip)));
    CHECK(!memcmp(&designs_before,af_v3_design_data(),AF_DESIGN_BYTES));
    printf("%u assertions: format-20 full-design save/restore, format-19 migration, deletion, and capacity rejection (paper mode %d)\n",assertions,TEST_PAPER_MODE);
    return 0;
}
