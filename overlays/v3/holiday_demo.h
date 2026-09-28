#ifndef AF_V3_HOLIDAY_DEMO_H
#define AF_V3_HOLIDAY_DEMO_H
#include "holiday_transition.h"
/* Additive native identities. Original types 0..13 retain their meanings. */
enum {AF_HD_EVENTMSG2=14,AF_HD_SPEECH=15,AF_HD_TYPES=16};
typedef void (*AFHDCallback)(void *);
typedef struct {void *actor;int type;AFHDCallback proc;float weight;} AFHDRequest;
typedef struct {
    void *speaker,*listener;
    int speaker_able,listener_able;
    unsigned short orders[100];
    signed char destiny;unsigned char padding[3];
    int state;
    AFHDRequest current,requests[32];
    int request_count,priority,camera,keep_camera;
    union {
        struct {int message;unsigned char colour[4];int message_delay,scene_delay;AFHolidayDoor door;unsigned char unused[4];} event;
        struct {int message,turn,zoom,name,change_player,return_wait;unsigned char colour[4],mass;} talk;
    } data;
} AFHDNativeDemo;
typedef struct {AFHDRequest saved;int fading_title,speech_camera;} AFHDDemoState;
extern AFHDNativeDemo *af_hd_native_demo;
extern AFHDDemoState af_hd_state;
extern void *af_hd_game;
extern unsigned char af_hd_common[];
extern volatile short af_hd_title_flags;
extern int (*const af_hd_checks[14])(void),(*const af_hd_defaults[14])(void);
extern int (*const af_hd_starts[14])(void),(*const af_hd_ends[14])(void);
extern int af_hd_title_demo(void);
extern int af_hd_trigger(unsigned int);
extern float af_hd_weight(void *);
extern int af_hd_force_speak(void *,void *);
extern void *af_hd_player(void *);
extern int af_hd_camera(int);
extern int af_hd_demo_type(void);
extern void af_hd_emsg_colour(void *);
extern void af_hd_camera_angle(void *,AFHolidayShortPosition *,float *);
extern void af_hd_camera_simple(void *,const AFHolidayPosition *,const AFHolidayShortPosition *,float,int,int);
extern int af_hd_camera_inter(void *,const AFHolidayPosition *,const AFHolidayPosition *,
    const AFHolidayPosition *,const AFHolidayPosition *,float,float,unsigned int,int,int);
extern void af_hd_camera_normal(void *,int,int);
extern int af_hd_landmark(int *,int *,unsigned int);
extern void af_hd_origin(float *,float *,int,int);
extern int af_hd_goto(void *,const AFHolidayDoor *,int);
extern void af_hd_bgm_end(void);
int af_holiday_demo_choose(void);
void af_holiday_demo_init(void);
void af_holiday_demo_run(void);
void af_holiday_demo_main(void);
int af_holiday_demo_request(int,void *,AFHDCallback);
int af_holiday_demo_busy(void);
int af_holiday_demo_camera_reverse(void *);
void af_holiday_demo_camera_counter(void *);
void *af_holiday_demo_talk_actor(void);
int af_holiday_demo_actors(void **,void **);
void af_holiday_demo_message(int);
void af_holiday_demo_colour(const unsigned char *);
unsigned char *af_holiday_demo_colour_pointer(void);
#define AF_HD_PROPERTY(name,type) void af_holiday_demo_set_##name(type); int af_holiday_demo_get_##name(void)
AF_HD_PROPERTY(zoom,unsigned char);
AF_HD_PROPERTY(name,signed char);
AF_HD_PROPERTY(change_player,unsigned char);
AF_HD_PROPERTY(return_wait,unsigned char);
AF_HD_PROPERTY(turn,unsigned char);
#undef AF_HD_PROPERTY
#endif
