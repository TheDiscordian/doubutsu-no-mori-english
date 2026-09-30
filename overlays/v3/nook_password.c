/* GAFE01-r0 ac_npc_shop_common.c code entry, result/retry, and gift stages.
 * No donor actor offsets, invented delivery method, or saved counter. */
#include "nook_password.h"
static int services(const struct AfNookPasswordOps *o) {
    return o && o->gift_count && o->foreign && o->pocket_free && o->order &&
        o->set_order && o->message_ready && o->message_hidden && o->message_open &&
        o->hide_message && o->open_message && o->open_editor && o->menu_active && o->check &&
        o->message && o->force_next && o->choice && o->insert_present &&
        o->rustle && o->lock_message && o->lock_head && o->left_item &&
        o->set_left_item && o->birth && o->request_handover && o->animation_stopped && o->animation &&
        o->handover_ready && o->handover_master && o->finish;
}
static void end(struct AfNookPassword *s,const struct AfNookPasswordOps *o,int question) {
    s->stage=AF_NP_IDLE;
    o->finish(o->context,question);
}
int af_nook_password_begin(struct AfNookPassword *s,const struct AfNookPasswordOps *o,
    void *shop,void *play,const af_pw_u8 *player,const af_pw_u8 *town) {
    af_pw_u32 i;
    int denial=0;
    if(!s || !services(o) || !shop || !play || !player || !town || s->stage!=AF_NP_IDLE)
        return 0;
    if(o->foreign(o->context))denial=AF_NP_FOREIGN;
    else if(*o->gift_count>=3)denial=AF_NP_GIFT_LIMIT;
    else if(!o->pocket_free(o->context))denial=AF_NP_FULL;
    if(denial){o->message(o->context,denial,0);o->finish(o->context,1);return 0;}
    s->shop=shop;s->play=play;s->inserted=0;
    for(i=0;i<8;i++){s->player[i]=player[i];s->town[i]=town[i];}
    for(i=0;i<28;i++)s->code[i]=' ';
    o->set_order(o->context,9,0);
    o->message(o->context,AF_NP_SAY,0);
    s->stage=AF_NP_INPUT_START;
    return 1;
}
int af_nook_password_step(struct AfNookPassword *s,const struct AfNookPasswordOps *o) {
    void *c,*item;
    int result,choice;
    if(!s || !services(o) || !s->shop || !s->play || s->stage>AF_NP_GIFT_END)return 0;
    c=o->context;
    switch(s->stage) {
    case AF_NP_IDLE:return 0;
    case AF_NP_INPUT_START:
        if(o->order(c,9) && o->message_ready(c)) {
            o->set_order(c,9,0);o->hide_message(c);s->stage=AF_NP_HIDE_WAIT;
        }
        break;
    case AF_NP_HIDE_WAIT:
        if(o->message_hidden(c) && o->open_editor(c,s->code))s->stage=AF_NP_MENU_WAIT;
        break;
    case AF_NP_MENU_WAIT:
        if(!o->menu_active(c)){o->open_message(c);s->stage=AF_NP_RESULT_WAIT;}
        break;
    case AF_NP_RESULT_WAIT:
        if(!o->message_open(c))break;
        result=o->check(c,s->code,s->player,s->town,&s->offer);
        if(result<AF_PW_INVALID || result>AF_PW_CANCEL)result=AF_PW_INVALID;
        o->message(c,result,result==AF_PW_INVALID || result==AF_PW_CANCEL?0:&s->offer);
        o->force_next(c);
        if(result==AF_PW_INVALID || result==AF_PW_WRONG_NAME)s->stage=AF_NP_RETRY_WAIT;
        else if(af_v3_password_result_gives_item((af_pw_u32)result))s->stage=AF_NP_GIFT_START;
        else end(s,o,result==AF_PW_CANCEL);
        break;
    case AF_NP_RETRY_WAIT:
        if(!o->message_ready(c))break;
        choice=o->choice(c);
        if(choice!=0 && choice!=1)break;
        if(choice==0){o->hide_message(c);s->stage=AF_NP_HIDE_WAIT;}
        else{o->message(c,AF_PW_CANCEL,0);end(s,o,1);}
        o->force_next(c);
        break;
    case AF_NP_GIFT_START:
        if(o->order(c,1)!=2)break;
        /* The source inserts only in the takeout initializer. Check actual
         * service availability and insertion success before starting it. */
        if(!o->handover_ready(c) || o->handover_master(c))break;
        if(!s->inserted) {
            if(!s->offer.item || s->offer.item>=65535 || *o->gift_count>=3 ||
                !o->pocket_free(c) || !o->insert_present(c,s->offer.item)) {
                o->message(c,AF_NP_FULL,0);end(s,o,1);break;
            }
            s->inserted=1;++*o->gift_count;
            o->set_order(c,1,0);o->rustle(c);o->lock_message(c,1);o->lock_head(c,1);
        }
        s->stage=AF_NP_GIFT_TAKEOUT;
        o->animation(c,AF_NP_GIFT_TAKEOUT);
        break;
    case AF_NP_GIFT_TAKEOUT:
        if(!o->handover_ready(c))break;
        if(!o->left_item(c)) {
            item=o->birth(c,s->offer.item,7,1,s->shop);
            if(item){o->request_handover(c,1);o->set_left_item(c,item);}
        }
        if(o->animation_stopped(c) && o->handover_master(c)==s->shop) {
            o->request_handover(c,2);s->stage=AF_NP_GIFT_TRANSFER;
            o->animation(c,AF_NP_GIFT_TRANSFER);
        }
        break;
    case AF_NP_GIFT_TRANSFER:
        if(o->handover_ready(c) && o->handover_master(c)!=s->shop) {
            o->set_left_item(c,0);o->lock_head(c,0);s->stage=AF_NP_GIFT_END;
            o->animation(c,AF_NP_GIFT_END);
        }
        break;
    case AF_NP_GIFT_END:
        if(o->handover_ready(c) && !o->handover_master(c)) {
            o->lock_message(c,0);end(s,o,0);
        }
        break;
    default:return 0;
    }
    return 1;
}
