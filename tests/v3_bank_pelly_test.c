#include "bank_pelly_source.h"
#include "bank_native.h"
#include "bank_dialogue.h"
#include "bank_entries.h"
#include <assert.h>
#include <string.h>
static int window,number,continuing=1,disappeared,appeared,chosen=1,order_value=1;
static int keep_mail,first_job,forced,unlocked,opened,showed,loan_calls,native_action_value;
static int original_business_calls,original_talk_calls,original_destruct_calls,status_calls;
static char free_str[12];
static char loan_str[2][8];
static union {unsigned int align;unsigned char b[0x958];} actor;
static union {unsigned int align;unsigned char b[0x1DAC];} game;
static union {unsigned int align;unsigned char b[0x40];} private;
static unsigned int word(const unsigned char *p) {return (unsigned int)p[0]<<24|(unsigned int)p[1]<<16|(unsigned int)p[2]<<8|p[3];}
static void put(unsigned char *p,unsigned int n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
void *af_bank_pelly_window(void) {return &window;}
int af_bank_pelly_native_number(void *w) {assert(w==&window);return number;}
int af_bank_pelly_continue(void *w) {assert(w==&window);return continuing;}
int af_bank_pelly_disappeared(void *w) {assert(w==&window);return disappeared;}
int af_bank_pelly_appeared(void *w) {assert(w==&window);return appeared;}
void af_bank_pelly_unlock(void *w) {assert(w==&window);unlocked++;}
void af_bank_pelly_force(void *w) {assert(w==&window);forced++;}
#ifndef AF_BANK_TEST_DIALOGUE
int af_bank_pelly_message_map(int n) {return n+0x4000;}
int af_bank_pelly_message_unmap(int n) {return n-0x4000;}
#endif
void af_bank_pelly_native_continue(void *w,int n) {assert(w==&window);number=n;}
void af_bank_pelly_native_change(void *w,int n) {assert(w==&window);number=n;}
void af_bank_pelly_native_message(int n) {number=n;}
void af_bank_pelly_free_string(void *w,int index,const unsigned char *text,int n) {
    assert(w==&window);
    if(index==3) {assert(n==11);memcpy(free_str,text,11);free_str[11]=0;}
    else {
        assert((index==1 || index==2) && n>=0 && n<=7);
        memset(loan_str[index-1],0,8);memcpy(loan_str[index-1],text,(unsigned int)n);
        if(index==2) {assert(n==7);loan_calls++;}
    }
}
void af_bank_pelly_appear(void *w,int n) {assert(w==&window && n==1);showed++;}
void af_bank_pelly_disappear(void *w) {assert(w==&window);disappeared=1;}
int af_bank_pelly_order(int group,int n) {assert(group==4 && n==9);return order_value;}
void af_bank_pelly_set_order(int group,int n,int value) {assert(group==4 && n==9 && value==0);order_value=0;}
void *af_bank_pelly_choice_window(void) {return &window;}
int af_bank_pelly_choice(void *w) {assert(w==&window);return chosen;}
int af_bank_pelly_mail_count(void) {return keep_mail;}
int af_bank_pelly_first_job(void) {return first_job;}
#ifdef AF_BANK_TEST_APRIL
extern int af_bank_april_test_foreigner;
extern void af_bank_april_test(void);
int af_bank_pelly_foreigner(void) {return af_bank_player>=4 || af_bank_april_test_foreigner;}
#else
int af_bank_pelly_foreigner(void) {return af_bank_player>=4;}
AFBankPellyApril *af_bank_pelly_april_clip(void) {return 0;}
#endif
void af_bank_pelly_native_open_menu(void *s,int n,int a,int b) {
    assert(s==game.b+0x1CBC && n==7 && !a && !b);opened++;
    /* Match native mSM_open_submenu: queue the program, without changing the
     * open flag. The native linker raises that flag several frames later. */
    put(game.b+0x1CC0,7);
}
static void original_process(void *a,void *g) {assert(a==actor.b && g==game.b);}
static void original_business(void *a,void *g) {original_process(a,g);original_business_calls++;}
static void original_talk(void *a) {assert(a==actor.b);original_talk_calls++;}
static void original_destruct(void *a,void *g) {original_process(a,g);original_destruct_calls++;}
static void native_status(void *a) {assert(a==actor.b);actor.b[0x948]=0;status_calls++;}
static void native_setup(void *a,void *g,int action) {
    assert(a==actor.b && g==game.b);native_action_value=action;
    put(actor.b+0x938,(unsigned int)action);
    af_bank_test_store_pointer(a,0x940,(void *)original_process);
}
static void enter(void) {
    memset(actor.b,0,sizeof(actor.b));memset(game.b,0,sizeof(game.b));
    memset(private.b,0,sizeof(private.b));private.b[0xC]=0x12;private.b[0xD]=0x34;
    private.b[0xE]=0x56;private.b[0xF]=0x78;
    af_bank_now_private=private.b;af_bank_player=0;af_bank_account_mode=1;
    af_bank_home_arrangement=0x1B;memset(af_bank_native_homes,0,sizeof(unsigned char)*4*0xB48);
    memcpy(af_bank_native_homes+3*0xB48,private.b,16);af_bank_native_homes[3*0xB48+0x22]=0x80;
    assert(af_bank_reset(af_bank_native_account(),48));
    af_bank_test_store_pointer(actor.b,0x944,(void *)native_setup);
    order_value=1;continuing=1;chosen=1;keep_mail=0;first_job=0;
    native_action_value=-1;number=af_bank_pelly_message_map(0x2DE0);
    disappeared=appeared=opened=forced=showed=unlocked=0;
}
void af_bank_pelly_test(void) {
    enter();assert(af_bank_native_eligible());
    unsigned char *home=af_bank_native_homes+3*0xB48;
    for(int size=0;size<4;size++) {home[0x22]=(unsigned char)(size<<6);assert(af_bank_native_eligible()==(size==2));}
    home[0x22]=0x88;assert(!af_bank_native_eligible());home[0x22]=0x80;
    home[0xC]^=1;assert(!af_bank_native_eligible());home[0xC]^=1;
    put(private.b+0x3C,1);assert(!af_bank_native_eligible());put(private.b+0x3C,0);
    af_bank_player=4;assert(!af_bank_native_eligible());af_bank_player=0;
    unsigned char before_actor[0x958],before_private[0x40];
    memcpy(before_actor,actor.b,sizeof(actor.b));memcpy(before_private,private.b,sizeof(private.b));
    assert(af_bank_pelly_native_talk(actor.b)==1 && af_bank_pelly_message_unmap(number)==0x8D1);
    assert(!memcmp(before_actor,actor.b,sizeof(actor.b)) && !memcmp(before_private,private.b,sizeof(private.b)));
    actor.b[0x724]=1;assert(af_bank_pelly_native_talk(actor.b)==1 && af_bank_pelly_message_unmap(number)==0x8D2);
    actor.b[0x724]=0;keep_mail=5;
    assert(af_bank_pelly_native_talk(actor.b)==1 && af_bank_pelly_message_unmap(number)==0x8CF);keep_mail=0;
    /* No bank selection means the native caller retains ordinary repayment. */
    af_bank_account_mode=0;assert(!af_bank_pelly_native_talk(actor.b));assert(!af_bank_pelly_native_business(actor.b,game.b));
    assert(!memcmp(before_actor,actor.b,sizeof(actor.b)));af_bank_account_mode=1;
    chosen=0;assert(af_bank_pelly_native_business(actor.b,game.b)==1 && native_action_value==29);
    put(actor.b+0x938,0);chosen=2;order_value=1;
    assert(af_bank_pelly_native_business(actor.b,game.b)==1 && native_action_value==16);
    put(actor.b+0x938,0);chosen=1;order_value=1;
    assert(af_bank_pelly_native_business(actor.b,game.b)==1 && word(actor.b+0x938)==33 && order_value==0);
    assert(af_bank_test_pointer(actor.b,0x940)==(void *)af_bank_pelly_native_move);
    number=af_bank_pelly_message_map(0x2DE0);
    af_bank_pelly_native_move(actor.b,game.b);assert(word(actor.b+0x938)==34 && disappeared);
    af_bank_pelly_native_move(actor.b,game.b);assert(word(actor.b+0x938)==35 && opened==1);
    assert(!game.b[0x1D98] && af_bank_native_pending(game.b+0x1CBC));
    for(int i=0;i<4;i++) {
        af_bank_pelly_native_move(actor.b,game.b);
        assert(word(actor.b+0x938)==35 && !forced && !showed && native_action_value==16);
    }
    game.b[0x1D98]=1;
    af_bank_pelly_native_move(actor.b,game.b);assert(word(actor.b+0x938)==35 && !forced);
    /* Present a changed account receipt from the separately tested transaction. */
    unsigned char *record=af_bank_native_account();record[8]=1;put(record+16,999999999);
    game.b[0x1D98]=0;(void)af_bank_native_destruct(game.b+0x1CBC);
    af_bank_pelly_native_move(actor.b,game.b);
    assert(word(actor.b+0x938)==36 && word(actor.b+0x93C)==37 && forced==2 && showed==1);
    assert(!strcmp(free_str,"999,999,999") && af_bank_pelly_message_unmap(number)==0x2DE2);
    appeared=1;af_bank_pelly_native_move(actor.b,game.b);assert(word(actor.b+0x938)==37 && unlocked==1);
    assert(af_bank_pelly_message_unmap(number)==0x8DF);
    af_bank_pelly_native_move(actor.b,game.b);assert(word(actor.b+0x938)==0 && native_action_value==0);
    assert(af_bank_test_pointer(actor.b,0x940)==(void *)original_process);
    assert(!memcmp(before_private,private.b,sizeof(private.b)));
    for(unsigned int i=0;i<sizeof(actor.b);i++)if(!(i>=0x938 && i<0x940))assert(actor.b[i]==before_actor[i]);
    /* A different resident cancels the owned route, without opening a menu. */
    enter();assert(af_bank_pelly_native_business(actor.b,game.b));af_bank_player=1;
    af_bank_pelly_native_move(actor.b,game.b);assert(native_action_value==1 && !opened);
    enter();assert(af_bank_pelly_native_business(actor.b,game.b));
    af_bank_pelly_native_move(actor.b,game.b);af_bank_pelly_native_move(actor.b,game.b);
    assert(opened==1 && af_bank_pelly_native_release(actor.b)==1);
    assert(!af_bank_native_pending(game.b+0x1CBC));
    assert(af_bank_native_construct(game.b+0x1CBC)==-1 && !af_bank_frontend_active());
    assert(af_bank_native_destruct(game.b+0x1CBC)==1);
    assert(!af_bank_pelly_native_release(actor.b));
    /* The installed wrappers receive actual relocated original functions,
     * refresh status before bank greeting, and preserve ordinary fallbacks. */
    enter();actor.b[0x948]=2;
    af_bank_pelly_talk_entry(actor.b,original_talk,native_status);
    assert(status_calls==1 && !original_talk_calls && af_bank_pelly_message_unmap(number)==0x8D1);
    af_bank_account_mode=0;
    af_bank_pelly_talk_entry(actor.b,original_talk,native_status);assert(original_talk_calls==1);
    af_bank_pelly_business_entry(actor.b,game.b,original_business);assert(original_business_calls==1);
    af_bank_pelly_destruct_entry(actor.b,game.b,original_destruct);assert(original_destruct_calls==1);
    af_bank_account_mode=1;chosen=3;
    af_bank_pelly_business_entry(actor.b,game.b,original_business);
    assert(original_business_calls==1 && native_action_value==1);
    /* The original source status function retains loan and mail-queue rules. */
    AFBankPelly s={0,0,0,0,0,100,0,0,1};keep_mail=5;first_job=0;
    assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==3 && loan_calls==1);
    assert(!strcmp(loan_str[1],"100    ") && !strcmp(loan_str[0],""));
    s.loan=999999;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS));
    assert(!strcmp(loan_str[1],"999,999") && !strcmp(loan_str[0],""));
    s.loan=1000000;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS));
    assert(!strcmp(loan_str[1],"0      ") && !strcmp(loan_str[0],"1"));
    s.loan=999999999;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS));
    assert(!strcmp(loan_str[1],"999,999") && !strcmp(loan_str[0],"999"));
    assert(loan_calls==4);
    s.loan=0;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==5);
    s.has_bank_account=0;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==1);
    s.action=30;assert(!af_bank_pelly_step(&s,AF_BANK_PELLY_MOVE));
#ifdef AF_BANK_TEST_APRIL
    af_bank_april_test();
#endif
}
