#ifndef AF_V3_HOLIDAY_TRANSITION_H
#define AF_V3_HOLIDAY_TRANSITION_H
#include "holiday_reserved.h"
enum {AF_HT_SOURCE_STRUCTURE=5,AF_HT_ORIGINAL_LAYOUT=128};
typedef struct {float x,y,z;} AFHolidayPosition;
typedef struct {short x,y,z;} AFHolidayShortPosition;
typedef struct {
    int next_scene_id;
    unsigned char exit_orientation,exit_type;
    unsigned short extra_data;
    AFHolidayShortPosition exit_position;
    unsigned short door_actor_name;
    unsigned char wipe_type,padding[3];
} AFHolidayDoor;
_Static_assert(sizeof(AFHolidayDoor)==20,"Native and donor door wire fields");
struct AFHolidayTransition;
typedef struct {
    int (*status)(void *,unsigned int donor,unsigned int mask);
    int (*resolve)(void *,unsigned int source_name);
    int (*structure)(void *,int,int,unsigned short,int,int);
    int (*landmark)(void *,int *,int *,unsigned int);
    void (*grid)(void *,int *,int *,int *,int *,AFHolidayPosition);
    void (*position)(void *,AFHolidayPosition *,int,int,int,int);
    void (*block_origin)(void *,float *,float *,int,int);
    int (*police)(void *,int,int,int,int);
    int (*npc_space)(void *,int,int,int,int);
    int (*near_gate)(void *,int *,int *,int,int,int,int);
    /* The caller commits the requested demo type BEFORE native goto, even on
     * rejection, and commits completed door/fade state before warp/BGM. */
    int (*go)(void *,struct AFHolidayTransition *,const AFHolidayDoor *,int);
    void (*climate)(void *,int);
    void (*tempo)(void *);
    void (*warp)(void *,struct AFHolidayTransition *);
    void (*bgm)(void *);
    int (*correct)(void *);
    /* Priority position of the original N64 layout, -1 for none, -2 for
     * invalid state. Its names and collision remain in the native namespace. */
    int (*original_rank)(void *);
    int (*original_collision)(void *,int,int);
} AFHolidayTransitionOps;
/* A normalized, explicitly populated view, never a cast of either game's
 * differently laid-out ACTOR/GAME_PLAY/CommonData structures. */
typedef struct AFHolidayTransition {
    void *context;
    const AFHolidayTransitionOps *ops;
    const unsigned char *maps;
    unsigned int map_bytes,pool_variant;
    AFHolidayBlock pool_block,station_block,shrine_block,player_home_block;
    int skip_event_at_wade;
    struct {
        struct {int block_x,block_z;} block_table;
        int fb_wipe_type,fb_fade_type;
    } play;
    struct {struct {AFHolidayPosition position;AFHolidayShortPosition angle;} world;} player;
    struct {
        int reset_flag,my_room_message_control_flags;
        struct {int type;} start_demo_request;
        AFHolidayDoor door_data,event_door_data;
        int event_id,event_title_flags,event_title_fade_in_progress;
        struct {int wipe_type;} transition;
    } common;
    int scene_no,demo_busy,player_ok,present_busy;
    struct {int fading_title;} groundhog;
    struct {int _00;} groundhog_save;
    int groundhog_present,groundhog_save_present;
    int failed;
} AFHolidayTransition;
/* Shared ACTIVE layout order, including an active null layout masking later
 * entries. Source structure IDs must resolve before native collision calls. */
int af_holiday_transition_map(AFHolidayTransition *);
int af_holiday_transition_collision(AFHolidayTransition *,int,int);
int af_holiday_transition_escape(AFHolidayTransition *,AFHolidayShortPosition *,
    AFHolidayPosition *,unsigned int landmark,unsigned int donor);
int af_holiday_transition_run(AFHolidayTransition *,unsigned int donor,
    unsigned int title,unsigned int landmark);
/* Primitive-backed layout access used by the generated complete source code. */
int af_holiday_transition_index(AFHolidayTransition *,int donor);
int af_holiday_transition_count(AFHolidayTransition *,int index);
int af_holiday_transition_unit(AFHolidayTransition *,unsigned short *,int *,int *,int donor,int index);
int af_holiday_transition_structure(AFHolidayTransition *,int,int,unsigned short,int,int);
int af_holiday_transition_ready(AFHolidayTransition *);
int af_holiday_transition_original(AFHolidayTransition *,int,int);
/* Fill all eight geometry operations from checked native functions, retaining
 * the caller's actual identity/status and transition-lifecycle operations. */
int af_holiday_transition_native_geometry(AFHolidayTransitionOps *);
/* Imported state and services absent from the original N64 fade. Every
 * applicable provider is mandatory; read must verify that the complete service set is
 * ready. No zero-filled stand-in for present/room-message/holiday state. */
enum {AF_HT_BEFORE_SCENE,AF_HT_RETURN_STATE};
typedef struct {
    void *context;
    const unsigned char *maps;
    unsigned int map_bytes;
    int (*status)(void *,unsigned int,unsigned int);
    int (*resolve)(void *,unsigned int);
    int (*read)(void *,AFHolidayTransition *);
    void (*commit)(void *,const AFHolidayTransition *,unsigned int phase);
    /* Source EVENTMSG2 has no original N64 counterpart. Return the installed
     * alternate demo identity, or -1; never alias it to native demo 13.
     * Required only when the source requests EVENTMSG2 (ceremony owner 7). */
    int (*alternate_demo)(void *);
    void (*climate)(void *,int);
    void (*tempo)(void *);
    int (*original_rank)(void *);
    int (*original_collision)(void *,int,int);
} AFHolidayTransitionServices;
/* Signature matches AFHolidayDedicatedServices.fade. Reads the actual N64
 * player/manager/common state and commits native scene/return state in order. */
int af_holiday_transition_native_fade(void *,void *manager,unsigned int donor,
    unsigned int native,unsigned int title,unsigned int landmark);
/* Complete native state/identity binding for scheduled owners. */
int af_holiday_transition_bind(AFHolidayTransitionServices *);
int af_holiday_transition_live_fade(void *,void *,unsigned int,unsigned int,unsigned int,unsigned int);
#endif
