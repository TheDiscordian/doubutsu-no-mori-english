#ifndef AF_V3_HOLIDAY_MOTION_H
#define AF_V3_HOLIDAY_MOTION_H
#include "holiday_npc.h"
#include "npc_registry.h"
typedef struct {float x,y,z;} AFHolidayPosition;
typedef struct {
    unsigned int arrays[4];
    short unused,duration;
    float start,end;
    unsigned int mode;
    float morph;
    unsigned int eye;
    short eye_type,eye_stop;
    unsigned int mouth;
    short mouth_type,mouth_stop,effect_frame,effect_type;
    unsigned int effect,sound;
} AFHolidayCane;
extern const AFHolidayCane af_holiday_cane;
_Static_assert(sizeof(AFHolidayCane)==64,"Complete NPC motion control record");

void af_holiday_motion_animation(void *,int,int);
void af_holiday_motion_decide(void *);
void af_holiday_motion_wander_init(void *,void *);
int af_holiday_motion_bind(AFHolidayNpc *);
int af_holiday_motion_resources(AFHolidayNpc *);

/* Native calls are separate from the controller so host checks exercise the
 * actual field offsets, branch ordering, and arguments, not a second port. */
void af_holiday_animation_original(void *,int,int);
void af_holiday_keyframe_init(void *,void *,const void *,float,float,float,float,float,int,void *);
void af_holiday_wander_original(void *);
void af_holiday_wander_init_original(void *,void *);
int af_holiday_fatigue(void *);
int af_holiday_mood(void *);
int af_holiday_move_next(unsigned short *,void *);
int af_holiday_ones_way(void *,unsigned short *);
int af_holiday_range(void *,void *,AFHolidayPosition,unsigned char);
int af_holiday_request_native(void *,unsigned char,unsigned char,unsigned char,unsigned short *);
void af_holiday_unit(int *,int *,AFHolidayPosition);
void af_holiday_block(int *,int *,AFHolidayPosition);
float af_holiday_random_native(void);
void af_holiday_schedule_native(void *,void *,unsigned char);
void af_holiday_sound_native(unsigned int,unsigned int,const void *);
#endif
