#ifndef AF_V3_HOLIDAY_ACTOR_H
#define AF_V3_HOLIDAY_ACTOR_H
#include "holiday_talk.h"

/* Ev_Soncho2's complete transient controller. These numbers describe donor
 * actions, not native animation/schedule indices or memory offsets. */
enum {
    AF_HACT_WAIT=0, AF_HACT_WALK=1, AF_HACT_RUN=2,
    AF_HACT_TURN=3, AF_HACT_TURN2=4, AF_HACT_POINT=3,
    AF_HACT_NO_EVENT=255, AF_HACT_THINKS=15
};
typedef struct {
    AFDiaryDate date;
    AFHolidayTalk talk;
    unsigned int event,variant,gender,ready,deleted;
    unsigned char think,return_think,talk_enabled,suppress_request;
    short timer,center_x,center_z,goal_x,goal_z;
} AFHolidayActor;
typedef struct {
    float x,z,destination_x,destination_z;
    unsigned int action,step,clapping;
} AFHolidayMotion;
typedef struct {
    void *context;
    /* Observations are taken at their actual source call sites, not cached
     * across a frame or conversation. event() returns a DONOR event identity. */
    unsigned int (*event)(void *);
    unsigned int (*field_event)(void *); /* race, ball toss, tug, exercise */
    int (*variant)(void *,unsigned int event,unsigned int gender,unsigned int *);
    int (*shrine)(void *,short position[3]);
    int (*runner)(void *,short position[2]); /* false unless race is active */
    void (*motion)(void *,AFHolidayMotion *);
    int (*request)(void *,unsigned int priority,unsigned int action,
        unsigned int type,short x,short z);
    void (*force_action)(void *,unsigned int);
    void (*weight)(void *,unsigned int);
    void (*hide_request)(void *,int);
    void (*clear_interrupts)(void *);
    void (*demo_flags)(void *,unsigned int value,int replace);
    /* This is the donor WALK_WANDER mode, not ordinary native wandering. */
    void (*walk_wander)(void *);
    void (*destination)(void *,float x,float z);
    void (*repeat_animation)(void *,int clap);
    void (*clap_sound)(void *);
    void (*remove)(void *);
    unsigned int (*random)(void *,unsigned int bound);
    void (*talk_request)(void *,int enabled);
    void (*request_demo)(void *); /* order 7, prepare on demo acceptance */
    void (*transport)(void *,const AFHolidayAction *);
    void (*restore_melody)(void *);
} AFHolidayActorOps;

/* Call construction after successful native birth/ctor. Calendar refresh is
 * not attendance. Actor memory and all calendar pages remain caller-owned. */
int af_holiday_actor_construct(AFHolidayActor *,const AFHolidayWorld *,unsigned int gender);
int af_holiday_actor_think_init(AFHolidayActor *,const AFHolidayActorOps *);
int af_holiday_actor_set_think(AFHolidayActor *,const AFHolidayActorOps *,unsigned int);
int af_holiday_actor_think(AFHolidayActor *,const AFHolidayWorld *,const AFHolidayActorOps *);
/* Elapsed 60 Hz ticks: native actors still move once per world update. */
int af_holiday_actor_think_elapsed(AFHolidayActor *,const AFHolidayWorld *,const AFHolidayActorOps *,unsigned int);
int af_holiday_actor_request(AFHolidayActor *,const AFHolidayActorOps *);
int af_holiday_actor_prepare(AFHolidayActor *,const AFHolidayWorld *,const AFHolidayActorOps *);
int af_holiday_actor_start(AFHolidayActor *,const AFHolidayWorld *,const AFHolidayActorOps *);
/* Return one only when the real demo has ended and behaviour is restored. */
int af_holiday_actor_talk(AFHolidayActor *,const AFHolidayWorld *,const AFHolidayActorOps *,
    int normal_continue,int delivered,int can_actor_talk);
#endif
