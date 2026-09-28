#ifndef AF_V3_HOLIDAY_FISHING_LIVE_H
#define AF_V3_HOLIDAY_FISHING_LIVE_H
#include "holiday_fishing.h"
typedef struct {
    int size;AFHFPerson person;short position[2];AFHFB talk,flag;
} AFHFLiveEvent;
typedef struct {
    AFHolidayFish records;AFHFLiveEvent event;AFHFPerson initial_person;
    AFHFB *native_event,*wire;unsigned int active,failed;
} AFHFLive;
extern AFHFLive af_hf_live;
extern AFHFPerson af_hf_controller_person;
extern AFHFTime af_hf_controller_clock;
extern const AFHFB af_fishing_aliases[6368];
extern const AFHFB *af_fishing_resolve(const AFHFB *,const AFHFB *,int);
extern const AFHFTime af_hf_native_clock;
extern const AFHFB *af_hf_native_player;
extern const AFHFB af_hf_native_players[4][0xBD0];
extern const AFHFB af_hf_native_animals[15][0x528];
extern float af_hf_native_random(void);
extern int af_hf_native_event_npc(AFHFH *);
extern int af_hf_native_name(AFHFB *,unsigned int,unsigned int);
extern AFHFB *af_hf_native_event_area(int,int);
extern AFHFB *af_v3_fishing_data(void);
extern void *af_hf_native_window(void);
extern void af_hf_native_string(void *,int,const AFHFB *,int);
extern const unsigned short af_hf_message_map[][2];
extern const unsigned char af_hf_unit_text[2][16];
extern const unsigned int af_hf_message_count;
int af_hf_live_enter(void);
int af_hf_records_enter(void);
void af_hf_live_leave(void);
AFHFLiveEvent *af_hf_live_event(int,int);
int af_hf_live_size(int),af_hf_live_npc_size(int),af_hf_live_event_npc(AFHFH *);
void af_hf_live_name(AFHFB *,AFHFH),af_hf_live_random_name(AFHFB *);
void af_hf_live_record(const AFHFPerson *,int);
int af_hf_live_message(int),af_hf_live_number(AFHFB *,int,int);
void af_hf_live_topname(void);
#endif
