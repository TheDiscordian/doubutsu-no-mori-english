/* Shared additional event announcement/speech lifecycle. Native requests keep
 * their original identity, admission, callbacks, and message implementation. */
#include "holiday_demo.h"
typedef unsigned int u32;
#ifdef __mips__
_Static_assert(sizeof(AFHDRequest)==16,"Native demo request");
_Static_assert(__builtin_offsetof(AFHDNativeDemo,state)==0xDC,"Native demo state");
_Static_assert(__builtin_offsetof(AFHDNativeDemo,current)==0xE0,"Native current request");
_Static_assert(__builtin_offsetof(AFHDNativeDemo,requests)==0xF0,"Native request directory");
_Static_assert(__builtin_offsetof(AFHDNativeDemo,request_count)==0x2F0,"Native request count");
_Static_assert(__builtin_offsetof(AFHDNativeDemo,data)==0x300,"Native message union");
_Static_assert(sizeof(AFHDNativeDemo)==0x328,"Native demo allocation");
_Static_assert(sizeof(AFHDDemoState)<=64,"Imported demo state reservation");
#endif
static int talk(int type) {return type==7 || type==8 || type==9 || type==AF_HD_SPEECH;}
/* Source speech precedes outdoor/event modes. Added destination numbers must
 * not silently change priority relative to original native requests. */
