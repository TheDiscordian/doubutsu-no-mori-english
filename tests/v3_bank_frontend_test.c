#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_BANK_FRONTEND 1
#define AF_BANK_FRONTEND_TEST 1
#include "bank_source_adapter.h"
#include "bank_frontend_source.h"

Gfx tyo_win_mode[1],tyo_win_model[1],tyo_win_moji2T_model[1],tyo_win_moji3T_model[1];
typedef struct {
    unsigned char record[48];AFBankWallet wallet;unsigned int player;int eligible;
    AFBankFrame frame;int reads,commits,refuse,transitions[5],sounds,matrices,reentrant;
    unsigned int last_sound;void (*move)(void);int (*draw)(void *);
} Context;
static Context c;
static int read(void *p,unsigned char *record,AFBankWallet *wallet,unsigned int *player,int *eligible) {
    Context *v=p;v->reads++;memcpy(record,v->record,48);*wallet=v->wallet;*player=v->player;*eligible=v->eligible;return 1;
}
static int commit(void *p,const unsigned char *before,const unsigned char *after,
    const AFBankWallet *old,const AFBankWallet *next,unsigned int player) {
    Context *v=p;v->commits++;
    if(v->refuse || player!=v->player || memcmp(before,v->record,48) || memcmp(old,&v->wallet,sizeof(*old)))return 0;
    if(v->reentrant) {
        int reads=v->reads;af_bank_frontend_move();af_bank_frontend_destruct();assert(v->reads==reads);
        assert(af_bank_frontend_active());
    }
    memcpy(v->record,after,48);v->wallet=*next;return 1;
}
static int frame(void *p,AFBankFrame *f) {*f=((Context *)p)->frame;return 1;}
static int activate(void *p,void (*move)(void),int (*draw)(void *),const AFBankFrame *f) {
    Context *v=p;v->move=move;v->draw=draw;v->frame=*f;assert(f->status==0 && f->next==1 && f->direction==5);return 1;
}
static void transition(void *p,int action,int direction) {
    Context *v=p;assert(action>=0 && action<5);v->transitions[action]++;
    if(action==AF_BANK_UI_MOVE)v->frame.status=v->frame.next;
    if(action==AF_BANK_UI_CLOSE) {assert(direction==4);v->frame.status=4;}
    if(action==AF_BANK_UI_PREDRAW && v->refuse==2)v->frame.x=0.0f/0.0f;
}
static void character(void *p,void *graph) {assert(graph);((Context *)p)->matrices++;}
static void sound(void *p,unsigned int n) {Context *v=p;v->sounds++;v->last_sound=n;}
static const AFBankFrontendOps ops={read,commit,frame,activate,transition,character,sound};
static char drawn[64][16];static int counts[64],lines,translates,scales;
static float positions[64][2];
void af_bank_native_translate(float x,float y,float z,int mode) {
    assert(x==16*c.frame.x && y==16*c.frame.y && z==140 && mode==0);translates++;
}
void af_bank_native_scale(float x,float y,float z,int mode) {
    assert(x==16 && y==16 && z==1 && mode==1);scales++;
}
void *af_bank_native_matrix(void *g) {assert(g);return (void *)(uptr)0x80001000u;}
#ifdef AF_BANK_TEST_NATIVE
int af_bank_native_string_width(const unsigned char *s,int n,int half) {assert(s && n>0 && half==1);return n*6;}
extern void af_bank_native_test(void);
void af_bank_test_native_draw(void *submenu,void (*draw)(void *,void *)) {
    c.frame=(AFBankFrame){0};lines=translates=scales=0;
    Gfx commands[2048];GRAPH graph={0};graph.head=commands;graph.tail=commands+2048;GAME game={&graph};
    draw(submenu,&game);assert(lines==11 && translates==1 && scales==1);
    assert(graph.head==commands+10 && !strcmp(drawn[0],"Your Account"));
}
#else
float af_bank_native_width(const unsigned char *s,int n,int half) {assert(s && n>0 && half==1);return n*6.0f;}
#endif
void af_bank_native_line(void *game,const unsigned char *s,int n,float x,float y,
    int r,int g,int b,int a,int cut,int half,float sx,float sy,int mode) {
    assert(game && n>0 && n<16 && lines<64 && r>=0 && g>=0 && b>=0 && a==255);
    assert(cut==0 && half==1 && sx>0 && sy==sx && mode==0);
    memcpy(drawn[lines],s,n);drawn[lines][n]=0;counts[lines]=n;
    positions[lines][0]=x;positions[lines][1]=y;lines++;
}
static void reset(unsigned int balance) {
    af_bank_frontend_destruct();memset(&c,0,sizeof(c));c.eligible=1;c.wallet.wallet=99999;
    c.wallet.items[0]=0x2102;c.wallet.items[1]=0x3294;c.wallet.conditions[1]=2;
    assert(af_bank_reset(c.record,48));
    c.record[8]=balance!=0;c.record[16]=balance>>24;c.record[17]=balance>>16;
    c.record[18]=balance>>8;c.record[19]=balance;
    memset(drawn,0,sizeof(drawn));lines=translates=scales=0;
}
static void press(unsigned int trigger) {c.frame.trigger=trigger;c.move();}
int main(void) {
    reset(100000000);assert(af_bank_frontend_open(&ops,&c)==1);
    assert(af_bank_frontend_open(&ops,&c)==0);
    c.move();assert(c.frame.status==1 && c.transitions[AF_BANK_UI_MOVE]==1);
    unsigned char before[48];memcpy(before,c.record,48);AFBankWallet original=c.wallet;
    press(8);assert(c.commits==0 && !memcmp(before,c.record,48) && !memcmp(&original,&c.wallet,sizeof(original)));
    assert(c.last_sound==0x426);
    Gfx commands[2048];memset(commands,0,sizeof(commands));GRAPH graph={0};graph.head=commands;graph.tail=commands+2048;
    GAME game={&graph};c.frame.x=3;c.frame.y=-2;c.frame.texture_x=65;c.frame.texture_y=-70;
    assert(c.draw(&game)==1 && translates==1 && scales==1 && c.matrices==1);
    assert(lines==11 && !strcmp(drawn[0],"Your Account") && !strcmp(drawn[1],"100,100,000"));
    assert(!strcmp(drawn[2],"     29,999") && !strcmp(drawn[10],"OK"));
    assert(counts[1]==11 && counts[2]==11 && positions[1][1]==159 && positions[2][1]==100);
    assert(commands[2].a==0xF20FC018u && commands[2].b==0x00178094u);
    assert(commands[4].b==0xA53232FFu && commands[7].b==0x465F46FFu);
    /* Frame commands and full glyph allowance are checked before any drawing. */
    int old_lines=lines;graph.tail=graph.head+1;assert(c.draw(&game)==0 && lines==old_lines);
    graph.tail=commands+2048;
    c.refuse=1;press(0x1000);assert(c.commits==1 && !memcmp(before,c.record,48));
    assert(c.last_sound==0x1003 && c.transitions[AF_BANK_UI_CLOSE]==0);
    c.refuse=0;c.reentrant=1;press(0x1000);assert(c.commits==2 && c.transitions[AF_BANK_UI_CLOSE]==1);
    assert(c.wallet.wallet==29999 && c.wallet.items[0]==0 && c.wallet.items[1]==0x3294 && c.wallet.conditions[1]==2);
    AFBankAccount account;assert(af_bank_get(c.record,48,0,&account) && account.balance==100100000);
    c.move();assert(c.transitions[AF_BANK_UI_END]==1);af_bank_frontend_destruct();assert(!af_bank_frontend_active());
    reset(100000000);assert(af_bank_frontend_open(&ops,&c));c.move();press(8);press(0x5000);
    assert(c.commits==0 && c.wallet.wallet==99999);assert(af_bank_get(c.record,48,0,&account) && account.balance==100000000);
    reset(100000000);assert(af_bank_frontend_open(&ops,&c));c.move();press(4);press(0x1000);
    assert(c.wallet.wallet==79999 && c.wallet.items[0]==0x2102 && c.wallet.items[2]==0x2102 && c.wallet.items[3]==0x2102);
    assert(af_bank_get(c.record,48,0,&account) && account.balance==99900000);
    /* A changed live resident never closes the menu or publishes its preview. */
    reset(100000000);assert(af_bank_frontend_open(&ops,&c));c.move();press(8);c.player=1;press(0x1000);
    assert(!c.commits && !c.transitions[AF_BANK_UI_CLOSE] && c.last_sound==0x1003);
    reset(100000000);assert(af_bank_frontend_open(&ops,&c));c.frame.status=5;press(0x1000);
    assert(!c.commits && !c.transitions[AF_BANK_UI_PREMOVE]);assert(c.draw(&game)==0);
    reset(999999999);assert(af_bank_frontend_open(&ops,&c));c.move();c.refuse=2;
    graph.head=commands;graph.tail=commands+2048;old_lines=lines;
    assert(c.draw(&game)==0 && graph.head==commands && lines==old_lines);
    reset(0);assert(af_bank_frontend_open(&ops,&c));c.move();press(8);
    assert(af_bank_frontend_cancel()==1 && af_bank_frontend_active());
    assert(!c.commits && c.wallet.wallet==99999 && c.transitions[AF_BANK_UI_CLOSE]==1);
    c.move();assert(c.transitions[AF_BANK_UI_END]==1);
    af_bank_frontend_destruct();assert(!af_bank_frontend_active());
    reset(0);c.eligible=0;assert(!af_bank_frontend_open(&ops,&c));assert(!af_bank_frontend_active());
#ifdef AF_BANK_TEST_NATIVE
    af_bank_native_test();
    extern void af_bank_pelly_test(void);
    af_bank_pelly_test();
#endif
    puts("Complete donor banking lifecycle, rendering, transfers, and guarded callbacks pass; native I/O is doubled.");
    return 0;
}
