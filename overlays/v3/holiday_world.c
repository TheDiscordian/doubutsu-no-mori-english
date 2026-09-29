/* All holiday reward identities use the same installed carried/profile records.
 * No source ID is cast into the native inventory, and no trophy changes merely
 * because an event is scheduled or a handover animation begins. */
#include "holiday_world.h"
typedef unsigned char u8;
typedef unsigned int u32;
static u32 half(const u8 *p) {return (u32)p[0]*256u+p[1];}
static u32 word(const u8 *p) {return (half(p)<<16)|half(p+2);}

static int identity(u32 player) {
    if(player>4 || af_holiday_player!=player)return 0;
    const u8 *expected=player<4?af_holiday_players[player]:af_holiday_visitor;
    return af_holiday_active==expected && expected[0x10]<=1;
}
static int resident(AFHolidayNpc *a) {
    return a && !a->failed && a->world.player<4 && identity(a->world.player);
}
static int map_valid(void) {
    const u8 *p=af_holiday_destination_data;
    u32 count=half(p+6);
    if(word(p)!=0x41464857u || half(p+4)!=1 || count<65 || count>128 ||
            half(p+8)!=8 || half(p+10)!=16+count*8 || word(p+12))return 0;
    u32 previous=0;
    for(u32 i=0;i<count;++i) {
        const u8 *r=p+16+i*8;u32 source=half(r),item=half(r+2),index=half(r+4),kind=half(r+6);
        if(source<=previous || index<1024 || index>=2048 || kind>1)return 0;
        if(kind) {
            if(source<0x2B00 || source>0x2B0F || item!=source+16 || index!=1087+source-0x2B00)return 0;
        } else if(item!=0x3000+(index-1024)*4)return 0;
        previous=source;
    }
    return 1;
}
u32 af_holiday_world_resolve(void *context,u32 donor) {
    (void)context;
    if(donor>65535 || !map_valid())return 0;
    u32 low=0,high=half(af_holiday_destination_data+6);
    while(low<high) {
        u32 mid=low+(high-low)/2;const u8 *r=af_holiday_destination_data+16+mid*8;
        u32 source=half(r);
        if(donor<source)high=mid;
        else if(donor>source)low=mid+1;
        else {
            u32 item=half(r+2),index=half(r+4),slot=index-1024,cover=0x3000+slot*4;
            const u8 *profile=af_holiday_profiles[slot],*meta=af_holiday_metadata[slot];
            if(half(profile)!=index || half(profile+2)!=cover || word(profile+4)!=1 ||
                    half(meta)!=index || half(meta+2)!=cover || meta[7]!=1)return 0;
            /* A carried diary and its cover share one selection, but giving
             * the cover would bypass the actual diary's inventory/use path. */
            if(half(r+6) && half(meta+28)!=item)return 0;
            return item;
        }
    }
    return 0;
}
static int claimed(void *context,u32 event) {
    AFHolidayNpc *a=context;
    if(!resident(a) || event>=28)return -1;
    return af_v3_reward_flag(a->world.player,0,event,0);
}
static int free_slots(void *context) {
    AFHolidayNpc *a=context;
    if(!resident(a))return -1;
    return af_holiday_native_free(af_holiday_active,0,0);
}
static int give(void *context,u32 item) {
    AFHolidayNpc *a=context;
    if(!resident(a) || !item || item>65535)return 0;
    /* The shared transaction validates the exact donor mapping before this
     * call. Native insertion also records collection through the installed
     * item reader. Do not duplicate that write or alter pocket conditions. */
    return af_holiday_native_give((void *)af_holiday_active,(unsigned short)item,0);
}
static void mark(void *context,u32 event) {
    AFHolidayNpc *a=context;
    if(!resident(a) || event>=28) {if(a)a->failed=1;return;}
    if(af_v3_reward_flag(a->world.player,0,event,1)!=1)a->failed=1;
}
int af_holiday_world_bind(AFHolidayNpc *a,AFDiaryDates dates,u32 *gender) {
    if(!a || !gender || a->failed || !identity(af_holiday_player) || !map_valid() ||
            !af_v3_holiday_valid(af_holiday_reward_data,370))return 0;
    AFDiaryDate now={(u32)af_holiday_rtc[6]*256+af_holiday_rtc[7],af_holiday_rtc[5],af_holiday_rtc[3]};
    if(!now.day || now.day>af_diary_days(now.year,now.month) || dates.town_day>31 ||
            ((dates.harvest_month || dates.harvest_day) &&
             (!dates.harvest_day || dates.harvest_day>af_diary_days(now.year,dates.harvest_month))))return 0;
    AFDiary *diary=af_v3_diary_data();
    if(!af_diary_valid(diary))return 0;
    AFHolidayWorld w={.diary=diary,.dates=dates,.today=now,.player=af_holiday_player,
        .rewards=af_holiday_reward_data,.reward_bytes=370,
        .items={a,af_holiday_world_resolve,claimed,give,mark},.context=a,.free_slots=free_slots};
    /* A conversation belongs to the player who started it. Loading a different
     * slot or changing the active pointer cannot transfer its pending offer. */
    if(a->actor.talk.active && a->actor.talk.player!=w.player)return 0;
    *gender=af_holiday_active[0x10];a->world=w;
    a->ops.variant=af_holiday_world_variant;return 1;
}
int af_holiday_world_variant(void *context,u32 event,u32 gender,u32 *out) {
    AFHolidayNpc *a=context;
    if(!a || a->failed || !out || gender>1 || !identity(a->world.player))return 0;
    if(event==101 || event==102) {*out=0;return 1;}
    int count=af_v3_holiday_count(a->world.rewards,a->world.reward_bytes,event,gender,&a->world.items);
    if(count<0)return 0;
    /* Disabling every gift does not disable the festival or its diary entry.
     * The conversation selects an official no-gift greeting in this case. */
    if(!count) {*out=0;return 1;}
    if(!a->ops.random)return 0;
    /* Fixed/gender-selected rewards consume no RNG in the original. */
    const u8 *row=a->world.rewards+16+event*8;
    u32 selected=row[4]==1?a->ops.random(a,(u32)count):0;
    if(selected>=(u32)count)return 0;
    *out=selected;return 1;
}
int af_holiday_world_resources(AFHolidayNpc *a) {
    const AFNpcExtra *r=af_v3_npc_extra_owned(a);
    if(!r || r->flags!=3 || r->actor_bytes!=0xA34 || !r->draw || !r->stream ||
            r->stream->name!=r->name || r->stream->texture_bytes!=4128)return 0;
    /* Both source appearances use the same complete Ev_Soncho2 controller.
     * Keep their separately reserved model and full voice identities. */
    if(!((r->name==0xD090 && r->profile==0xCC && r->voice==281 &&
            r->model_bank==448 && r->texture_bank==449) ||
         (r->name==0xD092 && r->profile==0xE2 && r->voice==231 &&
            r->model_bank==452 && r->texture_bank==453)))return 0;
    return !a->failed;
}
int af_holiday_npc_resources(AFHolidayNpc *a) {
    if(!af_holiday_world_resources(a) || !a->constructed)return 0;
    /* The native ctor's already-installed full-ID voice reader owns this field.
     * A mismatch means the constructor/resource path is wrong, not permission
     * to patch around an unverified actor layout. */
    return *(const u32 *)((const u8 *)a+0x930)==af_v3_npc_extra_owned(a)->voice;
}
