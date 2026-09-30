#include "bank_pelly.h"
#include "bank_native.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct {int open_flag;} AFBankPellySubmenu;
extern void af_bank_pelly_native_open_menu(void *,int,int,int);
extern int af_bank_pelly_message_map(int);
extern int af_bank_pelly_message_unmap(int);
extern int af_bank_pelly_native_number(void *);
extern void af_bank_pelly_native_continue(void *,int);
extern void af_bank_pelly_native_change(void *,int);
extern void af_bank_pelly_native_message(int);
#ifdef __mips__
static void *pointer(const void *p,u32 at) {return *(void *const *)((const u8 *)p+at);}
static void store(void *p,u32 at,void *v) {*(void **)((u8 *)p+at)=v;}
#else
#define pointer af_bank_test_pointer
#define store af_bank_test_store_pointer
#endif
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 n) {p[0]=n>>24;p[1]=n>>16;p[2]=n>>8;p[3]=n;}
static struct {void *actor,*game,*private;u32 player;int busy,failed;} owner;
/* Source actions 24..28 use additive native actions 33..37. Native 24..28
 * already perform other letter/card work and must never be overwritten. */
static int source_action(int n) {return n>=33 && n<=37?n-9:n==0?0:-1;}
static int admitted(void *actor,void *game) {
    return actor && game && !((uptr)actor&3) && !((uptr)game&3) &&
        af_bank_native_selected()==1 && af_bank_native_eligible()==1 &&
        af_bank_valid(af_bank_native_account(),48) && ((u8 *)actor)[0x724]<=1 &&
        ((u8 *)actor)[0x948]<=1 && pointer(actor,0x944);
}
static AFBankPelly snapshot(void *actor,void *game,int action) {
    const u8 *a=actor,*p=af_bank_now_private,*r=af_bank_native_account();
    int next=source_action((int)word(a+0x93C));if(next<0)next=0;
    return (AFBankPelly){a[0x724],a[0x948]|4,action,next,a[0x94A],word(p+0x3C),
        word(r+16+8*af_bank_player),game?(((const u8 *)game)[0x1D98] ||
            af_bank_native_pending((u8 *)game+0x1CBC)):0,1};
}
static void native_action(void *actor,void *game,int action) {
    ((void (*)(void *,void *,int))pointer(actor,0x944))(actor,game,action);
}
static void clear_owner(void) {owner.actor=owner.game=owner.private=0;owner.player=4;}
static void publish(AFBankPelly *s,void *actor,void *game) {
    ((u8 *)actor)[0x94A]=(u8)s->desk_full;
    if(s->action>=24 && s->action<=28) {
        put((u8 *)actor+0x938,(u32)(s->action+9));
        put((u8 *)actor+0x93C,(u32)(s->next_action>=24 && s->next_action<=28?s->next_action+9:s->next_action));
        store(actor,0x940,(void *)af_bank_pelly_native_move);
    } else {
        int n=s->action==21?29:s->action==17 || s->action==16?16:s->action;
        if(n!=0 && n!=1 && n!=11 && n!=16 && n!=29)n=1;
        clear_owner();native_action(actor,game,n);
    }
}
static void abort_owner(void) {
    void *actor=owner.actor,*game=owner.game;
    if(game && af_bank_native_cancel((u8 *)game+0x1CBC)<0)return;
    clear_owner();if(actor && game && pointer(actor,0x944))native_action(actor,game,1);
}
int af_bank_pelly_native_business(void *actor,void *game) {
    if(owner.busy)return -1;
    if(owner.actor)return owner.actor==actor?-1:0;
    if(!admitted(actor,game) || word((u8 *)actor+0x938))return 0;
    owner.busy=1;owner.failed=0;AFBankPelly s=snapshot(actor,game,0);
    if(!af_bank_pelly_step(&s,AF_BANK_PELLY_BUSINESS)) {owner.busy=0;return -1;}
    if(s.action==24) {
        owner.actor=actor;owner.game=game;owner.private=af_bank_now_private;owner.player=af_bank_player;
        publish(&s,actor,game);
    } else if(s.action!=0)publish(&s,actor,game);
    owner.busy=0;return 1;
}
int af_bank_pelly_native_talk(void *actor) {
    if(owner.busy)return -1;
    if(owner.actor)return owner.actor==actor?-1:0;
    if(!actor || ((uptr)actor&3) ||
        af_bank_native_selected()!=1 || af_bank_native_eligible()!=1 ||
        !af_bank_valid(af_bank_native_account(),48) || ((u8 *)actor)[0x724]>1 ||
        ((u8 *)actor)[0x948]>1)return 0;
    owner.busy=1;AFBankPelly s=snapshot(actor,0,0);
    int result=af_bank_pelly_step(&s,AF_BANK_PELLY_TALK);
    owner.busy=0;return result?1:-1;
}
int af_bank_pelly_native_release(void *actor) {
    if(!actor || owner.actor!=actor)return 0;
    if(owner.busy || af_bank_native_cancel((u8 *)owner.game+0x1CBC)<0)return -1;
    clear_owner();return 1;
}
void af_bank_pelly_native_move(void *actor,void *game) {
    if(owner.busy || owner.actor!=actor || owner.game!=game)return;
    owner.busy=1;owner.failed=0;
    if(owner.private!=af_bank_now_private || owner.player!=af_bank_player || !admitted(actor,game)) {
        abort_owner();owner.busy=0;return;
    }
    int action=source_action((int)word((u8 *)actor+0x938));
    if(action<24 || action>28) {abort_owner();owner.busy=0;return;}
    AFBankPelly s=snapshot(actor,game,action);
    if(!af_bank_pelly_step(&s,AF_BANK_PELLY_MOVE))owner.failed=1;
    if(!owner.failed && s.action!=action) {
        if(s.action>=24 && s.action<=28 && !af_bank_pelly_step(&s,AF_BANK_PELLY_INIT))owner.failed=1;
        if(!owner.failed)publish(&s,actor,game);
    }
    if(owner.failed)abort_owner();
    owner.busy=0;
}
void af_bank_pelly_open_menu(AFBankPellySubmenu *view,int menu,int a,int b) {
    (void)view;
    if(!owner.busy || !owner.actor || !owner.game || menu!=22 || a || b ||
        !af_bank_native_request((u8 *)owner.game+0x1CBC)) {owner.failed=1;return;}
    af_bank_pelly_native_open_menu((u8 *)owner.game+0x1CBC,7,0,0);
    if(!af_bank_native_pending((u8 *)owner.game+0x1CBC))owner.failed=1;
}
extern void *af_bank_pelly_window(void);
int af_bank_pelly_message_number(void *w) {return af_bank_pelly_message_unmap(af_bank_pelly_native_number(w));}
void af_bank_pelly_set_continue(void *w,int n) {af_bank_pelly_native_continue(w,af_bank_pelly_message_map(n));}
void af_bank_pelly_change(void *w,int n) {af_bank_pelly_native_change(w,af_bank_pelly_message_map(n));}
void af_bank_pelly_message(int n) {af_bank_pelly_native_message(af_bank_pelly_message_map(n));}
