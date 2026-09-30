#include "bank_native.h"
typedef unsigned int u32;
typedef unsigned char u8;
typedef __UINTPTR_TYPE__ uptr;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 n) {p[0]=(u8)(n>>24);p[1]=(u8)(n>>16);p[2]=(u8)(n>>8);p[3]=(u8)n;}
static int equal(const u8 *a,const u8 *b,u32 n) {for(u32 i=0;i<n;i++)if(a[i]!=b[i])return 0;return 1;}
static int same(const AFBankWallet *a,const AFBankWallet *b) {
    if(a->wallet!=b->wallet)return 0;
    for(u32 i=0;i<15;i++)if(a->items[i]!=b->items[i] || a->conditions[i]!=b->conditions[i])return 0;
    return 1;
}
static u32 bag(unsigned int item) {
    return item==0x2103?100:item==0x2100?1000:item==0x2101?10000:item==0x2102?30000:0;
}
static int total(const AFBankWallet *a,u32 *sum) {
    if(!a || a->wallet>99999)return 0;
    *sum=a->wallet;
    for(u32 i=0;i<15;i++) {if(a->conditions[i]>3)return 0;if(!a->conditions[i])*sum+=bag(a->items[i]);}
    return 1;
}
static int disjoint(const void *a,u32 n,const void *b,u32 m) {
    uptr x=(uptr)a,y=(uptr)b;return x<=y?y-x>=n:x-y>=m;
}
int af_bank_native_wallet(const void *native,AFBankWallet *out) {
    if(!native || !out || ((uptr)native&3) || !disjoint(native,0x40,out,sizeof(*out)))return 0;
    const u8 *p=native;AFBankWallet w={0};u32 conditions=word(p+0x34);
    w.wallet=word(p+0x38);if(w.wallet>99999)return 0;
    for(u32 i=0;i<15;i++) {
        w.items[i]=(unsigned short)((u32)p[0x14+2*i]<<8|p[0x15+2*i]);
        w.conditions[i]=(u8)((conditions>>(2*i))&3);
    }
    *out=w;return 1;
}
int af_bank_native_commit(u8 *record,const u8 *before,const u8 *after,void *native,
    const AFBankWallet *original,const AFBankWallet *next) {
    AFBankWallet current;u32 old_total,new_total;
    if(!record || !native || !original || !next || !af_bank_valid(record,48) ||
        !af_bank_valid(before,48) || !af_bank_valid(after,48) ||
        !disjoint(record,48,native,0x40) || !disjoint(record,48,original,sizeof(*original)) ||
        !disjoint(record,48,next,sizeof(*next)) || !disjoint(record,48,before,48) ||
        !disjoint(record,48,after,48) || !disjoint(native,0x40,before,48) ||
        !disjoint(native,0x40,after,48) || !disjoint(native,0x40,original,sizeof(*original)) ||
        !disjoint(native,0x40,next,sizeof(*next)) ||
        !total(original,&old_total) || !total(next,&new_total) ||
        !equal(record,before,48) || !af_bank_native_wallet(native,&current) || !same(&current,original))return 0;
    /* Only the selected player's balance and the support-required byte may
     * change. Receipt bits, other players, and reserved bytes are untouched. */
    u32 changed=4;
    for(u32 player=0;player<4;player++) {
        if(!equal(before+16+8*player,after+16+8*player,4)) {
            if(changed!=4)return 0;
            changed=player;
        }
    }
    for(u32 i=0;i<48;i++)if(i!=8 && !(changed<4 && i>=16+8*changed && i<20+8*changed) && before[i]!=after[i])return 0;
    if(after[8]!=1 || (changed==4?old_total!=new_total:
        word(before+16+8*changed)+old_total!=word(after+16+8*changed)+new_total))return 0;
    for(u32 i=0;i<15;i++)if(original->conditions[i]!=next->conditions[i] ||
        ((original->conditions[i] || (original->items[i] && !bag(original->items[i]))) &&
            original->items[i]!=next->items[i]) ||
        (original->items[i]!=next->items[i] && next->items[i] && !bag(next->items[i])))return 0;
    /* The reviewed native setter cannot fail for these bounded slots and Bell
     * IDs. It preserves packed condition bits and performs native bookkeeping.
     * Dummy-present randomness and imported-item collection are never reached. */
    for(u32 i=0;i<15;i++)if(current.items[i]!=next->items[i])
        af_bank_native_set_pocket(native,(int)i,next->items[i],next->conditions[i]);
    put((u8 *)native+0x38,next->wallet);
    for(u32 i=0;i<48;i++)record[i]=after[i];
    return 1;
}
#ifdef __mips__
static void *pointer(const void *p,u32 at) {return *(void *const *)((const u8 *)p+at);}
static void store_pointer(void *p,u32 at,void *v) {*(void **)((u8 *)p+at)=v;}
#else
#define pointer af_bank_test_pointer
#define store_pointer af_bank_test_store_pointer
#endif
static struct {void *submenu,*overlay,*private,*game;u32 player;int requested,active,cancelled;} context;
#define MENU 0x10280u
static int owned(void *s) {
    return s && s==context.submenu && context.overlay==pointer(s,0x2C) &&
        word((u8 *)s+4)==7 && context.player<4;
}
static int read(void *v,u8 *record,AFBankWallet *wallet,u32 *player,int *eligible) {
    if(v!=&context || !owned(context.submenu) || context.private!=af_bank_now_private ||
        context.player!=af_bank_player || af_bank_native_selected()!=1)return 0;
    u8 *live=af_bank_native_account();
    if(!af_bank_valid(live,48) || !af_bank_native_wallet(context.private,wallet))return 0;
    for(u32 i=0;i<48;i++)record[i]=live[i];
    *player=af_bank_player;*eligible=af_bank_native_eligible();return 1;
}
static int commit(void *v,const u8 *before,const u8 *after,const AFBankWallet *old,const AFBankWallet *next,u32 player) {
    if(v!=&context || !owned(context.submenu) || context.private!=af_bank_now_private ||
        player!=context.player || player!=af_bank_player || af_bank_native_eligible()!=1 ||
        af_bank_native_selected()!=1)return 0;
    /* The generic bridge also checks all player rows. The live owner additionally
     * permits a balance change only for its originally admitted resident. */
    for(u32 i=0;i<4;i++)if(i!=player && !equal(before+16+8*i,after+16+8*i,8))return 0;
    return af_bank_native_commit(af_bank_native_account(),before,after,context.private,old,next);
}
static float number(const u8 *p) {union {u32 i;float f;} n;n.i=word(p);return n.f;}
static int frame(void *v,AFBankFrame *f) {
    if(v!=&context || !owned(context.submenu))return 0;
    const u8 *o=context.overlay,*m=o+MENU;
    *f=(AFBankFrame){(int)word(m+4),(int)word(m+0x30),(int)word(m+0x34),word(o+0x1068C),
        number(m+0x18),number(m+0x1C),number(o+0x10698),number(o+0x1069C)};return 1;
}
static void native_move(void *s) {if(owned(s) && context.active)af_bank_frontend_move();}
static void native_draw(void *s,void *g) {
    if(owned(s) && context.active && !context.game) {
        context.game=g;(void)af_bank_frontend_draw(g);context.game=0;
    }
}
static int set_proc(void) {
    if(!owned(context.submenu))return 0;
    store_pointer(context.overlay,0x10670,(void *)native_move);
    store_pointer(context.overlay,0x10674,(void *)native_draw);return 1;
}
static int activate(void *v,void (*move)(void),int (*draw)(void *),const AFBankFrame *f) {
    if(v!=&context || !owned(context.submenu) || move!=af_bank_frontend_move || draw!=af_bank_frontend_draw ||
        !pointer(context.overlay,MENU+0x0C) || !pointer(context.overlay,MENU+0x10) ||
        !pointer(context.overlay,0x106A8) || !pointer(context.overlay,0x106AC) ||
        !pointer(context.overlay,0x106B0) || !pointer(context.overlay,0x106B4))return 0;
    u8 *o=context.overlay,*m=o+MENU;
    put(m+4,(u32)f->status);put(m+0x30,(u32)f->next);put(m+0x34,(u32)f->direction);put(o+0x106A0,0);
    return set_proc();
}
static void transition(void *v,int action,int direction) {
    if(v!=&context || !owned(context.submenu))return;
    void *s=context.submenu;u8 *o=context.overlay,*m=o+MENU;
    if(action==AF_BANK_UI_PREMOVE) ((void (*)(void *))pointer(o,MENU+0x0C))(s);
    else if(action==AF_BANK_UI_MOVE || action==AF_BANK_UI_END)
        ((void (*)(void *,void *))pointer(o,action==AF_BANK_UI_MOVE?0x106A8:0x106AC))(s,m);
    else if(action==AF_BANK_UI_PREDRAW) ((void (*)(void *,void *))pointer(o,MENU+0x10))(s,context.game);
    else if(action==AF_BANK_UI_CLOSE) ((void (*)(void *,int))pointer(o,0x106B0))(m,direction);
}
static void character(void *v,void *g) {
    if(v==&context && owned(context.submenu))((void (*)(void *))pointer(context.overlay,0x106B4))(g);
}
static void sound(void *v,u32 n) {if(v==&context && owned(context.submenu))af_bank_native_sound(n);}
static const AFBankFrontendOps ops={read,commit,frame,activate,transition,character,sound};
int af_bank_native_request(void *s) {
    AFBankWallet wallet;
    if(context.requested || context.active || !s || word((u8 *)s+4) || af_bank_player>=4 ||
        af_bank_native_selected()!=1 || af_bank_native_eligible()!=1 ||
        !af_bank_valid(af_bank_native_account(),48) || !af_bank_native_wallet(af_bank_now_private,&wallet))return 0;
    context.submenu=s;context.private=af_bank_now_private;context.player=af_bank_player;
    context.requested=1;context.cancelled=0;return 1;
}
int af_bank_native_construct(void *s) {
    if(!context.requested || context.submenu!=s || word((u8 *)s+4)!=7)return 0;
    if(context.cancelled) {context.requested=0;context.submenu=0;return -1;}
    context.overlay=pointer(s,0x2C);context.requested=0;
    if(!context.overlay || !af_bank_frontend_open(&ops,&context)) {context.submenu=0;return -1;}
    context.active=1;return 1;
}
int af_bank_native_set_proc(void *s) {return owned(s) && context.active && set_proc();}
int af_bank_native_destruct(void *s) {
    if(s!=context.submenu)return 0;
    af_bank_frontend_destruct();
    if(af_bank_frontend_active())return -1;
    context.submenu=context.overlay=context.private=context.game=0;
    context.requested=context.active=context.cancelled=0;return 1;
}
int af_bank_native_cancel(void *s) {
    if(!s || s!=context.submenu)return 0;
    if(context.requested) {context.cancelled=1;return 1;}
    return context.active?af_bank_frontend_cancel():0;
}
float af_bank_native_width(const unsigned char *s,int n,int half) {
    return (float)af_bank_native_string_width(s,n,half);
}
