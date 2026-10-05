#include "bank_account.h"
#include "../../runtime/mail/record.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

unsigned char af_bank_account_mode,af_bank_home_arrangement;
unsigned char af_bank_mail_players[4*0xBD0],af_bank_mail_homes[4*0xB48];
const unsigned short af_bank_mail_items[4]={0x3C90,0x3C40,0x3294,0x3020};
const unsigned char af_bank_mail_rows[64]={
    0,0,2,0x46,0x1F,0xB0,0x20,0,0,0,0,4,0,0x0F,0x42,0x40,
    0,0,2,0x47,0x1F,0xAC,0x20,0,0,0,0,8,0,0x98,0x96,0x80,
    0,0,2,0x48,0x32,0x94,0x20,0,0,0,0,0x10,5,0xF5,0xE1,0,
    0,0,2,0x49,0x30,0x20,0x20,0,0,0,0,0x20,0x3B,0x9A,0xC9,0xFF};
static unsigned char account[48],queued[164];
static int queue_result,attempts,deliveries,selected[4];
extern int af_bank_mail_run(void);
extern void af_bank_mail_start(void);
unsigned char *af_bank_native_account(void) {return account;}
int af_bank_mail_null(const void *p) {return !((const unsigned char *)p)[0];}
const void *af_bank_mail_selected(unsigned index) {
    for(unsigned i=0;i<4;i++)if(index==1024u+((unsigned)af_bank_mail_items[i]-0x3000u)/4u)
        return selected[i]?af_bank_mail_items:0;
    return 0;
}
const unsigned char *af_bank_mail_town(void) {return (const unsigned char *)"Grove ";}
void af_bank_mail_clear(void *p) {memset(p,0,164);((unsigned char *)p)[38]=255;}
int af_bank_mail_free(void *p,int n) {
    for(int i=0;i<n;i++)if(((unsigned char *)p)[i*164+38]==255)return i;
    return -1;
}
void af_bank_mail_copy(void *to,const void *from) {memcpy(to,from,164);}
int af_bank_mail_receipt(const void *mail,int kind) {
    assert(kind==0);++attempts;memcpy(queued,mail,164);return queue_result;
}
void af_bank_mail_first_delivery(void) {++deliveries;}
static void seed(unsigned p,unsigned value) {
    account[8]=1;unsigned char *b=account+16+p*8;
    b[0]=value>>24;b[1]=value>>16;b[2]=value>>8;b[3]=value;
}
static unsigned receipts(unsigned p) {return account[20+p*8];}
static void check(const unsigned char *mail,unsigned player,unsigned milestone) {
    AfMailRecord record;
    assert(!memcmp(mail,af_bank_mail_players+player*0xBD0,16));
    assert(mail[16]==0 && mail[34]==2 && mail[38]==0 && mail[39]==128 && mail[40]==10 && mail[41]==0);
    assert(((unsigned)mail[36]<<8|mail[37])==af_bank_mail_items[milestone]);
    assert(af_mail_record_unpack(&record,mail+42,122,4));
    assert(record.templates[0]==0x246+milestone && record.field_mask==3);
    assert(record.fields[0].length==5 && !memcmp(record.fields[0].text,"Grove",5));
    assert(record.fields[1].length==6 && !memcmp(record.fields[1].text,af_bank_mail_players+player*0xBD0,6));
}
int main(void) {
    assert(af_bank_reset(account,48));
    af_bank_home_arrangement=0x1B; /* Reverse arrangement, not player == house. */
    for(unsigned p=0;p<4;p++) {
        unsigned char *id=af_bank_mail_players+p*0xBD0;
        memcpy(id,"Player",6);id[5]=(unsigned char)('A'+p);id[12]=1;id[14]=2;
        unsigned home=(af_bank_home_arrangement>>(2*p))&3;
        memcpy(af_bank_mail_homes+home*0xB48,id,16);
        for(unsigned slot=0;slot<10;slot++)af_bank_mail_homes[home*0xB48+0x478+slot*164+38]=255;
        selected[p]=1;seed(p,999999999);
    }
    af_bank_mail_start();assert(deliveries==1 && !attempts && !receipts(0));
    af_bank_account_mode=1;
    for(unsigned m=0;m<4;m++) {
        assert(af_bank_mail_run()==4);
        for(unsigned p=0;p<4;p++) {
            unsigned home=(af_bank_home_arrangement>>(2*p))&3;
            check(af_bank_mail_homes+home*0xB48+0x478+m*164,p,m);
            assert(receipts(p)==((4u<<(m+1))-4));
        }
    }
    assert(af_bank_mail_run()==0 && !attempts);
    assert(af_bank_reset(account,48));seed(0,1000000);
    for(unsigned i=0;i<10;i++)af_bank_mail_homes[3*0xB48+0x478+i*164+38]=0;
    queue_result=0;assert(af_bank_mail_run()==0 && attempts==1 && !receipts(0));
    queue_result=2;assert(af_bank_mail_run()==0 && attempts==2 && !receipts(0));
    queue_result=1;assert(af_bank_mail_run()==1 && attempts==3 && receipts(0)==4);check(queued,0,0);
    assert(af_bank_mail_run()==0 && attempts==3);
    assert(af_bank_reset(account,48));seed(0,999999);assert(af_bank_mail_run()==0);
    seed(0,1000000);af_bank_mail_players[0]=0;assert(af_bank_mail_run()==0);
    af_bank_mail_players[0]='P';selected[0]=0;assert(af_bank_mail_run()==0);
    selected[0]=1;af_bank_mail_homes[3*0xB48]^=1;
    assert(af_bank_mail_run()==1 && attempts==4);check(queued,0,0);
    af_bank_account_mode=0;af_bank_mail_start();assert(deliveries==2 && attempts==4);
    puts("Savings mail: four milestones, four residents, original ordering, canonical gifts, name snapshots, mailbox/queue retry, and disabled scheduling pass");
    return 0;
}
