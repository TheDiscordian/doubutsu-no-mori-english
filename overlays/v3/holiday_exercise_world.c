/* One validated active-player context surrounds every complete exercise talk
 * callback. The GC Private view is never passed to native inventory functions. */
#include "holiday_exercise.h"
#include "holiday_cards.h"
#include "holiday_world.h"
#include "holiday_state.h"
#include "holiday_native.h"
#include "holiday_dialogue.h"
#include "constants.h"
extern u8 *af_v3_card_data(void);
extern u16 af_holiday_item_display(u32);
extern int af_he_native_sum(void *,u16,int),af_he_native_find(void *,u16,int);
extern int af_he_native_give(void *,u16,int);
extern void af_he_native_set(void *,int,u16,int);
extern const AFHolidayDialogue af_holiday_dialogue_data;
extern const u8 *af_he_native_town(void);
extern void af_he_native_item_string(void *,int,const u8 *,int);
static struct {
    ACTOR *actor;AFHPPrivate *native;Private_c view;
    int player,failed,open;u16 inserted;
} context;

int af_he_failed(void) {return !context.open || context.failed;}
void af_he_fault(void) {context.failed=1;}
static int current(void) {
    return context.open && !context.failed && context.actor &&
        af_he_player()==context.player && af_hp_private()==context.native;
}
ACTOR *af_he_talk_actor(void) {return current()?context.actor:0;}
void af_he_forget(ACTOR *actor) {
    /* Actor storage can be reused after scene cleanup. No later occupant may
     * inherit a previous conversation's borrowed player/card context. */
    if(context.actor==actor) {
        context.actor=0;context.native=0;context.failed=0;context.open=0;
        context.player=-1;context.inserted=0;
    }
}
int af_he_begin(ACTOR *actor,int first) {
    int player=af_he_player();AFHPPrivate *native=af_hp_private();
    if(!actor || !af_hp_owned(actor) || !native || player<0 || player>4)return 0;
    if(!first && (context.actor!=actor || context.player!=player || context.native!=native || context.failed))return 0;
    if(first) {
        context.actor=actor;context.player=player;context.native=native;
        context.failed=0;context.inserted=0;
    }
    context.open=1;
    AFHolidayCard card={{0,0,0},0};
    if(player<4 && !af_holiday_cards_get(af_v3_card_data(),(u32)player,&card)) {
        af_he_fault();return 0;
    }
    context.view.radiocard.last_date=(lbRTC_ymd_c){card.last_date.year,card.last_date.month,card.last_date.day};
    context.view.radiocard.days=card.days;
    return 1;
}
int af_he_finish(int ended) {
    int ok=current();
    if(ok && context.player<4) {
        const mPr_day_day_c *r=&context.view.radiocard;
        AFHolidayCard card={{r->last_date.year,r->last_date.month,r->last_date.day},r->days};
        ok=af_holiday_cards_set(af_v3_card_data(),(u32)context.player,&card);
    }
    if(!ok)af_he_fault();
    context.open=0;
    if(ended)context.actor=0;
    return ok;
}
Private_c *af_he_private(void) {
    if(!current())af_he_fault();
    return &context.view;
}
int af_he_item(u16 source) {
    if(!source)return 0;
    if(source>=ITM_EXCERCISE_CARD00 && source<=ITM_EXCERCISE_CARD12)
        return af_holiday_item_display(source)==source?source:-1;
    u32 n=af_holiday_world_resolve(0,source);return n && n<=65535?(int)n:-1;
}
static int possession(void *view,u16 item,int condition,int write) {
    if(!current() || view!=&context.view || condition || (write && context.player>=4)) {
        af_he_fault();return -1;
    }
    int native=af_he_item(item);if(native<0)af_he_fault();return native;
}
int mPr_GetPossessionItemSumWithCond(void *view,u16 item,int condition) {
    int native=possession(view,item,condition,0);
    return native<0?0:af_he_native_sum(context.native,(u16)native,condition);
}
int mPr_GetPossessionItemIdxWithCond(void *view,u16 item,int condition) {
    int native=possession(view,item,condition,0);
    return native<0?-1:af_he_native_find(context.native,(u16)native,condition);
}
void mPr_SetPossessionItem(void *view,int slot,u16 item,int condition) {
    int native=possession(view,item,condition,1);
    if(native<0 || slot<0 || slot>=15) {af_he_fault();return;}
    af_he_native_set(context.native,slot,(u16)native,condition);
}
int mPr_SetFreePossessionItem(void *view,u16 item,int condition) {
    int native=possession(view,item,condition,1);
    if(native<=0) {af_he_fault();return 0;}
    int n=af_he_native_give(context.native,(u16)native,condition);
    if(n==1)context.inserted=item;else af_he_fault();
    return n;
}
u8 mSC_get_soncho_event(void) {return (u8)af_holiday_native_current();}
int mSC_trophy_get(int event) {
    if(!current() || context.player>=4 || event<0 || event>=28) {af_he_fault();return 1;}
    int n=af_v3_reward_flag((u32)context.player,0,(u32)event,0);
    if(n<0)af_he_fault();
    return n!=0;
}
u16 mSC_trophy_item(int event) {
    if(!current() || event<0 || event>=28) {af_he_fault();return 0;}
    struct AfHolidayOps ops={.resolve=af_holiday_world_resolve};
    struct AfHolidayOffer offer;
    u32 gender=((const u8 *)context.native)[0x10];
    int count=af_v3_holiday_count(af_holiday_reward_data,370,(u32)event,gender,&ops);
    if(count<=0) {af_he_fault();return 0;}
    u32 roll=af_holiday_reward_data[16+(u32)event*8+4]==1?(u32)(fqrand()*(f32)count):0;
    if(roll>=(u32)count || !af_v3_holiday_select(af_holiday_reward_data,370,(u32)event,gender,roll,&ops,&offer)) {
        af_he_fault();return 0;
    }
    return (u16)offer.source_item;
}
void mSC_trophy_set(int event) {
    if(!current() || context.player>=4 || event<0 || event>=28 || !context.inserted ||
       af_v3_reward_flag((u32)context.player,0,(u32)event,1)!=1)af_he_fault();
    context.inserted=0;
}
static AFDiaryDate date(int y,int m,int d) {
    return (AFDiaryDate){(u16)y,(u8)m,(u8)d};
}
int mCD_calendar_event_check(int year,int month,int day,int player,int event) {
    if(!current() || player!=-1) {af_he_fault();return 0;}
    if(context.player==4)return 0;
    const lbRTC_time_c *t=af_he_clock();
    int n=af_diary_calendar_event_check(af_v3_diary_data(),(u32)context.player,
        date(t->year,t->month,t->day),date(year,month,day),(u32)event);
    if(n<0)af_he_fault();
    return n>0;
}
void mCD_calendar_event_on(int year,int month,int day,int event) {
    if(!current() || context.actor->npc_id!=SP_NPC_SONCHO_D078) {af_he_fault();return;}
    if(context.player==4)return;
    AFDiaryDates dates;AFDiary *diary=af_v3_diary_data();
    if(!af_holiday_state_dates(diary,(u32)year,&dates) ||
       af_diary_calendar_event(diary,(u32)context.player,date(year,month,day),dates,(u32)event)<0)af_he_fault();
}
int af_he_event_string(int event) {
    if(!current() || event<0 || event>=28)return 0;
    const AFHolidayDialogue *d=&af_holiday_dialogue_data;
    if(d->magic!=0x41464844 || d->version!=1 || d->count!=3)return 0;
    u8 text[16];u32 used=0,length=16;
    if(event==4) {
        const u8 *town=af_he_native_town();if(!town)return 0;
        used=6;while(used && town[used-1]==' ')--used;
        for(u32 i=0;i<used;i++)text[i]=town[i];
    }
    while(length && d->events[event][length-1]==' ')--length;
    if(used+length>16)return 0;
    for(u32 i=0;i<length;i++)text[used++]=d->events[event][i];
    while(used<16)text[used++]=' ';
    void *window=mMsg_Get_base_window_p();if(!window)return 0;
    af_he_native_item_string(window,1,text,16);return 1;
}
