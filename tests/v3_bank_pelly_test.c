#include "bank_pelly_source.h"
#include "bank_native.h"
#include "bank_dialogue.h"
#include <assert.h>
#include <string.h>
static int window,number,continuing=1,disappeared,appeared,chosen=1,order_value=1;
static int keep_mail,first_job,forced,unlocked,opened,showed,loan_calls,native_action_value;
static char free_str[12];
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
    assert(w==&window && index==3 && n==11);memcpy(free_str,text,11);free_str[11]=0;
}
void af_bank_pelly_appear(void *w,int n) {assert(w==&window && n==1);showed++;}
void af_bank_pelly_disappear(void *w) {assert(w==&window);disappeared=1;}
int af_bank_pelly_order(int group,int n) {assert(group==4 && n==9);return order_value;}
void af_bank_pelly_set_order(int group,int n,int value) {assert(group==4 && n==9 && value==0);order_value=0;}
void *af_bank_pelly_choice_window(void) {return &window;}
int af_bank_pelly_choice(void *w) {assert(w==&window);return chosen;}
int af_bank_pelly_mail_count(void) {return keep_mail;}
int af_bank_pelly_first_job(void) {return first_job;}
int af_bank_pelly_foreigner(void) {return af_bank_player>=4;}
void af_bank_pelly_loan_balance(void) {loan_calls++;}
AFBankPellyApril *af_bank_pelly_april_clip(void) {return 0;}
void af_bank_pelly_native_open_menu(void *s,int n,int a,int b) {
    assert(s==game.b+0x1CBC && n==7 && !a && !b);opened++;
    /* The native opening service is doubled. No emulator execution is claimed. */
    game.b[0x1D98]=1;put(game.b+0x1CC0,7);
}
static void original_process(void *a,void *g) {assert(a==actor.b && g==game.b);}
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
    assert(af_bank_native_construct(game.b+0x1CBC)==-1 && !af_bank_frontend_active());
    assert(!af_bank_pelly_native_release(actor.b));
    /* The original source status function retains loan and mail-queue rules. */
    AFBankPelly s={0,0,0,0,0,100,0,0,1};keep_mail=5;first_job=0;
    assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==3 && loan_calls==1);
    s.loan=0;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==5);
    s.has_bank_account=0;assert(af_bank_pelly_step(&s,AF_BANK_PELLY_STATUS) && s.status==1);
    s.action=30;assert(!af_bank_pelly_step(&s,AF_BANK_PELLY_MOVE));
}
