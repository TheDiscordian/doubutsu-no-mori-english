#include "bank_native.h"
#include "bank_pelly.h"
#include <assert.h>
#include <string.h>
typedef unsigned int u32;
static union {u32 aligned;unsigned char bytes[0x40];} private;
static unsigned char record[48],submenu[0xF0],overlay[0x10730];
void *af_bank_now_private;
unsigned char af_bank_player;
unsigned char af_bank_account_mode=1,af_bank_home_arrangement,af_bank_native_homes[4*0xB48];
static int set_calls,pre_calls,draw_calls,move_calls,end_calls,close_calls;
static void *pointers[16];static unsigned int offsets[16],pointer_count;
static void *pointer_owners[16];
static u32 word(const unsigned char *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(unsigned char *p,u32 n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
unsigned char *af_bank_native_account(void) {return record;}
void *af_bank_test_pointer(const void *p,unsigned int at) {
    for(u32 i=0;i<pointer_count;i++)if(p==pointer_owners[i] && at==offsets[i])return pointers[i];
    return 0;
}
void af_bank_test_store_pointer(void *p,unsigned int at,void *value) {
    for(u32 i=0;i<pointer_count;i++)if(p==pointer_owners[i] && at==offsets[i]) {pointers[i]=value;return;}
    assert(pointer_count<16);pointer_owners[pointer_count]=p;offsets[pointer_count]=at;
    pointers[pointer_count++]=value;
}
void af_bank_native_set_pocket(void *p,int slot,unsigned short item,unsigned int condition) {
    assert(p==private.bytes && slot>=0 && slot<15 && condition<4);
    unsigned char *b=p;set_calls++;b[0x14+slot*2]=item>>8;b[0x15+slot*2]=item;
    u32 c=word(b+0x34);c=(c&~(3u<<(2*slot)))|(condition<<(2*slot));put(b+0x34,c);
}
void af_bank_native_sound(unsigned int n) {assert(n);}
static void pre(void *s) {assert(s==submenu);pre_calls++;}
static void pre_draw(void *s,void *g) {assert(s==submenu && g);draw_calls++;}
static void move(void *s,void *m) {assert(s==submenu && m==overlay+0x10280);move_calls++;put((unsigned char *)m+4,1);}
static void end(void *s,void *m) {assert(s==submenu && m==overlay+0x10280);end_calls++;}
static void close(void *m,int direction) {assert(m==overlay+0x10280 && direction==4);close_calls++;put((unsigned char *)m+4,4);}
static void matrix(void *g) {assert(g);}
extern void af_bank_test_native_draw(void *,void (*)(void *,void *));
void af_bank_native_test(void) {
    memset(private.bytes,0xA5,sizeof(private.bytes));memset(submenu,0,sizeof(submenu));memset(overlay,0,sizeof(overlay));
    af_bank_now_private=private.bytes;af_bank_player=0;assert(af_bank_reset(record,48));
    put(private.bytes+0x3C,0);memcpy(af_bank_native_homes,private.bytes,16);
    af_bank_native_homes[0x22]=0x80;
    put(private.bytes+0x38,99999);put(private.bytes+0x34,0xC0000008u);
    for(u32 i=0;i<15;i++)private.bytes[0x14+2*i]=private.bytes[0x15+2*i]=0;
    private.bytes[0x14]=0x21;private.bytes[0x15]=2;
    private.bytes[0x16]=0x32;private.bytes[0x17]=0x94;
    AFBankWallet wallet;assert(af_bank_native_wallet(private.bytes,&wallet));
    assert(wallet.wallet==99999 && wallet.items[0]==0x2102 && wallet.items[1]==0x3294 && wallet.conditions[1]==2);
    af_bank_test_store_pointer(submenu,0x2C,overlay);
    af_bank_test_store_pointer(overlay,0x1028C,(void *)pre);
    af_bank_test_store_pointer(overlay,0x10290,(void *)pre_draw);
    af_bank_test_store_pointer(overlay,0x106A8,(void *)move);
    af_bank_test_store_pointer(overlay,0x106AC,(void *)end);
    af_bank_test_store_pointer(overlay,0x106B0,(void *)close);
    af_bank_test_store_pointer(overlay,0x106B4,(void *)matrix);
    assert(!af_bank_native_construct(submenu) && !af_bank_native_set_proc(submenu) && !af_bank_native_destruct(submenu));
    assert(af_bank_native_request(submenu)==1);assert(af_bank_native_request(submenu)==0);put(submenu+4,7);
    assert(af_bank_native_construct(submenu)==1 && af_bank_native_set_proc(submenu)==1);
    assert(word(overlay+0x10284)==0 && word(overlay+0x102B0)==1 && word(overlay+0x102B4)==5);
    void (*mover)(void *)=af_bank_test_pointer(overlay,0x10670);
    mover(submenu);assert(pre_calls==1 && move_calls==1);
    af_bank_test_native_draw(submenu,af_bank_test_pointer(overlay,0x10674));assert(draw_calls==1);
    put(overlay+0x1068C,8);mover(submenu);assert(!set_calls && word(private.bytes+0x38)==99999);
    unsigned char before_private[0x40];memcpy(before_private,private.bytes,sizeof(before_private));
    put(overlay+0x1068C,0x1000);mover(submenu);
    assert(set_calls==1 && word(private.bytes+0x38)==29999 && close_calls==1 && word(record+16)==100000);
    assert(word(private.bytes+0x34)==0xC0000008u);
    for(u32 i=0;i<sizeof(private.bytes);i++)if(i!=0x14 && i!=0x15 && !(i>=0x38 && i<0x3C))
        assert(private.bytes[i]==before_private[i]);
    mover(submenu);assert(end_calls==1);assert(af_bank_native_destruct(submenu)==1 && !af_bank_frontend_active());
    /* Stale native state and malformed proposals reject before native setters. */
    unsigned char before[48],after[48];memcpy(before,record,48);memcpy(after,record,48);
    assert(af_bank_native_wallet(private.bytes,&wallet));AFBankWallet next=wallet;next.wallet--;
    put(after+16,100001);int count=set_calls;
    private.bytes[0x39]^=1;
    assert(!af_bank_native_commit(record,before,after,private.bytes,&wallet,&next) && set_calls==count);
    private.bytes[0x39]^=1;after[24]=1;
    assert(!af_bank_native_commit(record,before,after,private.bytes,&wallet,&next) && set_calls==count);
    memcpy(after,before,48);put(after+16,100001);next.items[1]=0;
    assert(!af_bank_native_commit(record,before,after,private.bytes,&wallet,&next) && set_calls==count);
    af_bank_account_mode=0;put(submenu+4,0);assert(!af_bank_native_request(submenu));af_bank_account_mode=1;
    put(private.bytes+0x3C,1);assert(!af_bank_native_request(submenu));put(private.bytes+0x3C,0);
    af_bank_player=4;assert(!af_bank_native_request(submenu));af_bank_player=0;
    /* Forced closing retains bank ownership until the ordinary native dtor. */
    assert(af_bank_native_request(submenu)==1);put(submenu+4,7);
    assert(af_bank_native_construct(submenu)==1);
    count=close_calls;assert(af_bank_native_cancel(submenu)==1 && close_calls==count+1);
    assert(af_bank_frontend_active() && af_bank_native_destruct(submenu)==1);
    /* Cancelling an admitted request before construction is an owned failure,
     * never an invitation to open the old loan repayment menu. */
    put(submenu+4,0);assert(af_bank_native_request(submenu)==1);
    assert(af_bank_native_cancel(submenu)==1);put(submenu+4,7);
    assert(af_bank_native_construct(submenu)==-1 && !af_bank_frontend_active());
}