static int priority(int type) {
    if(type==AF_HD_SPEECH)return 10;
    if(type==AF_HD_EVENTMSG2)return 14;
    return type>=10?type+(type==13?2:1):type;
}
static int candidate(void) {
    AFHDNativeDemo *d=af_hd_native_demo;float weight=0.0f;int selected=-1;
    if(d->request_count<0 || d->request_count>32)return -1;
    for(int i=0;i<d->request_count;i++) {
        AFHDRequest *r=d->requests+i;int type=r->type;
        if(type<0 || type>=AF_HD_TYPES)continue;
        int title=af_hd_title_demo();
        if(title && type!=1 && !(title==-9 && type==8 && r->actor && *(short *)r->actor==0x99))continue;
        if(!af_hd_state.saved.type && priority(type)<priority(d->priority))continue;
        if(type<14 && !af_hd_checks[type]())continue;
        if(type==7) {
            if(af_hd_trigger(0x8000) && r->weight>weight) {weight=r->weight;selected=i;}
        } else {selected=i;break;}
    }
    return selected;
}
static void speech_init(AFHDNativeDemo *d) {
    d->data.talk.message=d->data.talk.turn=d->data.talk.change_player=d->data.talk.return_wait=0;
    d->data.talk.name=d->data.talk.zoom=1;
    d->data.talk.colour[0]=235;d->data.talk.colour[1]=255;
    d->data.talk.colour[2]=235;d->data.talk.colour[3]=255;
    d->camera=12;d->speaker_able=1;d->listener_able=0;
    d->speaker=af_hd_player(af_hd_game);d->listener=d->current.actor;
}
static void alternate_init(AFHDNativeDemo *d) {
    __builtin_memcpy(&d->data.event.door,af_hd_common+0x78C,sizeof(AFHolidayDoor));
    d->camera=6;d->data.event.message_delay=0;d->data.event.scene_delay=30;
    af_hd_state.saved=d->current;
}
int af_holiday_demo_choose(void) {
    AFHDNativeDemo *d=af_hd_native_demo;int index=candidate();
    if(index<0)return index;
    d->current=d->requests[index];
    if(d->current.type==AF_HD_EVENTMSG2)alternate_init(d);
    else if(d->current.type==AF_HD_SPEECH)speech_init(d);
    else (void)af_hd_defaults[d->current.type]();
    if(d->current.proc)d->current.proc(d->current.actor);
    d->state=1;return index;
}
static void shrine_camera(void) {
    unsigned char *player=af_hd_player(af_hd_game);int x,z;
    if(!player || !af_hd_landmark(&x,&z,4))return;
    AFHolidayShortPosition angle;AFHolidayPosition position;float distance;
    af_hd_camera_angle(af_hd_game,&angle,&distance);
    af_hd_origin(&position.x,&position.z,x,z);position.x+=320.0f;position.z+=400.0f;
    __builtin_memcpy(&position.y,player+0x2C,4);
    af_hd_camera_simple(af_hd_game,&position,&angle,distance,0,6);
}
static void camera(int kind) {
    AFHDNativeDemo *d=af_hd_native_demo;
    if(kind==12 && d->current.type==AF_HD_SPEECH) {
        /* Native camera mode 10 is the same interpolation primitive. Keep
           its valid directory index and own the source INTER2 return flag. */
        AFHolidayPosition center,eye;unsigned char *game=af_hd_game;
        __builtin_memcpy(&center,game+0x1A6C,sizeof(center));
        __builtin_memcpy(&eye,game+0x1A60,sizeof(eye));
        center.x-=80.0f;eye.x-=80.0f;eye.z-=20.0f;
        if(af_hd_camera_inter(game,&center,&eye,&center,&eye,0.6f,0.3f,1,7,7))af_hd_state.speech_camera=1;
    } else if(kind==6 && (d->current.type==AF_HD_SPEECH || d->current.type==AF_HD_EVENTMSG2))shrine_camera();
    else (void)af_hd_camera(kind);
}
int af_holiday_demo_camera_reverse(void *p) {
    unsigned char *game=p;
    if(*(int *)(game+0x1AC0)==10)*(u32 *)(game+0x1B10)|=af_hd_state.speech_camera?4u:2u;
    return 1;
}
void af_holiday_demo_camera_counter(void *p) {
    unsigned char *game=p;u32 flags=*(u32 *)(game+0x1B10);
    int *count=(int *)(game+0x1B14),limit=*(int *)(game+0x1B18);
    if(flags&2) {
        if(*count<=0) {*count=0;af_hd_camera_normal(game,0,5);}else --*count;
    } else if((flags&4) && af_hd_state.speech_camera) {
        if(*count<=0) {*count=0;shrine_camera();af_hd_state.speech_camera=0;}else --*count;
    } else {
        if(*count>=limit)*count=limit;else ++*count;
    }
}
static int alternate_end(void) {
    if(af_hd_state.fading_title!=1)return 0;
    AFHolidayDoor *door=(AFHolidayDoor *)(af_hd_common+0x78C);
    if(!af_hd_goto(af_hd_game,door,0))return 0;
    unsigned char *game=af_hd_game;
    game[0x1EE1]=door->wipe_type;game[0x1EE0]=11;af_hd_common[0x14B]=door->wipe_type;
    af_hd_bgm_end();__builtin_memset(&af_hd_state.saved,0,sizeof(AFHDRequest));return 1;
}
void af_holiday_demo_run(void) {
    AFHDNativeDemo *d=af_hd_native_demo;int type=d->current.type;
    if(type<0 || type>=AF_HD_TYPES)return;
    if(d->state==1) {
        int ready;
        if(type==AF_HD_EVENTMSG2) {af_hd_title_flags=2;ready=1;}
        else ready=af_hd_starts[type==AF_HD_SPEECH?9:type]();
        if(ready) {camera(d->camera);d->state=2;}
    } else if(d->state==2) {
        int done=type==AF_HD_EVENTMSG2?alternate_end():af_hd_ends[type==AF_HD_SPEECH?9:type]();
        if(done)d->state=9;
    }
}
void af_holiday_demo_main(void) {
    AFHDNativeDemo *d=af_hd_native_demo;
    if(d->state==9) {
        unsigned char *player=af_hd_player(af_hd_game);
        if(player)*(u32 *)(player+4)&=~0x40000000u;
        if(d->current.actor)*(u32 *)((unsigned char *)d->current.actor+4)&=~0x40000000u;
        d->camera=1;camera(d->keep_camera && d->current.actor?d->keep_camera:d->camera);
        d->keep_camera=0;__builtin_memset(&d->current,0,sizeof(d->current));d->state=0;
    }
    if(af_hd_state.saved.type && af_hd_state.saved.type==d->current.type) {
        int index=candidate();
        if(index>=0 && d->requests[index].type==AF_HD_SPEECH)d->state=0;
    }
    if(!d->state)(void)af_holiday_demo_choose();
    if(d->state)af_holiday_demo_run();
    if(d->state==9 && af_hd_state.saved.type && af_hd_state.saved.type!=d->current.type) {
        d->current=af_hd_state.saved;d->state=2;camera(12);
    }
}
void af_holiday_demo_init(void) {
    AFHDNativeDemo *d=af_hd_native_demo;int initial=*(int *)(af_hd_common+0x780);
    __builtin_memset(&d->current,0,sizeof(d->current));
    __builtin_memset(&af_hd_state.saved,0,sizeof(af_hd_state.saved));
    af_hd_state.speech_camera=0;
    d->state=d->request_count=d->priority=d->keep_camera=0;d->camera=1;
    if(initial==12 || initial==AF_HD_EVENTMSG2) {
        (void)af_holiday_demo_request(initial,0,af_hd_emsg_colour);
        *(int *)(af_hd_common+0x780)=0;
    }
}
int af_holiday_demo_request(int type,void *actor,AFHDCallback proc) {
    AFHDNativeDemo *d=af_hd_native_demo;float weight=1.0f;
    if(type<0 || type>=AF_HD_TYPES || d->request_count<0 || d->request_count>=32 ||
       (type==AF_HD_SPEECH && !actor))return 0;
    if(priority(type)>=priority(d->priority)) {
        if(type==7) {weight=af_hd_weight(actor);if(weight<0.0f)return 0;}
        else if(type==8 && !af_hd_force_speak(af_hd_game,actor))return 0;
        d->priority=type;d->requests[d->request_count++]=(AFHDRequest){actor,type,proc,weight};
    }
    return 1;
}
int af_holiday_demo_busy(void) {
    int type=af_hd_demo_type();return type!=0 && type!=12 && type!=AF_HD_EVENTMSG2;
}
void *af_holiday_demo_talk_actor(void) {
    AFHDNativeDemo *d=af_hd_native_demo;return talk(d->current.type)?d->current.actor:0;
}
int af_holiday_demo_actors(void **speaker,void **listener) {
    AFHDNativeDemo *d=af_hd_native_demo;int active=talk(d->current.type);
    *speaker=active?d->speaker:0;*listener=active?d->listener:0;return active;
}
void af_holiday_demo_message(int value) {if(talk(af_hd_native_demo->current.type))af_hd_native_demo->data.talk.message=value;}
#define AF_HD_PROPERTY(name,value_type) \
void af_holiday_demo_set_##name(value_type value) {if(talk(af_hd_native_demo->current.type))af_hd_native_demo->data.talk.name=value;} \
int af_holiday_demo_get_##name(void) {return talk(af_hd_native_demo->current.type)?af_hd_native_demo->data.talk.name:0;}
AF_HD_PROPERTY(zoom,unsigned char)
AF_HD_PROPERTY(name,signed char)
AF_HD_PROPERTY(change_player,unsigned char)
AF_HD_PROPERTY(return_wait,unsigned char)
AF_HD_PROPERTY(turn,unsigned char)
#undef AF_HD_PROPERTY
void af_holiday_demo_colour(const unsigned char *colour) {
    AFHDNativeDemo *d=af_hd_native_demo;
    if(talk(d->current.type))__builtin_memcpy(d->data.talk.colour,colour,4);
    else if(d->current.type==12 || d->current.type==AF_HD_EVENTMSG2)__builtin_memcpy(d->data.event.colour,colour,4);
}
unsigned char *af_holiday_demo_colour_pointer(void) {
    AFHDNativeDemo *d=af_hd_native_demo;
    /* Keep original native event colour-pointer behaviour unchanged. */
    if(talk(d->current.type))return d->data.talk.colour;
    return d->current.type==AF_HD_EVENTMSG2?d->data.event.colour:0;
}
