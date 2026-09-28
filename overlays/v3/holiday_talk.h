#ifndef AF_V3_HOLIDAY_TALK_H
#define AF_V3_HOLIDAY_TALK_H
#include "diary.h"
#include "holiday_rewards.h"

/* Shared Ev_Soncho2 conversation, not a replacement native actor. All message
 * numbers are donor IDs; the caller must bind the official message resources. */
enum {
    AF_HOLIDAY_BEFORE_GIVE=0, AF_HOLIDAY_GIVE=1, AF_HOLIDAY_VISITOR=2,
    AF_HOLIDAY_LIGHTHOUSE=3, AF_HOLIDAY_CLAIMED=4, AF_HOLIDAY_WAIT=5,
    AF_HOLIDAY_MESSAGE=1, AF_HOLIDAY_CONTINUE=2, AF_HOLIDAY_BEGIN=4,
    AF_HOLIDAY_ITEM_NAME=8, AF_HOLIDAY_EVENT_NAME=16,
    AF_HOLIDAY_LIGHTHOUSE_DATES=32, AF_HOLIDAY_HANDOVER=64,
    AF_HOLIDAY_END=128
};
typedef struct {
    AFDiary *diary;
    AFDiaryDates dates;
    AFDiaryDate today;
    unsigned int player; /* 4 is the donor's visiting-player case. */
    const unsigned char *rewards;
    unsigned int reward_bytes;
    struct AfHolidayOps items;
    void *context;
    int (*free_slots)(void *);
    int (*lighthouse_after)(void *);
    void (*lighthouse_start)(void *);
} AFHolidayWorld;
typedef struct {
    unsigned int effects,message,item,event;
    AFDiaryDate lighthouse_dates[2];
} AFHolidayAction;
typedef struct {
    AFDiaryDate date;
    unsigned int event,player,phase,prepared,active;
    struct AfHolidayOffer offer;
} AFHolidayTalk;

/* Zero-initialize the actor's transient state. The actor chooses its reward
 * variant once, then supplies the same variant when preparing each conversation.
 * variant is the checked ordinal from holiday_count(); repeat is RNG(3).
 * Preparation does not mark attendance, award an item, or change a trophy.
 * MESSAGE on preparation also requires the donor's turn=true and camera=3.
 * END returns control to the actor's current think state and restores its
 * saved melody instrument, exactly as the native actor transport must implement. */
int af_holiday_talk_prepare(AFHolidayTalk *,const AFHolidayWorld *,unsigned int event,
    AFDiaryDate actor_date,unsigned int gender,unsigned int variant,unsigned int repeat,
    AFHolidayAction *);
/* Call at the actual Ev_Soncho2 talk-init, not request/schedule/actor presence. */
int af_holiday_talk_start(AFHolidayTalk *,const AFHolidayWorld *,AFHolidayAction *);
/* Signals correspond to MainNormalContinue, NPC0 order value 1 == 2, and
 * CAN_ACTOR_TALK. No elapsed timer is used as a substitute for delivery. */
int af_holiday_talk_step(AFHolidayTalk *,const AFHolidayWorld *,int normal_continue,
    int delivered,int can_actor_talk,AFHolidayAction *);
/* The other donor attendance caller is Taisou_Npc0 talk-init. Its caller must
 * check Tortimer's identity; ordinary exercise villagers/Copper return unchanged.
 * This does not implement or replace the exercise-card conversation. */
int af_holiday_exercise_attend(const AFHolidayWorld *,int is_tortimer,unsigned int donor_event);
#endif
