/* Connected native-field/reward/calendar test; inventory I/O is a host double. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "holiday_world.h"
#include "save_runtime.h"
#include "save_rewards.h"
#include "holiday-data.h"
_Static_assert(AF_SAVE_REWARD_OFFSET+48<=AF_SAVE_STATE,"Use the installed reward save profile");
unsigned char af_holiday_players[4][0xBD0],af_holiday_visitor[0xBD0];
const unsigned char *volatile af_holiday_active;
volatile unsigned char af_holiday_player,af_holiday_rtc[8];
unsigned char af_holiday_profiles[1024][80],af_holiday_metadata[1024][32];
struct AfSaveRuntime af_reward_state;
unsigned char af_reward_players[4*0xBD0],*af_reward_active;
static AFDiary diary;
static AFHolidayNpc npc;
static AFNpcStreamRecord stream={.name=0xD090,.texture_bytes=4128};
static unsigned char draw[100];
static AFNpcExtra registry={.name=0xD090,.profile=0xCC,.flags=3,
    .actor_bytes=0xA34,.draw=draw,.stream=&stream,.voice=281,.model_bank=448,.texture_bank=449};
static unsigned int rng_calls,rng_next,gives,marks,capacity=15,save_queries;
static unsigned short last_item;
const AFNpcExtra *af_v3_npc_extra_owned(const void *a) {return a==&npc?&registry:0;}
AFDiary *af_v3_diary_data(void) {return &diary;}
void af_v3_require_save_state(void) {++save_queries;}
void af_v3_save_halt(int error) {(void)error;abort();}
void af_v3_catalogue_clear(unsigned char *p) {(void)p;abort();}
void af_v3_reward_stop_fanfare(void *a) {(void)a;abort();}
int af_holiday_native_free(const void *p,unsigned short item,unsigned int cond) {
    assert(p==af_holiday_players[af_holiday_player] && item==0 && cond==0);return capacity;
}
int af_holiday_native_give(void *p,unsigned short item,unsigned int cond) {
    assert(p==af_holiday_players[af_holiday_player] && item && cond==0);
    if(!capacity)return 0;
    --capacity;++gives;last_item=item;return 1;
}
static unsigned int random_bounded(void *a,unsigned int n) {
    assert(a==&npc && n);++rng_calls;return rng_next;
}
static unsigned int half(const unsigned char *p) {return p[0]*256u+p[1];}
static void date(unsigned int month,unsigned int day) {
    af_holiday_rtc[6]=7;af_holiday_rtc[7]=0xEA;
    af_holiday_rtc[5]=month;af_holiday_rtc[3]=day;
}
static void player(unsigned int p) {
    af_holiday_player=p;af_holiday_active=p<4?af_holiday_players[p]:af_holiday_visitor;
}
static void reset(unsigned int p) {
    memset(&npc,0,sizeof(npc));af_diary_reset(&diary);
    memset(&af_reward_state,0,sizeof(af_reward_state));
    rng_calls=rng_next=gives=marks=save_queries=0;capacity=15;last_item=0;
    player(p);date(1,1);npc.ops.random=random_bounded;
}
static unsigned int bind(void) {
    unsigned int gender=99;
    assert(af_holiday_world_bind(&npc,(AFDiaryDates){0,0,0},&gender)==1);
    return gender;
}
static void load(const char *path,void *out,size_t bytes) {
    FILE *f=fopen(path,"rb");assert(f);assert(fread(out,1,bytes,f)==bytes);
    assert(fgetc(f)==EOF);fclose(f);
}
int main(int argc,char **argv) {
    assert(argc==3);
    load(argv[1],af_holiday_profiles,sizeof(af_holiday_profiles));
    load(argv[2],af_holiday_metadata,sizeof(af_holiday_metadata));
    reset(0);assert(bind()==0);
    /* The current admission controls both complete records. Then disable the
     * candidates for the existing no-gift fixture, without changing identities. */
    unsigned int candidate_count=half(af_holiday_destination_data+6);
    for(unsigned int i=0;i<candidate_count;++i) {
        const unsigned char *r=af_holiday_destination_data+16+i*8;
        unsigned int slot=half(r+4)-1024;
        unsigned int selected=af_holiday_profiles[slot][7]==1 && af_holiday_metadata[slot][7]==1;
        assert(af_holiday_world_resolve(&npc,half(r))==(selected?half(r+2):0));
        af_holiday_profiles[slot][7]=af_holiday_metadata[slot][7]=0;
    }
    /* A diary-only profile can attend every event without importing its gift.
     * No item string, handover, fake receipt, or RNG call is needed. Visitors
     * still cannot write a resident's diary. */
    for(unsigned int p=0;p<5;++p)for(unsigned int event=0;event<28;++event) {
        reset(p);bind();unsigned int variant=99;AFHolidayAction action;
        assert(af_holiday_world_variant(&npc,event,0,&variant) && variant==0 && !rng_calls);
        AFDiary snapshot=diary;
        assert(af_holiday_talk_prepare(&npc.actor.talk,&npc.world,event,npc.world.today,
            0,variant,0,&action)>0);
        assert(action.message==af_v3_holiday_chat(event) && action.effects==AF_HOLIDAY_MESSAGE);
        assert(!memcmp(&snapshot,&diary,sizeof(diary)));
        assert(af_holiday_talk_start(&npc.actor.talk,&npc.world,&action)>0);
        assert(action.effects==AF_HOLIDAY_BEGIN);
        if(p==4)assert(!memcmp(&snapshot,&diary,sizeof(diary)));
        else assert(af_diary_calendar_event_check(&diary,p,npc.world.today,npc.world.today,event)==(event==17?0:1));
        assert(af_holiday_talk_step(&npc.actor.talk,&npc.world,1,1,1,&action)>0);
        assert(action.effects==AF_HOLIDAY_END && !gives && !last_item && !rng_calls);
        for(unsigned int owner=0;owner<4;++owner)assert(!af_v3_reward_flag(owner,0,event,0));
    }
    reset(0);bind();
    /* Exercise the actual shared records for every candidate, not invented IDs. */
    for(unsigned int i=0;i<candidate_count;++i) {
        const unsigned char *r=af_holiday_destination_data+16+i*8;
        unsigned int donor=half(r),item=half(r+2),slot=half(r+4)-1024;
        af_holiday_profiles[slot][7]=af_holiday_metadata[slot][7]=1;
        assert(af_holiday_world_resolve(&npc,donor)==item);
        af_holiday_profiles[slot][7]=0;
        assert(af_holiday_world_resolve(&npc,donor)==0);
        af_holiday_profiles[slot][7]=1;af_holiday_metadata[slot][7]=0;
        assert(af_holiday_world_resolve(&npc,donor)==0);
        af_holiday_metadata[slot][7]=1;
        if(half(r+6)) {
            af_holiday_metadata[slot][29]^=1;
            assert(af_holiday_world_resolve(&npc,donor)==0);
            af_holiday_metadata[slot][29]^=1;
        }
    }
    assert(af_holiday_world_resolve(&npc,0x1FC0)==0x3C94);
    assert(af_holiday_world_resolve(&npc,0x2B00)==0x2B10);
    if(candidate_count==66)assert(af_holiday_world_resolve(&npc,0x1FCC)==0x3C48);
    assert(!af_holiday_world_resolve(&npc,0x10000));
    /* All 28 events, every actual reward variant, both gender branches. */
    unsigned int handovers=0;
    for(unsigned int event=0;event<28;++event)for(unsigned int gender=0;gender<2;++gender) {
        reset(2);af_holiday_players[2][0x10]=gender;assert(bind()==gender);
        int count=af_v3_holiday_count(npc.world.rewards,370,event,gender,&npc.world.items);
        assert(count>0);
        for(int variant=0;variant<count;++variant) {
            reset(2);assert(bind()==gender);rng_next=variant;
            unsigned int picked=99;
            assert(af_holiday_world_variant(&npc,event,gender,&picked));assert(picked==(unsigned int)variant);
            assert(rng_calls==(af_holiday_reward_data[16+event*8+4]==1));
            AFHolidayAction action;
            assert(af_holiday_talk_prepare(&npc.actor.talk,&npc.world,event,npc.world.today,
                gender,picked,0,&action)>0);
            assert(!npc.world.items.claimed(&npc,event));
            assert(!af_diary_calendar_event_check(&diary,2,npc.world.today,npc.world.today,event));
            assert(af_holiday_talk_start(&npc.actor.talk,&npc.world,&action)>0);
            assert(af_diary_calendar_event_check(&diary,2,npc.world.today,npc.world.today,event)==
                (event==17?0:1)); /* Moon Festival uses its source month-specific flag. */
            assert(af_holiday_talk_step(&npc.actor.talk,&npc.world,1,0,0,&action)>0);
            assert(!gives && !npc.world.items.claimed(&npc,event));
            assert(af_holiday_talk_step(&npc.actor.talk,&npc.world,0,1,0,&action)>0);
            assert(gives==1 && last_item==npc.actor.talk.offer.item && npc.world.items.claimed(&npc,event)==1);
            assert(af_holiday_talk_step(&npc.actor.talk,&npc.world,0,1,0,&action)>0 && gives==1);
            for(unsigned int p=0;p<4;++p)assert(af_v3_reward_flag(p,0,event,0)==(p==2));
            ++handovers;
        }
    }
    /* Full inventory and a stale selection never set the saved receipt. */
    reset(0);bind();struct AfHolidayOffer offer;
    assert(af_v3_holiday_select(af_holiday_reward_data,370,1,0,0,&npc.world.items,&offer));
    capacity=0;assert(!af_v3_holiday_commit(af_holiday_reward_data,370,&npc.world.items,&offer));
    assert(!gives && !af_v3_reward_flag(0,0,1,0));capacity=15;
    unsigned int slot=(offer.item-0x3000)/4;
    af_holiday_profiles[slot][7]=0;
    assert(!af_v3_holiday_commit(af_holiday_reward_data,370,&npc.world.items,&offer));
    af_holiday_profiles[slot][7]=1;
    af_holiday_active=af_holiday_players[1];
    assert(!af_v3_holiday_commit(af_holiday_reward_data,370,&npc.world.items,&offer));
    unsigned int gender;
    assert(!af_holiday_world_bind(&npc,(AFDiaryDates){0},&gender));
    player(0);assert(!gives && !af_v3_reward_flag(0,0,1,0));
    /* Visitors can hear the official visitor conversation, never write a resident. */
    reset(4);bind();AFHolidayAction action;
    assert(af_holiday_talk_prepare(&npc.actor.talk,&npc.world,1,npc.world.today,0,0,0,&action)>0);
    AFDiary before=diary;
    assert(af_holiday_talk_start(&npc.actor.talk,&npc.world,&action)>0);
    assert(!memcmp(&before,&diary,sizeof(diary)) && !save_queries);
    assert(npc.world.free_slots(&npc)==-1 && npc.world.items.claimed(&npc,1)==-1);
    player(0);assert(!af_holiday_world_bind(&npc,(AFDiaryDates){0},&gender));
    reset(0);bind();date(2,30);
    assert(!af_holiday_world_bind(&npc,(AFDiaryDates){0},&gender));date(1,1);
    assert(!af_holiday_world_bind(&npc,(AFDiaryDates){0,2,30},&gender));
    assert(af_holiday_world_resources(&npc));
    assert(!af_holiday_npc_resources(&npc));npc.constructed=1;
    *(unsigned int *)((unsigned char *)&npc+0x930)=281;
    assert(af_holiday_npc_resources(&npc));registry.flags=0;
    assert(!af_holiday_npc_resources(&npc));
    printf("All 65 candidates, %u handovers, four-player receipts, visitors, full/stale inventory, and resource gates pass.\n",handovers);
    return 0;
}
