/* Mechanical state checks, not native shop gameplay or FlashRAM evidence. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/nook_password.c"
#include "../overlays/v3/password_policy.c"
struct Fixture {
    int foreign,free,orders[10],ready,hidden,opened,menu,choice,result;
    int insert_ok,insertions,births,locks,head,stopped,clip_ready,finish,question,message;
    int requests,mode,hide,force,rustle,animation;
    af_pw_u32 count;
    void *left,*master,*shop;
};
static int foreign(void *c){return ((struct Fixture *)c)->foreign;}
static int pocket(void *c){return ((struct Fixture *)c)->free;}
static int order(void *c,int i){assert(i==1||i==9);return ((struct Fixture *)c)->orders[i];}
static void set_order(void *c,int i,int v){assert(i==1||i==9);((struct Fixture *)c)->orders[i]=v;}
static int ready(void *c){return ((struct Fixture *)c)->ready;}
static int hidden(void *c){return ((struct Fixture *)c)->hidden;}
static int opened(void *c){return ((struct Fixture *)c)->opened;}
static int menu(void *c){return ((struct Fixture *)c)->menu;}
static void hide(void *c){((struct Fixture *)c)->hide++;}
static void open_message(void *c){((struct Fixture *)c)->opened=0;}
static int editor(void *c,af_pw_u8 *code){(void)c;assert(code);return 1;}
static int check(void *c,const af_pw_u8 *code,const af_pw_u8 *player,const af_pw_u8 *town,struct AfPasswordOffer *offer){
    assert(code&&player&&town);int r=((struct Fixture *)c)->result;
    if(r>0&&r<9)*offer=(struct AfPasswordOffer){0x3000,0x3200,(af_pw_u32)r};
    return r;
}
static void message(void *c,int m,const struct AfPasswordOffer *offer){
    (void)offer;((struct Fixture *)c)->message=m;
}
static void force(void *c){((struct Fixture *)c)->force++;}
static int choice(void *c){return ((struct Fixture *)c)->choice;}
static int insert(void *c,af_pw_u32 item){assert(item==0x3200);((struct Fixture *)c)->insertions++;return ((struct Fixture *)c)->insert_ok;}
static void rustle(void *c){((struct Fixture *)c)->rustle++;}
static void lock(void *c,int v){((struct Fixture *)c)->locks=v;}
static void head(void *c,int v){((struct Fixture *)c)->head=v;}
static void *left(void *c){return ((struct Fixture *)c)->left;}
static void set_left(void *c,void *v){((struct Fixture *)c)->left=v;}
static void *birth(void *c,af_pw_u32 item,int mode,int present,void *shop){
    struct Fixture *f=c;assert(item==0x3200&&mode==7&&present==1&&shop==f->shop);
    f->births++;f->master=shop;return &f->births;
}
static void request(void *c,int mode){struct Fixture *f=c;assert(mode==1||mode==2);f->requests++;f->mode=mode;}
static int stopped(void *c){return ((struct Fixture *)c)->stopped;}
static void animation(void *c,int stage){assert(stage>=AF_NP_GIFT_TAKEOUT&&stage<=AF_NP_GIFT_END);((struct Fixture *)c)->animation=stage;}
static int clip_ready(void *c){return ((struct Fixture *)c)->clip_ready;}
static void *master(void *c){return ((struct Fixture *)c)->master;}
static void finish(void *c,int question){struct Fixture *f=c;f->finish++;f->question=question;}
static struct AfNookPasswordOps ops(struct Fixture *f){
    struct AfNookPasswordOps o={.context=f,.gift_count=&f->count,.foreign=foreign,.pocket_free=pocket,
        .order=order,.set_order=set_order,.message_ready=ready,.message_hidden=hidden,.message_open=opened,
        .hide_message=hide,.open_message=open_message,.open_editor=editor,.menu_active=menu,.check=check,.message=message,
        .force_next=force,.choice=choice,.insert_present=insert,.rustle=rustle,.lock_message=lock,
        .lock_head=head,.left_item=left,.set_left_item=set_left,.birth=birth,.request_handover=request,
        .animation_stopped=stopped,.animation=animation,.handover_ready=clip_ready,.handover_master=master,.finish=finish};return o;
}
static void initialize(struct Fixture *f,struct AfNookPassword *s){
    memset(f,0,sizeof(*f));memset(s,0,sizeof(*s));f->free=f->insert_ok=f->clip_ready=1;
    f->shop=&f->head;f->choice=-1;
}
static void enter(struct Fixture *f,struct AfNookPassword *s,struct AfNookPasswordOps *o){
    assert(af_nook_password_begin(s,o,f->shop,f,(const af_pw_u8 *)"Player  ",(const af_pw_u8 *)"Forest  "));
    assert(!memcmp(s->code,"                            ",28));
    assert(!memcmp(s->player,"Player  ",8));assert(!memcmp(s->town,"Forest  ",8));
    assert(s->stage==AF_NP_INPUT_START);
    af_nook_password_step(s,o);assert(s->stage==AF_NP_INPUT_START);
    f->orders[9]=f->ready=1;af_nook_password_step(s,o);assert(s->stage==AF_NP_HIDE_WAIT&&!f->orders[9]);
    f->hidden=1;af_nook_password_step(s,o);assert(s->stage==AF_NP_MENU_WAIT);
    f->menu=1;af_nook_password_step(s,o);assert(s->stage==AF_NP_MENU_WAIT);
    f->menu=0;af_nook_password_step(s,o);assert(s->stage==AF_NP_RESULT_WAIT);
    f->opened=1;af_nook_password_step(s,o);
}
int main(void){
    struct Fixture f;struct AfNookPassword s;struct AfNookPasswordOps o;
    for(int result=0;result<10;result++) {
        initialize(&f,&s);o=ops(&f);f.result=result;enter(&f,&s,&o);
        if(result==0||result==8){assert(s.stage==AF_NP_RETRY_WAIT);assert(!f.finish);}
        else if(af_v3_password_result_gives_item((af_pw_u32)result))assert(s.stage==AF_NP_GIFT_START);
        else {assert(s.stage==AF_NP_IDLE&&f.finish==1);assert(f.question==(result==9));}
        assert(f.count==0&&f.insertions==0&&f.births==0);
    }
    for(int denial=0;denial<3;denial++) {
        initialize(&f,&s);o=ops(&f);
        if(denial==0)f.foreign=1;else if(denial==1)f.count=3;else f.free=0;
        assert(!af_nook_password_begin(&s,&o,f.shop,&f,(const af_pw_u8 *)"Player  ",(const af_pw_u8 *)"Forest  "));
        assert(s.stage==AF_NP_IDLE&&f.finish==1&&f.question==1);
        assert(f.message==(denial==0?AF_NP_FOREIGN:denial==1?AF_NP_GIFT_LIMIT:AF_NP_FULL));
    }
    initialize(&f,&s);o=ops(&f);f.result=AF_PW_FAMICOM;enter(&f,&s,&o);
    af_nook_password_step(&s,&o);assert(!f.insertions);
    f.orders[1]=2;f.clip_ready=0;af_nook_password_step(&s,&o);assert(!f.insertions);
    f.clip_ready=1;af_nook_password_step(&s,&o);
    assert(s.stage==AF_NP_GIFT_TAKEOUT&&s.inserted&&f.count==1&&f.insertions==1&&f.locks&&f.head);
    for(int i=0;i<20;i++)af_nook_password_step(&s,&o);
    assert(f.count==1&&f.insertions==1&&f.births==1&&s.stage==AF_NP_GIFT_TAKEOUT);
    f.stopped=1;af_nook_password_step(&s,&o);assert(s.stage==AF_NP_GIFT_TRANSFER&&f.mode==2);
    af_nook_password_step(&s,&o);assert(s.stage==AF_NP_GIFT_TRANSFER);
    f.master=&s;af_nook_password_step(&s,&o);assert(s.stage==AF_NP_GIFT_END&&!f.head&&!f.left&&f.locks);
    af_nook_password_step(&s,&o);assert(s.stage==AF_NP_GIFT_END);
    f.master=0;af_nook_password_step(&s,&o);assert(s.stage==AF_NP_IDLE&&!f.locks&&f.finish==1&&!f.question);
    initialize(&f,&s);o=ops(&f);f.result=AF_PW_USER;enter(&f,&s,&o);
    f.orders[1]=2;f.insert_ok=0;af_nook_password_step(&s,&o);
    assert(s.stage==AF_NP_IDLE&&f.insertions==1&&!f.count&&!f.births&&!f.locks&&!f.head&&f.question);
    initialize(&f,&s);o=ops(&f);f.result=AF_PW_INVALID;enter(&f,&s,&o);
    memset(s.code,'a',28);af_nook_password_step(&s,&o);assert(s.stage==AF_NP_RETRY_WAIT);
    f.choice=0;af_nook_password_step(&s,&o);assert(s.stage==AF_NP_HIDE_WAIT&&s.code[27]=='a');
    s.stage=AF_NP_RETRY_WAIT;f.choice=1;af_nook_password_step(&s,&o);assert(s.stage==AF_NP_IDLE&&f.question);
    puts("Nook result/retry and single-insertion animated-handover states pass");
    return 0;
}
