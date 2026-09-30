#include "bank_account.h"
typedef af_bank_u8 u8;
typedef af_bank_u32 u32;
typedef __UINTPTR_TYPE__ address;
static int busy;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static u32 half(const u8 *p) {return (u32)p[0]<<8|p[1];}
static void put(u8 *p,u32 v) {p[0]=(u8)(v>>24);p[1]=(u8)(v>>16);p[2]=(u8)(v>>8);p[3]=(u8)v;}
static int overlap(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    return !a || !b || x+an<x || y+bn<y || (x<y+bn && y<x+an);
}
int af_bank_valid(const u8 *data,u32 bytes) {
    if(!data || bytes!=AF_BANK_BYTES || word(data)!=0x41464241 ||
        data[4]!=1 || data[5]!=4 || data[6]!=8 || data[7] || data[8]>1)return 0;
    for(u32 i=9;i<16;i++)if(data[i])return 0;
    for(u32 i=0;i<4;i++) {
        const u8 *p=data+16+i*8;
        if(word(p)>AF_BANK_MAX || p[4]&~0x3Cu || p[5] || p[6] || p[7] ||
            (!data[8] && (word(p) || p[4])))return 0;
    }
    return 1;
}
int af_bank_reset(u8 *data,u32 bytes) {
    if(busy || !data || bytes!=AF_BANK_BYTES)return 0;
    for(u32 i=0;i<bytes;i++)data[i]=0;
    put(data,0x41464241);data[4]=1;data[5]=4;data[6]=8;return 1;
}
int af_bank_clear(u8 *data,u32 bytes,u32 player) {
    if(busy || player>=4 || !af_bank_valid(data,bytes))return 0;
    for(u32 i=0;i<8;i++)data[16+player*8+i]=0;
    return 1;
}
int af_bank_get(const u8 *data,u32 bytes,u32 player,AFBankAccount *out) {
    if(player>=4 || !af_bank_valid(data,bytes) || overlap(data,bytes,out,sizeof(*out)))return 0;
    out->balance=word(data+16+player*8);out->received=data[20+player*8];return 1;
}
int af_bank_required(const u8 *data,u32 bytes) {return af_bank_valid(data,bytes)?data[8]:-1;}
int af_bank_eligible(u32 resident,u32 loan,u32 size,u32 renewing) {
    return resident==1 && !loan && size>=3 && !renewing;
}
static int same_wallet(const AFBankWallet *a,const AFBankWallet *b) {
    if(a->wallet!=b->wallet)return 0;
    for(u32 i=0;i<15;i++)if(a->items[i]!=b->items[i] || a->conditions[i]!=b->conditions[i])return 0;
    return 1;
}
static u32 money(u32 item) {
    return item==0x2103?100:item==0x2100?1000:item==0x2101?10000:item==0x2102?30000:0;
}
static int cash(const AFBankWallet *wallet,u32 *total) {
    if(!wallet || wallet->wallet>AF_BANK_WALLET_MAX)return 0;
    *total=wallet->wallet;
    for(u32 i=0;i<15;i++) {
        if(wallet->conditions[i]>3)return 0;
        if(!wallet->conditions[i])*total+=money(wallet->items[i]);
    }
    return 1;
}
int af_bank_begin(const u8 *data,u32 bytes,u32 player,int eligible,
    const AFBankWallet *wallet,AFBankTransaction *tx) {
    AFBankAccount a;u32 total;
    if(busy || eligible!=1 || !af_bank_get(data,bytes,player,&a) ||
        overlap(data,bytes,wallet,sizeof(*wallet)) || !cash(wallet,&total) ||
        overlap(data,bytes,tx,sizeof(*tx)) || overlap(wallet,sizeof(*wallet),tx,sizeof(*tx)))return 0;
    AFBankTransaction next={0};next.original=*wallet;next.player=player;
    next.balance=a.balance;next.received=a.received;next.open=1;
    if(!af_bank_source_init(&next.menu,wallet,a.balance))return 0;
    *tx=next;return 1;
}
int af_bank_step(u8 *data,u32 bytes,u32 player,int eligible,
    AFBankWallet *wallet,AFBankTransaction *tx,u32 trigger) {
    AFBankAccount a;AFBankMenu initial;u32 before,after;
    if(busy || eligible!=1 || !tx || tx->open!=1 || player!=tx->player ||
        !af_bank_get(data,bytes,player,&a) || !cash(wallet,&before) ||
        overlap(data,bytes,wallet,sizeof(*wallet)) || overlap(data,bytes,tx,sizeof(*tx)) ||
        overlap(wallet,sizeof(*wallet),tx,sizeof(*tx)) ||
        a.balance!=tx->balance || a.received!=tx->received || !same_wallet(wallet,&tx->original) ||
        !af_bank_source_init(&initial,wallet,a.balance))return AF_BANK_ERROR;
    const AFBankMenu *m=&tx->menu;
    int delta=m->now_bell-(int)before;
    if(m->cursol<0 || m->cursol>6 || m->bank_bell<0 || m->bank_bell>AF_BANK_MAX ||
        m->now_bell<0 || m->now_bell>initial.player_max_bell ||
        m->player_bell!=initial.player_bell || m->player_max_bell!=initial.player_max_bell ||
        (u32)m->bank_bell+(u32)m->now_bell!=a.balance+before ||
        m->bell!=(delta<0?-delta:delta))return AF_BANK_ERROR;
    AFBankMenu next_menu=*m;AFBankWallet next=*wallet;u32 balance=a.balance,sound=0;
    int result=af_bank_source_step(&next_menu,&next,&balance,trigger,&sound);
    if(result==AF_BANK_CANCEL) {tx->sound=sound;tx->open=0;return result;}
    if(result==AF_BANK_PREVIEW) {tx->sound=sound;tx->menu=next_menu;return result;}
    if(result!=AF_BANK_CONFIRM || balance>AF_BANK_MAX || !cash(&next,&after) ||
        balance+after!=a.balance+before)return AF_BANK_ERROR;
    for(u32 i=0;i<15;i++) {
        if(next.conditions[i]!=wallet->conditions[i] ||
            (wallet->conditions[i] && next.items[i]!=wallet->items[i]) ||
            (wallet->items[i] && !money(wallet->items[i]) && next.items[i]!=wallet->items[i]))
            return AF_BANK_ERROR;
    }
    /* No failure-prone service runs between validation and these publications.
     * Native bridge writes must use the same checked transaction boundary. */
    *wallet=next;put(data+16+player*8,balance);data[8]=1;
    tx->sound=sound;tx->menu=next_menu;tx->open=0;return AF_BANK_CONFIRM;
}
int af_bank_send_rewards(u8 *data,u32 bytes,const u8 *rows,u32 rows_bytes,const AFBankMailOps *ops) {
    if(busy || !af_bank_valid(data,bytes) || !rows || rows_bytes!=64 ||
        !ops || !ops->exists || !ops->resolve || !ops->submit ||
        overlap(data,bytes,rows,rows_bytes) || overlap(data,bytes,ops,sizeof(*ops)))return -1;
    u32 previous=0;
    for(u32 i=0;i<4;i++) {
        const u8 *p=rows+i*16;u32 threshold=word(p+12);
        if(!word(p) || word(p)>65535 || !half(p+4) || !half(p+6) ||
            word(p+8)!=(4u<<i) || threshold<=previous || threshold>AF_BANK_MAX)return -1;
        previous=threshold;
    }
    int sent=0;busy=1;
    for(u32 player=0;player<4;player++) {
        if(ops->exists(ops->context,player)!=1)continue;
        u8 *account=data+16+player*8;
        for(u32 i=0;i<4;i++) {
            const u8 *p=rows+i*16;u32 mask=word(p+8);
            if(word(account)<word(p+12) || (account[4]&mask))continue;
            u32 item=ops->resolve(ops->context,half(p+4));
            if(!item)continue;
            if(item>65535) {busy=0;return -1;}
            if(ops->submit(ops->context,player,item,half(p+6),word(p))==1) {
                account[4]|=(u8)mask;data[8]=1;sent++;
            }
            break;
        }
    }
    busy=0;return sent;
}
