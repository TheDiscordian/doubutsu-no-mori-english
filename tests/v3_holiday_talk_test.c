/* Compare the connected port with the complete checked local donor talk file.
 * Native demo/actor transport is deliberately not claimed by these host doubles. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_talk.h"
typedef unsigned char u8;
typedef AFDiaryDate lbRTC_time_c;
typedef int GAME,GAME_PLAY,mMsg_Window_c;
typedef void (*aNPC_TALK_REQUEST_PROC)(void);
typedef struct {struct {aNPC_TALK_REQUEST_PROC talk_request_proc;int melody_inst;} talk_info;} NPC_ACTOR;
typedef struct {
    NPC_ACTOR npc_class;
    unsigned year,month,day,item,talk,event,think,melody_inst,_9ac;
} ACTOR,NPC_SONCHO2;
typedef void (*aEV_SONCHO2_TALK_PROC)(NPC_SONCHO2 *,GAME *);
enum {FALSE,TRUE,EMPTY_NO=0,mPr_ITEM_COND_NORMAL=0,mDemo_ORDER_NPC0=0,mDemo_ORDER_NPC1=1,
    mDemo_ORDER_7=7,aHOI_REQUEST_PUTAWAY=1,mSC_EVENT_HARVEST_FESTIVAL=27,
    MSG_SONCHO_EVENTS=0x3280,MSG_SONCHO_EVENTS_COUNT=10,MSG_HARVEST_FESTIVAL=0x3391,
    MSG_SONCHO_LIGHTHOUSE_1=0x33F4,MSG_SONCHO_LIGHTHOUSE_2=0x340B,
    aES2_TALK_0=0,aES2_TALK_1,aES2_TALK_2,aES2_TALK_LIGHTHOUSE_QUEST_START_1,
    aES2_TALK_LIGHTHOUSE_QUEST_START_2,aES2_TALK_5};
struct Context {unsigned claims[28],free,gives,marks,item,after,quests,disabled;};
static struct {
    unsigned player_no,repeat;struct {lbRTC_time_c rtc_time;} time;
    AFDiary *diary;AFDiaryDates dates;struct Context *io;
    AFHolidayAction action;int continuation,delivery,ended;
} ref;
#define Common_Get(field) (ref.field)
#define Now_Private ((void *)0)
#define RANDOM_F(n) ((void)(n),(float)ref.repeat)
#define mDemo_CAN_ACTOR_TALK(actor) ((void)(actor),ref.ended)
static void none_proc1(void) {}
static void mActor_NONE_PROC1(NPC_SONCHO2 *s,GAME *g) {(void)s;(void)g;}
static int aES2_change_talk_proc(ACTOR *,u8);
static unsigned resolve(void *ctx,unsigned item) {
    return ((struct Context *)ctx)->disabled?0:(item^0x4000u);
}
static int claimed(void *ctx,unsigned event) {return ((struct Context *)ctx)->claims[event];}
static int give(void *ctx,unsigned item) {
    struct Context *c=ctx;
    if(!c->free)return 0;
    --c->free;++c->gives;c->item=item;return 1;
}
static void mark(void *ctx,unsigned event) {
    struct Context *c=ctx;assert(event<28 && !c->claims[event]);
    c->claims[event]=1;++c->marks;
}
static int slots(void *ctx) {return ((struct Context *)ctx)->free;}
static int lighthouse_after(void *ctx) {return ((struct Context *)ctx)->after;}
static void lighthouse_start(void *ctx) {++((struct Context *)ctx)->quests;}
static mMsg_Window_c *mMsg_Get_base_window_p(void) {static int window;return &window;}
static int mMsg_Check_MainNormalContinue(mMsg_Window_c *p) {(void)p;return ref.continuation;}
static void mDemo_Set_msg_num(unsigned msg) {ref.action.message=msg;ref.action.effects|=AF_HOLIDAY_MESSAGE;}
static void mMsg_Set_continue_msg_num(mMsg_Window_c *p,unsigned msg) {
    (void)p;mDemo_Set_msg_num(msg);ref.action.effects|=AF_HOLIDAY_CONTINUE;
}
static int mPr_GetPossessionItemSumWithCond(void *p,unsigned item,int cond) {
    (void)p;(void)cond;assert(item==EMPTY_NO);return ref.io->free;
}
static void mPr_SetFreePossessionItem(void *p,unsigned item,int cond) {
    (void)p;(void)cond;assert(give(ref.io,item));
}
static int mDemo_Get_OrderValue(int who,int value) {assert(who==0 && value==1);return ref.delivery?2:0;}
static void mDemo_Set_OrderValue(int who,int value,unsigned data) {
    assert(who==1);
    if(value==0) {ref.action.effects|=AF_HOLIDAY_HANDOVER;ref.action.item=data;}
}
static int mSC_trophy_get(unsigned event) {return claimed(ref.io,event);}
static void mSC_trophy_set(unsigned event) {mark(ref.io,event);}
static void mSC_item_string_set(unsigned item,int which) {
    (void)which;ref.action.item=item;ref.action.effects|=AF_HOLIDAY_ITEM_NAME;
}
static void mSC_event_name_set(unsigned event) {ref.action.event=event;ref.action.effects|=AF_HOLIDAY_EVENT_NAME;}
static int mSC_LightHouse_Talk_After_Check(void) {return lighthouse_after(ref.io);}
static void mSC_LightHouse_Quest_Start(void) {lighthouse_start(ref.io);}
static void mDemo_Set_talk_turn(int v) {assert(v==1);}
static void mDemo_Set_camera(int v) {assert(v==3);}
static void mDemo_Set_ListenAble(void) {}
static void mDemo_Start(ACTOR *a) {(void)a;ref.action.effects|=AF_HOLIDAY_BEGIN;}
static void mDemo_Request(int order,ACTOR *actor,void (*cb)(ACTOR *)) {assert(order==7);cb(actor);}
static int mCD_calendar_event_check(unsigned y,unsigned m,unsigned d,int p,unsigned e) {
    assert(p==-1);return af_diary_calendar_event_check(ref.diary,ref.player_no,
        ref.time.rtc_time,(AFDiaryDate){y,m,d},e);
}
static void mCD_calendar_event_on(unsigned y,unsigned m,unsigned d,unsigned e) {
    if(ref.player_no<4)assert(af_diary_calendar_event(ref.diary,ref.player_no,
        (AFDiaryDate){y,m,d},ref.dates,e)==1);
}
static void lbRTC_TimeCopy(lbRTC_time_c *out,const lbRTC_time_c *in) {*out=*in;}
static void lbRTC_Add_DD(lbRTC_time_c *d,int count) {
    while(count--) {
        if(d->day==af_diary_days(d->year,d->month)) {
            d->day=1;
            if(d->month==12) {d->month=1;++d->year;}else ++d->month;
        } else ++d->day;
    }
}
static void mString_Load_DayStringFromRom(u8 out[4],unsigned day) {memset(out,0,4);out[0]=day;}
static void mMsg_Set_free_str(mMsg_Window_c *w,unsigned i,u8 *text,unsigned bytes) {
    (void)w;assert(i<2 && bytes==4);ref.action.lighthouse_dates[i].day=text[0];
    ref.action.effects|=AF_HOLIDAY_LIGHTHOUSE_DATES;
}
static void aES2_setup_think_proc(NPC_SONCHO2 *s,GAME_PLAY *p,unsigned think) {
    (void)s;(void)p;(void)think;ref.action.effects|=AF_HOLIDAY_END;
}
#include "reference-holiday-talk.inc"

static AFDiary live,reference,snapshot;
static unsigned char table[1024];static unsigned table_bytes;
static void same(const AFHolidayAction *a,const AFHolidayTalk *talk,const NPC_SONCHO2 *npc,
        const struct Context *io) {
    assert(a->effects==ref.action.effects);
    if(a->effects&AF_HOLIDAY_MESSAGE)assert(a->message==ref.action.message);
    if(a->effects&AF_HOLIDAY_ITEM_NAME)assert(a->item==ref.action.item);
    if(a->effects&AF_HOLIDAY_EVENT_NAME)assert(a->event==ref.action.event);
    if(a->effects&AF_HOLIDAY_LIGHTHOUSE_DATES)
        for(unsigned i=0;i<2;i++)assert(a->lighthouse_dates[i].day==ref.action.lighthouse_dates[i].day);
    assert(talk->phase==npc->talk);
    assert(!memcmp(&live,&reference,sizeof(live)));
    assert(!memcmp(io,ref.io,sizeof(*io)));
}
static void clear_action(void) {memset(&ref.action,0,sizeof(ref.action));}
static void scenario(unsigned player,unsigned event,unsigned mode,unsigned repeat) {
    struct Context io={0},rio={0};io.free=mode==4?0:15;io.after=mode==2;
    if(event<28 && (mode==2 || mode==3))io.claims[event]=1;
    rio=io;af_diary_reset(&live);
    AFHolidayWorld w={.diary=&live,.dates={23,9,29},.today={2006,12,28},.player=player,
        .rewards=table,.reward_bytes=table_bytes,.items={&io,resolve,claimed,give,mark},
        .context=&io,.free_slots=slots,.lighthouse_after=lighthouse_after,.lighthouse_start=lighthouse_start};
    if(player<4) {
        assert(af_diary_calendar_visit(&live,player,w.today,w.dates)==1);
        if(mode==1 || mode==3)assert(af_diary_calendar_event(&live,player,w.today,w.dates,event)==1);
    }
    reference=live;snapshot=live;
    memset(&ref,0,sizeof(ref));ref.diary=&reference;ref.dates=w.dates;ref.player_no=player;
    ref.time.rtc_time=w.today;ref.repeat=repeat;ref.io=&rio;
    AFHolidayTalk talk={0};AFHolidayAction a;
    assert(af_holiday_talk_prepare(&talk,&w,event,w.today,0,0,repeat,&a)==1);
    assert(!memcmp(&live,&snapshot,sizeof(live))); /* Preparing/requesting is not attendance. */
    NPC_SONCHO2 npc={.year=w.today.year,.month=w.today.month,.day=w.today.day,
        .item=talk.offer.item,.event=event};
    aES2_set_norm_talk_info(&npc);same(&a,&talk,&npc,&io);
    clear_action();assert(af_holiday_talk_start(&talk,&w,&a)==1);
    assert(aES2_talk_init(&npc,NULL)==1);same(&a,&talk,&npc,&io);
    unsigned quests=io.quests;assert(af_holiday_talk_start(&talk,&w,&a)==0);assert(io.quests==quests);
    clear_action();ref.continuation=1;
    assert(af_holiday_talk_step(&talk,&w,1,0,0,&a)==1);
    aES2_talk_end_chk(&npc.npc_class,NULL);same(&a,&talk,&npc,&io);
    clear_action();ref.continuation=0;ref.delivery=1;
    assert(af_holiday_talk_step(&talk,&w,0,1,0,&a)==1);
    aES2_talk_end_chk(&npc.npc_class,NULL);same(&a,&talk,&npc,&io);
    clear_action();ref.ended=1;
    assert(af_holiday_talk_step(&talk,&w,0,1,1,&a)==1);
    assert(aES2_talk_end_chk(&npc.npc_class,NULL)==1);same(&a,&talk,&npc,&io);
    assert(!talk.active && !talk.prepared);
    assert(af_holiday_talk_start(&talk,&w,&a)<0);
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    table_bytes=fread(table,1,sizeof(table),f);assert(feof(f));fclose(f);
    assert(af_v3_holiday_valid(table,table_bytes));
    for(unsigned p=0;p<5;p++)for(unsigned e=0;e<28;e++)for(unsigned mode=0;mode<5;mode++)
        for(unsigned repeat=0;repeat<3;repeat++)scenario(p,e,mode,repeat);
    for(unsigned e=101;e<=102;e++)for(unsigned mode=0;mode<3;mode+=2)
        for(unsigned repeat=0;repeat<3;repeat++)scenario(0,e,mode,repeat);

    /* Fail safely when the profile/player/pockets change during the demo. */
    struct Context io={.free=15};af_diary_reset(&live);
    AFHolidayWorld w={.diary=&live,.today={2006,1,1},.player=0,.rewards=table,
        .reward_bytes=table_bytes,.items={&io,resolve,claimed,give,mark},.context=&io,.free_slots=slots};
    AFHolidayTalk t={0};AFHolidayAction a;
    assert(af_diary_calendar_visit(&live,0,w.today,w.dates)==1);
    assert(af_holiday_talk_prepare(&t,&w,0,w.today,0,0,0,&a)==1);
    assert(af_holiday_talk_start(&t,&w,&a)==1);
    assert(af_holiday_talk_prepare(&t,&w,1,w.today,0,0,0,&a)==AF_DIARY_ARGUMENT);
    assert(af_holiday_talk_step(&t,&w,1,0,0,&a)==1);
    io.free=0;snapshot=live;
    assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==AF_DIARY_CHANGED);
    assert(!io.gives && !io.marks && t.phase==AF_HOLIDAY_GIVE);
    io.free=15;io.disabled=1;
    assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==AF_DIARY_CHANGED);
    io.disabled=0;w.player=1;
    assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==AF_DIARY_ARGUMENT);
    assert(!memcmp(&live,&snapshot,sizeof(live)) && !io.gives && !io.marks);
    w.player=0;assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==1);
    assert(io.gives==1 && io.marks==1);
    assert(af_holiday_talk_step(&t,&w,0,1,0,&a)==1);
    assert(io.gives==1 && io.marks==1);
    /* Exercise attendance never treats Copper or another villager as Tortimer. */
    w.today=(AFDiaryDate){2006,8,1};assert(af_diary_calendar_visit(&live,0,w.today,w.dates)==1);
    snapshot=live;assert(af_holiday_exercise_attend(&w,0,103)==0);
    assert(!memcmp(&live,&snapshot,sizeof(live)));
    assert(af_holiday_exercise_attend(&w,1,103)==1);
    assert(af_diary_calendar_event_check(&live,0,w.today,w.today,103)==1);
    w.player=4;snapshot=live;assert(af_holiday_exercise_attend(&w,1,103)==0);
    assert(!memcmp(&live,&snapshot,sizeof(live)));
    puts("All holiday conversation branches match donor C; attendance and guarded rewards connect");
    return 0;
}
