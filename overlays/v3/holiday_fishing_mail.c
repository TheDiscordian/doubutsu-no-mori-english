/* Complete winner-mail path, reusing the translation's immutable English
 * catalogue, saved snapshots, native mailbox, and post-office delivery. */
#include "holiday_fishing_mail.h"
typedef unsigned int u32;
typedef struct {
    AfMailWorkspace catalogue;
    AfMailText text;
    AFHolidayFish acknowledged;
    AFHFB next_wire[AF_HF_BYTES],mail[164];
    AFHFB snapshot[128] __attribute__((aligned(16)));
} MailWork;
static u32 word(const AFHFB *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static int same(const AFHFB *a,const AFHFB *b,u32 n) {
    for(u32 i=0;i<n;i++)if(a[i]!=b[i])return 0;
    return 1;
}
static int eligible(u32 item,u32 player,int unowned) {
    const AFHFB *p=af_hf_native_players[player];
    if((item>>12)==3) {
        if(!af_hf_mail_selected(1024+((item&4095)>>2)))return 0;
        return !unowned || !af_hf_mail_owned(p,item);
    }
    if(item<0x1000 || item>=0x1ECC || (item&3))return 0;
    u32 index=(item-0x1000)>>2;
    return !unowned || !(word(p+0xAF0+(index>>5)*4)>>(index&31)&1);
}
static u32 choose(u32 group,u32 player,int unowned) {
    u32 first=af_hf_prize_limits[group],last=af_hf_prize_limits[group+1],count=0;
    if(first>=last || last>103)return 0;
    for(u32 i=first;i<last;i++)count+=eligible(af_hf_prizes[i],player,unowned);
    if(!count)return 0;
    /* The donor's general fallback rejects the current rare item. Keep its
       rejection sampling, but refuse a profile containing only that item. */
    if(!unowned && count==1 && eligible(af_hf_native_rare,player,0)) {
        for(u32 i=first;i<last;i++)
            if(af_hf_prizes[i]!=af_hf_native_rare && eligible(af_hf_prizes[i],player,0))goto usable;
        return 0;
    }
usable:
    for(;;) {
        u32 pick=(u32)(af_hf_random(&af_hf_live.records)*count);
        if(af_hf_live.records.error || pick>=count)return 0;
        for(u32 i=first;i<last;i++)if(eligible(af_hf_prizes[i],player,unowned) && !pick--) {
            if(unowned || af_hf_prizes[i]!=af_hf_native_rare)return af_hf_prizes[i];
            break;
        }
    }
}
u32 af_hf_mail_prize(u32 player) {
    if(player>=4 || af_hf_live.active!=2)return 0;
    u32 group=((u32)(af_hf_random(&af_hf_live.records)*100)&1)?0:1;
    if(af_hf_live.records.error)return 0;
    u32 item=choose(group,player,1);
    if(!item)item=choose(group^1,player,1);
    if(item)return item;
    group=((u32)(af_hf_random(&af_hf_live.records)*100)&1)?0:1;
    return af_hf_live.records.error?0:choose(group,player,0);
}
static int make(MailWork *w,const AFHFRecord *winner,u32 player) {
    u32 gift=af_hf_mail_prize(player);
    if(!gift || af_mail_generation_capital>1)return 0;
    af_hf_mail_clear(w->mail);
    af_hf_copy(w->mail,af_hf_native_players[player],16);
    w->mail[16]=0;w->mail[36]=gift>>8;w->mail[37]=gift;
    w->mail[38]=0;w->mail[39]=0x80;w->mail[40]=9;w->mail[41]=15;
    AfMailRecord *r=&w->catalogue.record;
    af_hf_clear(r,sizeof(*r),0);
    r->catalog=4;r->flags=(AFHFB)af_mail_generation_capital;r->field_mask=1;
    r->templates[0]=(AFHFH)(0x23E + (((winner->time.day-1)/7)&3));
    r->fields[0].length=16;
    if(!af_hf_mail_item_name(r->fields[0].text,16,gift) ||
       !af_mail_record_pack(w->snapshot,AF_MAIL_RECORD_BYTES,r) ||
       !af_mail_restore(&w->text,w->snapshot,AF_MAIL_RECORD_BYTES,&w->catalogue))return 0;
    af_hf_copy(w->mail+42,w->snapshot,AF_MAIL_RECORD_BYTES);return 1;
}
int af_hf_mail_deliver(void) {
    AFHFLive *s=&af_hf_live;
    if(!af_hf_records_enter())return -1;
    int mask=af_holiday_fish_finalize(&s->records),result=0;
    void *allocation=0;
    if(mask<0 || s->failed || s->records.error ||
       !af_holiday_fish_store(&s->records,s->wire,AF_HF_BYTES)) {result=-1;goto done;}
    if(!mask) {result=1;goto done;}
    allocation=af_hf_mail_alloc(sizeof(MailWork)+15);
    if(!allocation)goto done;
#ifdef __mips__
    u32 address=(u32)allocation;
    if(address<0x8019C8E0 || address>0x80400000-sizeof(MailWork)-15) {result=-1;goto done;}
#endif
    MailWork *w=(MailWork *)(((__UINTPTR_TYPE__)allocation+15)&~(__UINTPTR_TYPE__)15);
    for(u32 i=0;i<5;i++)if(mask&(1u<<i)) {
        const AFHFRecord *winner=s->records.fishRecord+i;
        int player=s->records.services.player_index(s->records.opaque,&winner->pid);
        if(player<0 || player>=4) {result=-1;goto done;}
        u32 house=(u32)af_hf_mail_house((u32)player)&3;
        const AFHFB *owner=af_hf_native_save+0x3588+house*0xB48;
        AFHFB *mailbox=(AFHFB *)af_hf_native_save+0x3A00+house*0xB48;
        /* Do not deliver to a different resident's home when town state is
           inconsistent. The ordinary post-office route may still accept it. */
        int slot=same(owner,af_hf_native_players[player],16)?af_hf_mail_slot(mailbox,10):-1;
        if(slot>=10) {result=-1;goto done;}
        if(slot<0 && af_hf_mail_kept()>=5)continue;
        if(!make(w,winner,(u32)player))goto done;
        /* Prepare the complete acknowledged record before publishing mail;
           no fallible save operation follows a successful delivery. */
        w->acknowledged=s->records;
        if(!af_holiday_fish_acknowledge(&w->acknowledged,i,winner) ||
           !af_holiday_fish_store(&w->acknowledged,w->next_wire,AF_HF_BYTES)) {result=-1;goto done;}
        if(slot>=0)af_hf_mail_copy(mailbox+slot*164,w->mail);
        else if(af_hf_mail_receipt(w->mail,0)!=1)continue;
        af_hf_copy(s->wire,w->next_wire,AF_HF_BYTES);s->records=w->acknowledged;
        af_mail_generation_capital=w->text.final_capital;mask&=~(1u<<i);
    }
    result=!mask;
done:
    if(allocation)af_hf_mail_free(allocation);
    s->active=0;return result;
}
void af_hf_mail_notice(void *destination,const void *clock) {
    af_hf_mail_timecopy(destination,clock);
    /* Native notice completion owns the daily attempt, not the stall's
       lifetime. Prize mail remains available after the tournament ends. */
    if((af_hf_services_ready&8) && af_hf_mail_deliver()<0) {
        extern void af_hf_native_halt(void);
        af_hf_native_halt();
    }
}
