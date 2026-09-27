#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/creature_travel.c"

u8 af_creature_players[4*PRIVATE],af_travel_foreign[PRIVATE],af_travel_passport[PASSPORT];
u8 *af_creature_active;
u32 af_travel_loaded;
struct AfSaveRuntime af_creature_collection_state;
struct Visitor af_travel_visitor;
static u8 disk[PASSPORT];
static unsigned mask=0x1FFFF,writes,read_ok=1,write_ok=1;
static jmp_buf failure;
static int expected_error;
extern int af_v3_creature_collected(u8 *,unsigned,unsigned,unsigned);

u32 af_v3_creature_profile_byte(u32 i) {return i<3 ? (mask>>(i*8))&255 : 0;}
int af_creature_item_type(u32 id) {
    unsigned i=id>=0x2320 && id<=0x2328 ? id-0x2320 : id>=0x2D20 && id<=0x2D27 ? id-0x2D20+9 : 17;
    return i<17 && (mask&(1u<<i)) ? (i<9 ? 8 : 18) : 0;
}
int af_creature_save_collect(u8 *s,u32 n,u32 id,u32 mark) {
    unsigned i=id<0x2D00 ? id-0x2320 : id-0x2D20+9;
    assert(n<4 && i<17 && af_creature_item_type(id));
    u8 *b=s+AF_SAVE_CREATURE_OFFSET+4+n*4+i/8;
    if (mark) *b|=1u<<(i&7);
    return !!(*b&(1u<<(i&7)));
}
void af_v3_require_save_state(void) {
    for (unsigned i=0;i<4;i++) assert(state->working[AF_SAVE_CREATURE_OFFSET+i]==af_v3_creature_profile_byte(i));
}
void af_v3_save_halt(int error) {assert(error==expected_error);longjmp(failure,1);}
void af_pak_set_kind(void *info,unsigned kind) {assert(info==(void *)123 && kind==0);}
int af_pak_read(void *info,void *p) {
    assert(info==(void *)123);if (!read_ok) return 0;memcpy(p,disk,PASSPORT);return 1;
}
int af_pak_write(void *info,const void *p) {
    assert(info==(void *)123);writes++;if (!write_ok) return 0;memcpy(disk,p,PASSPORT);return 1;
}
int af_pak_check_private(const u8 *p) {return p[14]==0x30 && p[15];}
void af_pak_clear_private(u8 *p) {memset(p,0,PRIVATE);}
void af_pak_clear_animal(u8 *p) {memset(p,0,0x528);}
static void set_mask(unsigned m) {
    mask=m;for (unsigned i=0;i<4;i++) state->working[AF_SAVE_CREATURE_OFFSET+i]=af_v3_creature_profile_byte(i);
}
static void identity(u8 *p,unsigned n) {
    for (unsigned i=0;i<12;i++) p[i]=(u8)('A'+n+i);
    p[12]=0xF0;p[13]=n;p[14]=0x30;p[15]=n+1;
}
static void rejects(void) {
    u8 before[PRIVATE],animal[0x528],saved[AF_SAVE_STATE];struct Visitor v=visitor;
    memcpy(before,foreign,PRIVATE);memset(animal,0xA5,sizeof(animal));memcpy(saved,state->working,sizeof(saved));
    assert(!af_v3_creature_passport_load(foreign,animal,(void *)123));
    assert(!memcmp(before,foreign,PRIVATE) && !memcmp(saved,state->working,sizeof(saved)) && !memcmp(&v,&visitor,sizeof(v)));
    for (unsigned i=0;i<sizeof(animal);i++) assert(animal[i]==0xA5);
}
int main(void) {
    u8 animal[0x528],received[0x528],saved[AF_SAVE_STATE],original[PASSPORT];
    memset(animal,0xCD,sizeof(animal));set_mask(0x1FFFF);
    for (unsigned n=0;n<4;n++) identity(players+n*PRIVATE,n);
    /* Each resident's independent history follows that identity through the
     * native save/load/copy path without changing another resident. */
    for (unsigned n=0;n<4;n++) {
        memset(state->working+AF_SAVE_CREATURE_OFFSET+4,0,16);
        u8 *priv=players+n*PRIVATE;
        assert(af_v3_creature_collected(priv,0,32+n,1));
        af_v3_creature_passport_clear(passport);
        assert(af_v3_creature_passport_save(priv,animal,(void *)123)==1 && !checksum(disk));
        assert(!memcmp(disk+8,priv,PRIVATE) && !memcmp(disk+0xBD8,animal,sizeof(animal)));
        assert(disk[0x1100]==255 && disk[0x1101]==255);
        memcpy(saved,state->working,sizeof(saved));
        memset(&visitor,0,sizeof(visitor));memset(foreign,0,PRIVATE);
        assert(af_v3_creature_passport_load(foreign,received,(void *)123)==1);
        assert(!memcmp(received,animal,sizeof(animal)) && !memcmp(saved,state->working,sizeof(saved)));
        assert(af_v3_creature_collected(foreign,0,32+n,0));
        for (unsigned i=0;i<17;i++) {
            unsigned kind=i>=9,index=i<9 ? i+32 : i-9+32;
            assert(af_v3_creature_collected(foreign,kind,index,1));
        }
        assert(!memcmp(saved,state->working,sizeof(saved)));
        assert(af_v3_creature_passport_save(foreign,received,(void *)123)==1);
        /* A fresh process has no visitor state; only the passport carries it. */
        memset(&visitor,0,sizeof(visitor));memset(foreign,0,PRIVATE);
        assert(af_v3_creature_passport_load(foreign,received,(void *)123)==1);
        for (unsigned i=0;i<17;i++) assert(af_v3_creature_collected(foreign,i>=9,i<9 ? i+32 : i-9+32,0));
        af_v3_creature_private_copy(priv,foreign);
        for (unsigned k=0;k<4;k++) {
            const u8 *bits=state->working+AF_SAVE_CREATURE_OFFSET+4+k*4;
            assert(bits[0]==(k==n ? 255 : 0) && bits[1]==(k==n ? 255 : 0) && bits[2]==(k==n ? 1 : 0) && bits[3]==0);
        }
        assert(!memcmp(priv,foreign,PRIVATE));
    }
    memcpy(original,disk,sizeof(original));
    /* Failure never copies native data or commits an extended record. */
    read_ok=0;rejects();read_ok=1;
    disk[100]^=1;rejects();memcpy(disk,original,sizeof(disk));
    disk[CAPSULE+28]^=1;seal(disk);rejects();memcpy(disk,original,sizeof(disk));
    disk[2]^=1;seal(disk);rejects();memcpy(disk,original,sizeof(disk));
    disk[8]^=1;seal(disk);rejects();memcpy(disk,original,sizeof(disk));
    disk[CAPSULE+7]=49;put(disk+CAPSULE+32,crc(disk+CAPSULE,32));
    put(disk+CAPSULE+36,~word(disk+CAPSULE+32));seal(disk);rejects();memcpy(disk,original,sizeof(disk));
    set_mask(0xFF);rejects();set_mask(0x1FFFF);
    /* Reject an unrelated resident even with a valid, supported passport. */
    u8 snapshot[PRIVATE];memcpy(snapshot,players,PRIVATE);
    assert(!af_v3_creature_passport_load(players,received,(void *)123));
    assert(!memcmp(snapshot,players,PRIVATE));
    expected_error=AF_SAVE_BINDING;
    if (!setjmp(failure)) {af_v3_creature_private_copy(players,foreign);abort();}
    assert(!memcmp(snapshot,players,PRIVATE));
    /* Device failure is reported, not success; the stored note is unchanged. */
    memcpy(original,disk,sizeof(original));write_ok=0;
    assert(!af_v3_creature_passport_save(foreign,animal,(void *)123));
    assert(!memcmp(original,disk,sizeof(disk)));write_ok=1;
    /* Legacy transport initializes only the visitor. Home records survive. */
    memset(disk+2,0,6);memset(disk+CAPSULE,0,CAPSULE_BYTES);seal(disk);
    assert(af_v3_creature_passport_load(foreign,received,(void *)123));
    for (unsigned i=0;i<4;i++) assert(visitor.collected[i]==0);
    memcpy(saved,state->working,sizeof(saved));
    af_v3_creature_private_copy(players+3*PRIVATE,foreign);
    assert(!memcmp(saved,state->working,sizeof(saved)));
    assert(af_v3_creature_collected(foreign,0,40,1));
    assert(visitor.profile[1]==1 && visitor.collected[1]==1);
    assert(af_v3_creature_passport_save(foreign,animal,(void *)123));
    set_mask(0xFF);rejects();set_mask(0x1FFFF);
    /* Clearing a passport removes both markers and records, not its nonce. */
    af_v3_creature_passport_clear(passport);
    for (unsigned i=0;i<8;i++) assert(!passport[i]);
    for (unsigned i=0;i<CAPSULE_BYTES;i++) assert(!passport[CAPSULE+i]);
    assert(passport[0x1100]==255 && passport[0x1101]==255 && writes==10);
    puts("pass: all 17 records, four residents, visitor isolation, passport round trips, legacy merge, corruption/profile/identity rejection and device failures");
}
