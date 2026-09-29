#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/creature_travel.c"

u8 af_save_live[AF_SAVE_PAYLOAD],af_creature_players[4*PRIVATE];
u8 af_travel_foreign[PRIVATE],af_travel_passport[PASSPORT];
u32 af_travel_loaded;
struct AfSaveRuntime af_creature_collection_state;
struct Visitor af_travel_visitor;
int af_cw_test_save_step;
static u8 bank[AF_SAVE_BANK],disk[AF_SAVE_BANK],pak[PASSPORT],before[AF_SAVE_PAYLOAD];
static u8 temporary[PRIVATE],animal[0x528],*active;
static int enabled=1,allocate_ok=1,erase_ok=1,write_ok=1,pak_ok=1,step_result;
static unsigned prepares,pages,erases,releases,pak_writes;
extern void af_cw_clean_spirits(u8 *),af_cw_save_prepare(u8 *);
extern int af_cw_save_step(int,int,int),af_cw_save_sync(void);

void *af_cw_private(void) {return active;}
u32 af_carried_quantity(u32 item) {assert(item==0x2D28);return enabled;}
u32 af_v3_creature_profile_byte(u32 i) {return i<2?255:i==2?1:0;}
void af_v3_require_save_state(void) {}
void af_v3_save_halt(int e) {fprintf(stderr,"unexpected save halt: %d\n",e);abort();}
void af_save_copy(const void *s,void *d,u32 n) {memcpy(d,s,n);}
u8 *af_save_allocate(u32 n) {assert(n==AF_SAVE_BANK);return allocate_ok?bank:NULL;}
void af_save_release(void *p) {assert(p==bank);releases++;}
void af_v3_save_prepare(u8 *p) {assert(p==bank);prepares++;}
int af_save_erase(void) {erases++;if(!erase_ok)return -1;memset(disk,255,sizeof(disk));return 0;}
int af_save_write_page(const u8 *p,u32 page) {
    pages++;assert(page<512 && p==bank+page*128);
    if(!write_ok && page==64)return -1;
    memcpy(disk+page*128,p,128);return 0;
}
void af_pak_set_kind(void *p,unsigned n) {assert(p==(void *)123 && n==0);}
int af_pak_read(void *p,void *out) {assert(p==(void *)123);memcpy(out,pak,PASSPORT);return 1;}
int af_pak_write(void *p,const void *data) {
    assert(p==(void *)123);pak_writes++;
    assert(!memcmp(before,af_save_live,sizeof(before)));
    if(!pak_ok)return 0;
    memcpy(pak,data,PASSPORT);return 1;
}
int af_pak_check_private(const u8 *p) {return p[14]==0x30 && p[15];}
void af_pak_clear_private(u8 *p) {memset(p,0,PRIVATE);}
void af_pak_clear_animal(u8 *p) {memset(p,0,0x528);}
int af_cw_prior_save_step(int kind,int unused,int mode) {
    assert((kind==1 || kind==3) && unused==1 && (mode==0 || mode==1));
    assert(!memcmp(before,af_save_live,sizeof(before)));
    if(af_cw_test_save_step==0)af_cw_test_save_step=1;
    else if(af_cw_test_save_step==2) {
        memcpy(bank,af_save_live,AF_SAVE_PAYLOAD);af_cw_save_prepare(bank);
    } else if(af_cw_test_save_step==4) {
        memcpy(temporary,active,PRIVATE);
        assert(af_v3_creature_passport_save(temporary,animal,(void *)123)==pak_ok);
        assert(!memcmp(temporary,active,PRIVATE));
    }
    return step_result;
}
static void seed(void) {
    memset(af_save_live,0xA5,sizeof(af_save_live));
    memset(bank,0,sizeof(bank));memset(pak,0xB6,sizeof(pak));
    memset(&visitor,0,sizeof(visitor));
    for(unsigned n=0;n<4;n++) {
        u8 *p=af_save_live+0x20+n*PRIVATE;
        for(unsigned i=0;i<16;i++)p[i]=(u8)(n*20+i);
        p[14]=0x30;p[15]=n+1;
        for(unsigned i=0;i<15;i++) {
            unsigned item=i<5?0x2D28+i:i==5?0x2D27:i==6?0x2D2D:0x2043;
            p[0x14+i*2]=item>>8;p[0x15+i*2]=item;
        }
        put(p+0x34,0xE4E4E4E4);
    }
    memcpy(af_creature_players,af_save_live+0x20,sizeof(af_creature_players));
    active=af_save_live+0x20+2*PRIVATE;
    memcpy(before,af_save_live,sizeof(before));
    for(unsigned i=0;i<4;i++) {
        state->working[AF_SAVE_CREATURE_OFFSET+i]=af_v3_creature_profile_byte(i);
        for(unsigned n=0;n<4;n++)state->working[AF_SAVE_CREATURE_OFFSET+4+n*4+i]=i==0?1u<<n:0;
    }
    allocate_ok=erase_ok=write_ok=pak_ok=1;step_result=0;
    prepares=pages=erases=releases=pak_writes=0;
}
static void expect_clean(const u8 *actual,const u8 *original) {
    u8 expected[PRIVATE];memcpy(expected,original,sizeof(expected));
    memset(expected+0x14,0,10);put(expected+0x34,word(expected+0x34)&~0x3FFu);
    assert(!memcmp(actual,expected,PRIVATE));
}
static void transaction(int kind,int mode,int final_step,int result) {
    seed();af_cw_test_save_step=0;
    assert(!af_cw_save_step(kind,1,mode));
    af_cw_test_save_step=2;assert(!af_cw_save_step(kind,1,mode));
    assert(prepares==1);
    for(unsigned n=0;n<4;n++) {
        const u8 *p=bank+0x20+n*PRIVATE,*old=before+0x20+n*PRIVATE;
        if(n==2 && mode==0)expect_clean(p,old);else assert(!memcmp(p,old,PRIVATE));
    }
    af_cw_test_save_step=4;assert(!af_cw_save_step(kind,1,mode));
    if(mode==0)expect_clean(pak+8,active);else assert(!memcmp(pak+8,active,PRIVATE));
    assert(!checksum(pak));
    assert(pak[CAPSULE+28]==4 && pak[CAPSULE+29]==0);
    assert(!memcmp(before,af_save_live,sizeof(before)));
    af_cw_test_save_step=final_step;step_result=result;
    assert(af_cw_save_step(kind,1,mode)==result);
    if(final_step==8 && result==1 && mode==0) {
        expect_clean(active,before+0x20+2*PRIVATE);
        memset(before+0x20+2*PRIVATE+0x14,0,10);
        put(before+0x20+2*PRIVATE+0x34,0xE4E4E400);
    }
    assert(!memcmp(before,af_save_live,sizeof(before)));
}
int main(void) {
    for(int kind=1;kind<=3;kind+=2) {
        transaction(kind,0,8,1);transaction(kind,1,8,1);
        transaction(kind,0,5,1);transaction(kind,0,7,-2);
    }
    seed();allocate_ok=0;assert(af_cw_save_sync()==-1 && !erases && !releases);
    assert(!memcmp(before,af_save_live,sizeof(before)));
    seed();erase_ok=0;assert(af_cw_save_sync()==-1 && !pages && releases==1);
    assert(!memcmp(before,af_save_live,sizeof(before)));
    seed();write_ok=0;assert(af_cw_save_sync()==-1 && pages==68 && releases==1);
    assert(!memcmp(before,af_save_live,sizeof(before)));
    seed();assert(!af_cw_save_sync() && pages==512 && releases==1);
    expect_clean(active,before+0x20+2*PRIVATE);assert(!memcmp(bank,disk,sizeof(bank)));
    seed();pak_ok=0;assert(!af_v3_creature_passport_save(active,animal,(void *)123));
    assert(!memcmp(before,af_save_live,sizeof(before)));
    pak_ok=1;assert(af_v3_creature_passport_save(active,animal,(void *)123));
    expect_clean(active,before+0x20+2*PRIVATE);assert(!checksum(pak));
    assert(af_v3_creature_passport_load(foreign,animal,(void *)123));
    assert(!memcmp(foreign,active,PRIVATE) && visitor.collected[0]==4);
    /* Returning visitors use the same temporary native private-copy route. */
    seed();
    memcpy(foreign,active,PRIVATE);foreign[0]^=0x80;
    memcpy(visitor.identity,foreign,16);visitor.valid=0x41464354;
    for(unsigned i=0;i<4;i++)visitor.profile[i]=af_v3_creature_profile_byte(i);
    visitor.collected[0]=16;memcpy(temporary,foreign,PRIVATE);
    assert(af_v3_creature_passport_save(temporary,animal,(void *)123));
    expect_clean(temporary,foreign);assert(pak[CAPSULE+28]==16 && !checksum(pak));
    temporary[0]^=1;unsigned count=pak_writes;
    assert(!af_v3_creature_passport_save(temporary,animal,(void *)123) && pak_writes==count);
    seed();enabled=0;assert(!af_cw_save_sync());assert(!memcmp(before,af_save_live,sizeof(before)));
    puts("pass: staged spirit cleanup, all conditions/quantities, reset saves, both bank failures, Pak snapshots, and success-only live changes");
}
