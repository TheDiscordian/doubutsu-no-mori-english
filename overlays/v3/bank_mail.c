#include "bank_account.h"
#include "../../runtime/mail/record.h"

/* Original four-row milestones and checked canonical destination identities. */
extern const unsigned char af_bank_mail_rows[64];
extern const unsigned short af_bank_mail_items[4];
extern unsigned char af_bank_account_mode;
extern unsigned char af_bank_mail_players[];
extern unsigned char af_bank_mail_homes[];
extern unsigned char af_bank_home_arrangement;
extern unsigned char *af_bank_native_account(void);
extern int af_bank_mail_null(const void *);
extern const void *af_bank_mail_selected(unsigned int);
extern const unsigned char *af_bank_mail_town(void);
extern void af_bank_mail_clear(void *);
extern int af_bank_mail_free(void *, int);
extern void af_bank_mail_copy(void *, const void *);
extern int af_bank_mail_receipt(const void *, int);
extern void af_bank_mail_first_delivery(void);

static unsigned int half(const unsigned char *p) {return (unsigned int)p[0]<<8|p[1];}
static int exists(void *context,unsigned int player) {
    (void)context;
    return player<4 && af_bank_mail_null(af_bank_mail_players+player*0xBD0u)==0;
}
static unsigned int resolve(void *context,unsigned int donor) {
    (void)context;
    for(unsigned int i=0;i<4;i++)if(half(af_bank_mail_rows+i*16+4)==donor) {
        unsigned int item=af_bank_mail_items[i];
        unsigned int index=1024u+(item-0x3000u)/4u;
        return af_bank_mail_selected(index)?item:0;
    }
    return 0;
}
static int submit(void *context,unsigned int player,unsigned int item,
                  unsigned int paper,unsigned int number) {
    unsigned char mail[164] __attribute__((aligned(16)));
    AfMailRecord record;
    const unsigned char *identity,*town;
    unsigned int i,home;
    int slot;
    (void)context;
    if(!exists(0,player) || paper!=0x2000u || number<0x246u || number>0x249u ||
       item!=af_bank_mail_items[number-0x246u] ||
       resolve(0,half(af_bank_mail_rows+(number-0x246u)*16+4))!=item)return 0;
    identity=af_bank_mail_players+player*0xBD0u;
    town=af_bank_mail_town();
    if(!town)return 0;
    for(i=0;i<sizeof(record);i++)((unsigned char *)&record)[i]=0;
    record.catalog=4;record.templates[0]=(unsigned short)number;record.field_mask=3;
    /* English donor string 484 is empty: no Japanese village suffix. Native
     * town/player names have six characters, not the donor's eight. Snapshot
     * both original substitution fields so letters retain their names. */
    for(i=0;i<6;i++) {
        record.fields[0].text[i]=town[i];
        record.fields[1].text[i]=identity[i];
    }
    record.fields[0].length=6;record.fields[1].length=6;
    while(record.fields[0].length && record.fields[0].text[record.fields[0].length-1]==' ')
        --record.fields[0].length;
    af_bank_mail_clear(mail);
    for(i=0;i<16;i++)mail[i]=identity[i];
    mail[16]=0;mail[34]=2; /* Player recipient; source system sender. */
    mail[36]=(unsigned char)(item>>8);mail[37]=(unsigned char)item;
    mail[38]=0;mail[39]=0x80;mail[40]=10;mail[41]=0;
    if(!af_mail_record_pack(mail+42,122,&record))return 0;
    home=(af_bank_home_arrangement>>(2*player))&3;
    unsigned char *house=af_bank_mail_homes+home*0xB48u;
    for(i=0;i<16 && house[i]==identity[i];i++) {}
    if(i==16 && (slot=af_bank_mail_free(house+0x478,10))>=0 && slot<10) {
        af_bank_mail_copy(house+0x478+(unsigned int)slot*164,mail);
        return 1;
    }
    /* Original source falls back to the post office after a missing/mismatched
     * home or full mailbox. Only exact receipt success acknowledges a reward. */
    return af_bank_mail_receipt(mail,0)==1;
}

int af_bank_mail_run(void) {
    AFBankMailOps ops;
    ops.context=0;ops.exists=exists;ops.resolve=resolve;ops.submit=submit;
    if(af_bank_account_mode!=1)return 0;
    return af_bank_send_rewards(af_bank_native_account(),48,af_bank_mail_rows,64,&ops);
}

void af_bank_mail_start(void) {
    /* Source mSDI_StartInitAfter sends milestones immediately before the
     * ordinary initial post-office delivery. No per-frame/daily re-awards. */
    af_bank_mail_run();
    af_bank_mail_first_delivery();
}
