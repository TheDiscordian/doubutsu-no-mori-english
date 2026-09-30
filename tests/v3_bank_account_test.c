#include "bank_account.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned char ledger[AF_BANK_BYTES],rewards[64];
static AFBankWallet wallet;
static AFBankTransaction tx;
static void put(unsigned char *p,unsigned v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static unsigned balance(unsigned player) {
    AFBankAccount a;assert(af_bank_get(ledger,sizeof ledger,player,&a));return a.balance;
}
static unsigned received(unsigned player) {
    AFBankAccount a;assert(af_bank_get(ledger,sizeof ledger,player,&a));return a.received;
}
static void seed(unsigned player,unsigned amount) {ledger[8]=1;put(ledger+16+player*8,amount);}
static void reset(void) {
    assert(af_bank_reset(ledger,sizeof ledger));memset(&wallet,0,sizeof wallet);memset(&tx,0,sizeof tx);
}
static int step(unsigned player,unsigned buttons) {
    return af_bank_step(ledger,sizeof ledger,player,1,&wallet,&tx,buttons);
}
static void cursor(unsigned player,int n) {
    while(tx.menu.cursol<n)assert(step(player,1)==AF_BANK_PREVIEW);
    while(tx.menu.cursol>n)assert(step(player,2)==AF_BANK_PREVIEW);
}
static void record_and_ownership(void) {
    reset();assert(af_bank_valid(ledger,sizeof ledger));assert(!af_bank_required(ledger,sizeof ledger));
    for(unsigned p=0;p<4;p++)assert(!balance(p) && !received(p));
    assert(!af_bank_valid(ledger,sizeof ledger-1));
    for(unsigned p=0;p<4;p++) {
        wallet.wallet=1000+p;
        assert(af_bank_begin(ledger,sizeof ledger,p,1,&wallet,&tx));
        cursor(p,2);assert(step(p,8)==AF_BANK_PREVIEW);assert(!balance(p));
        assert(step(p,0x1000)==AF_BANK_CONFIRM);assert(balance(p)==1000);assert(wallet.wallet==p);
    }
    assert(af_bank_required(ledger,sizeof ledger)==1);
    assert(af_bank_clear(ledger,sizeof ledger,1));assert(!balance(1));assert(balance(0)==1000);
    assert(balance(2)==1000 && balance(3)==1000);assert(af_bank_required(ledger,sizeof ledger)==1);
    unsigned char old[AF_BANK_BYTES];memcpy(old,ledger,sizeof old);
    assert(!af_bank_clear(ledger,sizeof ledger,4));assert(!memcmp(old,ledger,sizeof old));
    ledger[21]=1;assert(!af_bank_valid(ledger,sizeof ledger));memcpy(ledger,old,sizeof old);
    seed(1,AF_BANK_MAX+1u);assert(!af_bank_valid(ledger,sizeof ledger));memcpy(ledger,old,sizeof old);
    ledger[20]=1;assert(!af_bank_valid(ledger,sizeof ledger));memcpy(ledger,old,sizeof old);
    ledger[8]=0;assert(!af_bank_valid(ledger,sizeof ledger));
    reset();assert(af_bank_eligible(1,0,3,0));assert(af_bank_eligible(1,0,4,0));
    assert(!af_bank_eligible(0,0,4,0));assert(!af_bank_eligible(1,1,4,0));
    assert(!af_bank_eligible(1,0,2,0));assert(!af_bank_eligible(1,0,3,1));
    assert(!af_bank_begin(ledger,sizeof ledger,4,1,&wallet,&tx));
    assert(!af_bank_begin(ledger,sizeof ledger,0,0,&wallet,&tx));
    assert(!af_bank_begin(ledger,sizeof ledger,0,1,&wallet,(AFBankTransaction *)ledger));
}
static void source_controls_and_cancellation(void) {
    reset();wallet.wallet=2000;wallet.items[0]=0x2103;wallet.items[1]=0x2100;
    wallet.items[2]=0x2101;wallet.items[3]=0x2102;wallet.items[4]=0x1234;
    wallet.items[5]=0x2102;wallet.conditions[5]=1;
    AFBankWallet original=wallet;unsigned char old[AF_BANK_BYTES];memcpy(old,ledger,sizeof old);
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));
    assert(tx.menu.player_bell==43100);assert(tx.menu.player_max_bell==489999);
    cursor(0,2);assert(step(0,8)==AF_BANK_PREVIEW);assert(tx.menu.bank_bell==1000);
    assert(tx.sound==0x426);assert(!memcmp(&original,&wallet,sizeof wallet));
    assert(!memcmp(old,ledger,sizeof old));
    assert(step(0,0x5000)==AF_BANK_CANCEL);assert(tx.sound==2);
    assert(!memcmp(&original,&wallet,sizeof wallet));assert(!memcmp(old,ledger,sizeof old));
    assert(step(0,0x1000)==AF_BANK_ERROR);
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));
    assert(step(0,8)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==0);
    cursor(0,6);assert(step(0,0x8000)==AF_BANK_CONFIRM);assert(balance(0)==43100);
    assert(wallet.wallet==0);
    for(int i=0;i<4;i++)assert(!wallet.items[i]);
    assert(wallet.items[4]==0x1234 && wallet.items[5]==0x2102 && wallet.conditions[5]==1);
    /* Crossing the opening balance in either direction stops exactly there. */
    reset();seed(0,1000000);wallet.wallet=1500;
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));cursor(0,2);
    assert(step(0,8)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==500);
    cursor(0,0);assert(step(0,4)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==1500);
    assert(step(0,4)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==101500);
    assert(step(0,8)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==1500);
    assert(step(0,0x4000)==AF_BANK_CANCEL);assert(balance(0)==1000000 && wallet.wallet==1500);
}
static void source_capacity_and_stale_state(void) {
    reset();seed(2,1000000);
    assert(af_bank_begin(ledger,sizeof ledger,2,1,&wallet,&tx));
    for(int i=0;i<6;i++)assert(step(2,4)==AF_BANK_PREVIEW);
    assert(tx.menu.now_bell==549999 && tx.menu.bank_bell==450001);
    assert(step(2,0x1000)==AF_BANK_CONFIRM);assert(balance(2)==450001 && wallet.wallet==99999);
    for(int i=0;i<15;i++)assert(wallet.items[i]==0x2102 && !wallet.conditions[i]);
    reset();seed(0,1000000);
    for(int i=0;i<15;i++)wallet.items[i]=0x1234;
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));
    assert(step(0,4)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==99999);
    assert(step(0,0x1000)==AF_BANK_CONFIRM);assert(wallet.wallet==99999 && balance(0)==900001);
    for(int i=0;i<15;i++)assert(wallet.items[i]==0x1234);
    reset();seed(1,AF_BANK_MAX-50);wallet.wallet=200;
    assert(af_bank_begin(ledger,sizeof ledger,1,1,&wallet,&tx));
    assert(step(1,8)==AF_BANK_PREVIEW);assert(tx.menu.now_bell==150);
    assert(step(1,8)==AF_BANK_PREVIEW);assert(tx.sound==0x1003);
    assert(step(1,0x1000)==AF_BANK_CONFIRM);assert(balance(1)==AF_BANK_MAX && wallet.wallet==150);
    reset();wallet.wallet=5000;
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));cursor(0,2);
    assert(step(0,8)==AF_BANK_PREVIEW);wallet.wallet++;
    unsigned char old[AF_BANK_BYTES];memcpy(old,ledger,sizeof old);
    assert(step(0,0x1000)==AF_BANK_ERROR);assert(!memcmp(old,ledger,sizeof old));assert(wallet.wallet==5001);
    wallet.wallet--;tx.menu.bank_bell++;
    assert(step(0,0x1000)==AF_BANK_ERROR);assert(!memcmp(old,ledger,sizeof old));
    assert(af_bank_begin(ledger,sizeof ledger,0,1,&wallet,&tx));
    assert(step(1,0x1000)==AF_BANK_ERROR);
    assert(af_bank_step(ledger,sizeof ledger,0,0,&wallet,&tx,0x1000)==AF_BANK_ERROR);
    assert(af_bank_step(ledger,sizeof ledger,0,1,&wallet,&tx,0)==AF_BANK_PREVIEW);
}
static int mail_attempts,mail_success,disabled,absent;
static unsigned last_player,last_template,last_item;
static int exists(void *ctx,unsigned player) {(void)ctx;return player!=(unsigned)absent;}
static unsigned resolve(void *ctx,unsigned source) {(void)ctx;return source==(unsigned)disabled?0:source;}
static int submit(void *ctx,unsigned player,unsigned item,unsigned paper,unsigned template) {
    (void)ctx;assert(paper==0x2000);last_player=player;last_item=item;last_template=template;mail_attempts++;
    /* Re-entrant account mutation cannot race the real delivery/receipt boundary. */
    assert(!af_bank_clear(ledger,sizeof ledger,player));assert(!af_bank_reset(ledger,sizeof ledger));
    return mail_success;
}
static void source_milestones_and_receipts(void) {
    reset();AFBankMailOps ops={0,exists,resolve,submit};absent=-1;disabled=0;mail_success=0;mail_attempts=0;
    seed(0,999999);assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==0);assert(!mail_attempts);
    seed(0,AF_BANK_MAX);
    assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==0);
    assert(mail_attempts==1 && !received(0));assert(last_template==0x246 && last_item==0x1FB0);
    mail_success=2;assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==0);assert(!received(0));
    mail_success=1;
    for(unsigned i=0;i<4;i++) {
        int before=mail_attempts;
        assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==1);
        assert(mail_attempts==before+1 && last_template==0x246+i && last_player==0);
    }
    assert(received(0)==0x3C);assert(!af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops));
    reset();seed(3,AF_BANK_MAX);disabled=0x1FB0;absent=3;mail_attempts=0;
    assert(!af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops));assert(!mail_attempts);
    absent=-1;assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==1);
    assert(last_player==3 && last_template==0x247 && received(3)==8);
    assert(!balance(0) && !received(0));
    unsigned char old[64];memcpy(old,rewards,64);rewards[11]^=1;
    assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,64,&ops)==-1);memcpy(rewards,old,64);
    assert(af_bank_send_rewards(ledger,sizeof ledger,rewards,63,&ops)==-1);
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    assert(fread(rewards,1,sizeof rewards,f)==sizeof rewards);assert(fgetc(f)==EOF);fclose(f);
    record_and_ownership();source_controls_and_cancellation();source_capacity_and_stale_state();source_milestones_and_receipts();
    puts("bank account: donor controls, bags, cancellation, snapshots, ownership, and mail receipts pass");return 0;
}
