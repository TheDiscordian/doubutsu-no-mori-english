/* Front-counter adapter for the four native Nook shops. Native actor sizes,
 * ordinary actions, clips, and UI remain owned by their original readers. */
#include "nook_password.h"
#include "password_runtime.h"
typedef af_pw_u8 u8;
typedef af_pw_u16 u16;
typedef af_pw_u32 u32;
#include "nook-native.inc"
struct Session {
    struct AfNookPassword password;
    u32 gift_count,other,name_valid;
    af_v3_password decoded;
};
typedef char CodeOffset[__builtin_offsetof(struct AfNookPassword,code)==8?1:-1];
typedef char SessionBounds[sizeof(struct Session)<=0x7F0?1:-1];
#define session ((struct Session *)0x804C7800u)
#define word(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define byte(p,n) (*((u8 *)(p)+(n)))
#define native_private (*(void **)0x80136FD8u)
extern void af_np_setup(void *,void *,int);
extern void af_np_original_destroy(void *,void *);
extern void *af_np_window(void);
extern int af_np_continue(void *),af_np_hidden(void *),af_np_opened(void *);
extern void af_np_hide(void *),af_np_open(void *),af_np_force(void *);
extern void af_np_set_message(void *,int),af_np_change_message(void *,int);
extern void af_np_lock(void *),af_np_unlock(void *);
extern void *af_np_choice_window(void);
extern int af_np_choice_number(void *);
extern int af_np_order_get(int,int);
extern void af_np_order_set(int,int,int);
extern int af_np_foreign(void),af_np_pocket_index(void *,int);
extern int af_np_insert(void *,u16,int);
extern const u8 *af_np_town(void);
extern void af_np_editor(void *,int,int,int,void *,void *);
extern void af_np_free_string(void *,int,const u8 *,int);
extern int af_np_item_name(u8 *,u32,u32);
extern void af_np_item_string(void *,int,const u8 *,int);
extern void af_np_fault(int) __attribute__((noreturn));
extern void af_np_sound(u16,void *);
struct Handover {
    void *(*birth)(u16,int,int,void *);
    void (*change_master)(void *,void *);
    void (*request)(void *,int);
    u8 request_mode,player_after;u16 item;
    void *master,*target;u8 present,changed,pad[2];void *actor,*rebuild;
};
static struct Handover *handover(void){return *(struct Handover **)0x80136F34u;}
static struct Session *context(void *c){return (struct Session *)c;}
static void *shop(void *c){return context(c)->password.shop;}
static int foreign(void *c){(void)c;return af_np_foreign();}
static int pocket(void *c){(void)c;return native_private && af_np_pocket_index(native_private,0)>=0;}
static int order(void *c,int index){(void)c;return af_np_order_get(4,index);}
static void set_order(void *c,int index,int value){(void)c;af_np_order_set(4,index,value);}
static int ready(void *c){(void)c;return af_np_continue(af_np_window())==1;}
static int hidden(void *c){(void)c;return af_np_hidden(af_np_window())==1;}
static int opened(void *c){(void)c;return af_np_opened(af_np_window())==1;}
static void hide(void *c){(void)c;af_np_hide(af_np_window());}
static void open_message(void *c){(void)c;af_np_open(af_np_window());}
static int editor(void *c,u8 *code){
    u8 *play=context(c)->password.play;
    if(!play || word(play,0x1D98))return 0;
    af_np_editor(play+0x1CBC,10,5,28,code,(void *)2);return 1;
}
static int menu(void *c){return word(context(c)->password.play,0x1D98)!=0;}
static int choice(void *c){(void)c;return af_np_choice_number(af_np_choice_window());}
static void force(void *c){(void)c;af_np_force(af_np_window());}
static int name(const u8 *native,u8 *donor){
    int n=0,i,valid=1;
    for(i=0;i<8;i++)donor[i]=32;
    if(!native)return 0;
    for(i=0;i<6;i++) {
        u32 value;
        if(native[i]==0x80) {
            if(++i>=6){valid=0;break;}
            value=native[i];
        } else value=af_np_native_to_donor[native[i]];
        if(value>255){valid=0;value=255;}
        donor[n++]=(u8)value;
    }
    return valid;
}
static int check(void *c,const u8 *code,const u8 *player,const u8 *town,struct AfPasswordOffer *offer){
    struct Session *s=context(c);
    int result=af_v3_password_boot_check(code,player,town,offer);
    if(result!=AF_PW_INVALID && result!=AF_PW_CANCEL) {
        if(!af_v3_password_decode((const u8 *)0x804C2800u,AF_NP_TABLE_BYTES,code,28,&s->decoded))return AF_PW_INVALID;
        if(!s->name_valid && (s->decoded.type==0 || s->decoded.type==1 || s->decoded.type==4))
            result=AF_PW_WRONG_NAME;
    }
    return result;
}
static void info(void *window,int field,const u8 *source){
    u8 data[16];int i,n=0;
    for(i=0;i<8;i++) {
        u16 mapped=af_np_donor_to_native[source[i]];
        if(mapped>>8)data[n++]=(u8)(mapped>>8);
        data[n++]=(u8)mapped;
    }
    af_np_free_string(window,field,data,n);
}
static void message(void *c,int result,const struct AfPasswordOffer *offer){
    struct Session *s=context(c);void *window=af_np_window();int id;
    if(result<10)id=af_np_results[result];
    else id=result==AF_NP_SAY?AF_NP_SAY_ID:result==AF_NP_FULL?AF_NP_FULL_ID:
        result==AF_NP_FOREIGN?AF_NP_FOREIGN_ID:AF_NP_LIMIT_ID;
    if(offer) {
        u8 item[16];if(!af_np_item_name(item,sizeof(item),offer->item))af_np_fault(-1);
        af_np_item_string(window,2,item,16);
        info(window,6,s->decoded.str1);info(window,7,s->decoded.str0);
    }
    /* Gift-page order 72 locks the English pager. An inventory refusal can
     * replace that page before its matching order 73; release only that lock. */
    if(result==AF_NP_FULL)word(window,0x28C)&=~(1u<<14);
    if(s->password.stage==AF_NP_RESULT_WAIT || s->password.stage==AF_NP_RETRY_WAIT ||
            s->password.stage==AF_NP_GIFT_START)af_np_change_message(window,id);
    else af_np_set_message(window,id);
    word(shop(c),0x968)=id;
}
static int insert(void *c,u32 item){(void)c;return native_private && af_np_insert(native_private,(u16)item,1)==1;}
static void rustle(void *c){af_np_sound(AF_NP_RUSTLE,((u8 *)shop(c))+28);}
static void lock(void *c,int value){(void)c;if(value)af_np_lock(af_np_window());else af_np_unlock(af_np_window());}
static void head(void *c,int value){byte(shop(c),0x876)=(u8)value;}
static void *left(void *c){return *(void **)((u8 *)shop(c)+0x848);}
static void set_left(void *c,void *item){*(void **)((u8 *)shop(c)+0x848)=item;}
static void *birth(void *c,u32 item,int mode,int present,void *actor){
    struct Handover *h=handover();(void)c;return h&&h->birth?h->birth((u16)item,mode,present,actor):0;
}
static void request(void *c,int mode){struct Handover *h=handover();if(h&&h->request)h->request(shop(c),mode);}
static int stopped(void *c){return word(shop(c),0x188)==1;}
static int clips(void *c){
    struct Handover *h=handover();void *npc=*(void **)0x80136EECu;(void)c;
    return h && h->birth && h->request && h->actor && npc && word(npc,0x104);
}
static void *master(void *c){struct Handover *h=handover();(void)c;return h?h->master:0;}
static void animation(void *c,int stage){
    void *npc=*(void **)0x80136EECu;int id=stage==AF_NP_GIFT_TAKEOUT?26:stage==AF_NP_GIFT_TRANSFER?27:5;
    if(npc && word(npc,0x104))((void (*)(void *,int,int))word(npc,0x104))(shop(c),id,1);
}
static void finish(void *c,int question){struct Session *s=context(c);s->other=0;af_np_setup(shop(c),s->password.play,question?7:8);}
static struct AfNookPasswordOps ops(struct Session *s){
    struct AfNookPasswordOps o={s,&s->gift_count,foreign,pocket,order,set_order,ready,hidden,opened,
        hide,open_message,editor,menu,check,message,force,choice,insert,rustle,lock,head,left,set_left,
        birth,request,stopped,animation,clips,master,finish};return o;
}
void af_np_destroy(void *actor,void *play){
    if(af_v3_password_boot_ready() && session->password.shop==actor) {
        session->password.stage=AF_NP_IDLE;session->other=0;
        session->password.shop=session->password.play=0;
    }
    af_np_original_destroy(actor,play);
}
void af_np_actor_dispatch(void *actor,void *play,void (*original)(void *,void *)){
    struct Session *s;struct AfNookPasswordOps o;
    if(!af_v3_password_boot_ready()){original(actor,play);return;}
    s=session;
    if(s->password.shop!=actor || s->password.play!=play) {
        s->password.stage=AF_NP_IDLE;s->other=0;s->password.shop=actor;s->password.play=play;
    }
    o=ops(s);
    if(s->password.stage!=AF_NP_IDLE){af_nook_password_step(&s->password,&o);return;}
    if(word(actor,0x938)==7 && ready(s) && order(s,9)) {
        int selected=choice(s);
        if(s->other) {
            if(selected==0) {
                u8 player[8],town[8];
                s->other=0;s->name_valid=name(native_private,player);
                s->name_valid&=name(af_np_town(),town);
                af_nook_password_begin(&s->password,&o,actor,play,player,town);force(s);return;
            }
            if(selected==1) {
                s->other=0;af_np_set_message(af_np_window(),AF_NP_CANCEL_NATIVE_ID);
                word(actor,0x968)=AF_NP_CANCEL_NATIVE_ID;force(s);finish(s,0);return;
            }
            return;
        }
        if(selected==3) {
            s->other=1;set_order(s,9,0);
            af_np_set_message(af_np_window(),AF_NP_OTHER_ID);word(actor,0x968)=AF_NP_OTHER_ID;
            force(s);return;
        }
    }
    original(actor,play);
}
