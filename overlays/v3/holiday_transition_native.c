/* Actual N64 geometry functions; source identities are resolved by the graph
 * reader before a structure reaches the native 5xxx structure namespace. */
#include "holiday_transition.h"
#include "holiday_native.h"
extern int af_holiday_transition_grid(int *,int *,int *,int *,AFHolidayPosition);
extern void af_holiday_transition_position(AFHolidayPosition *,int,int,int,int);
extern int af_holiday_transition_origin(float *,float *,int,int);
extern int af_holiday_transition_area(int,int,unsigned short,int,int);
extern int af_holiday_transition_landmark(int *,int *,unsigned int);
extern int af_holiday_transition_police(int,int,int,int);
extern int af_holiday_transition_space(int,int,int,int);
extern int af_holiday_transition_gate(int *,int *,int,int,int,int);
static void grid(void *c,int *bx,int *bz,int *ux,int *uz,AFHolidayPosition p) {
    (void)c;af_holiday_transition_grid(bx,bz,ux,uz,p);
}
static void position(void *c,AFHolidayPosition *p,int bx,int bz,int ux,int uz) {
    (void)c;af_holiday_transition_position(p,bx,bz,ux,uz);
}
static void origin(void *c,float *x,float *z,int bx,int bz) {
    (void)c;af_holiday_transition_origin(x,z,bx,bz);
}
static int area(void *c,int x,int z,unsigned short name,int ux,int uz) {
    (void)c;return af_holiday_transition_area(x,z,name,ux,uz);
}
static int landmark(void *c,int *x,int *z,unsigned int kind) {
    (void)c;return af_holiday_transition_landmark(x,z,kind);
}
static int police(void *c,int bx,int bz,int ux,int uz) {
    (void)c;return af_holiday_transition_police(bx,bz,ux,uz);
}
static int space(void *c,int bx,int bz,int ux,int uz) {
    (void)c;return af_holiday_transition_space(bx,bz,ux,uz);
}
static int gate(void *c,int *x,int *z,int bx,int bz,int ux,int uz) {
    (void)c;return af_holiday_transition_gate(x,z,bx,bz,ux,uz);
}
int af_holiday_transition_native_geometry(AFHolidayTransitionOps *ops) {
    if(!ops)return 0;
    ops->structure=area;ops->landmark=landmark;ops->grid=grid;ops->position=position;
    ops->block_origin=origin;ops->police=police;ops->npc_space=space;ops->near_gate=gate;
    return 1;
}

extern void *af_holiday_native_game;
extern unsigned char af_holiday_transition_common[];
extern const int af_holiday_transition_scene;
extern void *af_holiday_transition_player(void *);
extern int af_holiday_transition_demo_busy(void);
extern int af_holiday_transition_player_ok(void);
extern int af_holiday_transition_correct(void);
extern int af_holiday_transition_goto(void *,const AFHolidayDoor *,int);
extern void af_holiday_transition_warp(void);
extern void af_holiday_transition_bgm(void);
typedef struct {
    unsigned char *game;
    int *manager;
    unsigned int native;
    AFHolidayTransition *view;
    const AFHolidayTransitionServices *services;
} Scene;
static int status(void *c,unsigned int donor,unsigned int mask) {
    Scene *n=c;return n->services->status(n->services->context,donor,mask);
}
static int identity(void *c,unsigned int source) {
    Scene *n=c;return n->services->resolve(n->services->context,source);
}
static int go(void *c,AFHolidayTransition *s,const AFHolidayDoor *door,int flags) {
    Scene *n=c;const AFHolidayTransitionServices *o=n->services;
    int type=s->common.start_demo_request.type;
    if(type==13)type=12;
    else if(type==14) {
        type=o->alternate_demo(o->context);
        if(type<14)type=-1; /* All original native types have other meanings. */
    }
    else type=-1;
    if(type<0) {s->failed=1;return 0;}
    /* The native request is visible to goto, including a rejected goto. The
     * source Groundhog fallback also changes its common area before goto. */
    o->commit(o->context,s,AF_HT_BEFORE_SCENE);
    *(int *)(af_holiday_transition_common+0x780)=type;
    return af_holiday_transition_goto(n->game,door,flags);
}
static void climate(void *c,int value) {
    Scene *n=c;n->services->climate(n->services->context,value);
}
static void tempo(void *c) {
    Scene *n=c;AFHolidayTransition *s=n->view;unsigned char *common=af_holiday_transition_common;
    /* These writes precede rhythm capture and warp, as in the complete donor
     * function. The source event identity is translated only at this boundary. */
    n->manager[0x244/4]=s->skip_event_at_wade;
    __builtin_memcpy(common+0x78C,&s->common.event_door_data,sizeof(AFHolidayDoor));
    *(short *)(common+0x7E2)=(short)n->native;
    *(short *)(common+0x7E4)=(short)s->common.event_title_flags;
    n->game[0x1EE1]=(unsigned char)s->play.fb_wipe_type;
    n->game[0x1EE0]=(unsigned char)s->play.fb_fade_type;
    common[0x14B]=(unsigned char)s->common.transition.wipe_type;
    n->services->commit(n->services->context,s,AF_HT_RETURN_STATE);
    n->services->tempo(n->services->context);
}
static void warp(void *c,AFHolidayTransition *s) {(void)c;(void)s;af_holiday_transition_warp();}
static void bgm(void *c) {(void)c;af_holiday_transition_bgm();}
static int correct(void *c) {(void)c;return af_holiday_transition_correct();}
int af_holiday_transition_native_fade(void *context,void *manager,unsigned int donor,
        unsigned int native,unsigned int title,unsigned int landmark_kind) {
    const AFHolidayTransitionServices *o=context;
    if(!manager || !o || !o->maps || !o->status || !o->resolve || !o->read || !o->commit ||
       !o->alternate_demo || !o->climate || !o->tempo || !af_holiday_native_game ||
       donor>=128 || native<AF_HN_FIRST || native>=AF_HN_END || title>32767 ||
       af_holiday_native_type(donor)!=(int)native)return -1;
    unsigned char *player=af_holiday_transition_player(af_holiday_native_game);
    if(!player)return -1;
    AFHolidayTransition view={0};Scene n={af_holiday_native_game,manager,native,&view,o};
    AFHolidayTransitionOps ops={.status=status,.resolve=identity,.go=go,.climate=climate,
        .tempo=tempo,.warp=warp,.bgm=bgm,.correct=correct};
    af_holiday_transition_native_geometry(&ops);
    view.context=&n;view.ops=&ops;view.maps=o->maps;view.map_bytes=o->map_bytes;
    const int *w=manager;const unsigned char *common=af_holiday_transition_common;
    view.pool_block=(AFHolidayBlock){w[0x214/4],w[0x218/4]};
    view.station_block=(AFHolidayBlock){w[0x220/4],w[0x224/4]};
    view.shrine_block=(AFHolidayBlock){w[0x22C/4],w[0x230/4]};
    view.player_home_block=(AFHolidayBlock){w[0x238/4],w[0x23C/4]};
    view.skip_event_at_wade=w[0x244/4];
    __builtin_memcpy(&view.player.world.position,player+0x28,sizeof(AFHolidayPosition));
    __builtin_memcpy(&view.player.world.angle,player+0x34,sizeof(AFHolidayShortPosition));
    __builtin_memcpy(&view.common.door_data,common+0x754,sizeof(AFHolidayDoor));
    __builtin_memcpy(&view.common.event_door_data,common+0x78C,sizeof(AFHolidayDoor));
    view.common.reset_flag=common[0xA68];
    view.scene_no=af_holiday_transition_scene;
    view.demo_busy=af_holiday_transition_demo_busy();
    view.player_ok=af_holiday_transition_player_ok();
    /* read supplies actual imported common state, present/room gates, pool
     * variant, and current acre. It may reject; it must not manufacture state. */
    if(o->read(o->context,&view)!=1)return -1;
    return af_holiday_transition_run(&view,donor,title,landmark_kind);
}
