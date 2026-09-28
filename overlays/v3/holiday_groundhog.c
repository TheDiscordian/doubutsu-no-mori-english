/* Complete Groundhog controller sequence from the pinned GameCube controller.
 * Services are mandatory: missing actors/music/fades cannot become a successful
 * empty ceremony. No source profile or audio ID is passed directly to N64. */
#include "holiday_groundhog.h"
#include "holiday_demo.h"
#ifdef __mips__
_Static_assert(sizeof(AFHDDemoState)==24,"Groundhog clip pointer follows owned demo state");
_Static_assert(sizeof(AFHolidayGroundhog)<=80,"Bounded normalised controller state");
#endif
static int term(int seconds) {
    return seconds>=28800?5:seconds>=28740?4:seconds>=28500?3:
        seconds>=27900?2:seconds>=27000?1:0;
}
static int ready(const AFHolidayGroundhogOps *o) {
    return o && o->area && o->find && o->spawn && o->parent && o->attention &&
        o->fade && o->music && o->reverse_camera && o->death;
}
int af_holiday_groundhog_begin(AFHolidayGroundhog *a,void *owner,const AFHolidayGroundhogOps *o,int seconds) {
    if(!a || !owner || af_hg_live || !ready(o) || seconds<0 || seconds>=86400)return 0;
    int *area=o->area(o->context,0);int existed=area!=0;
    if(!area)area=o->area(o->context,1);
    if(!area)return 0;
    __builtin_memset(a,0,sizeof(*a));a->owner=owner;a->ops=o;a->awaiting_birth=area;
    a->action=seconds>=28800?AF_HG_AFTER:AF_HG_BEFORE;
    if(existed && *area==1) {a->action=AF_HG_BIRTH_WAIT;a->timer=600;}
    a->clip.term=term(seconds);af_hg_live=a;return 1;
}
void af_holiday_groundhog_end(AFHolidayGroundhog *a) {
    if(!a || af_hg_live!=a)return;
    af_hg_live=0;a->ops->death(a->ops->context,a->owner);
}
int af_holiday_groundhog_signal(AFHolidayGroundhog *a,unsigned int event) {
    if(!a || af_hg_live!=a || event<AF_HG_MAJIN_DONE || event>AF_HG_SONCHO_DONE)return 0;
    a->event_state=(int)event;return 1;
}
int af_holiday_groundhog_step(AFHolidayGroundhog *a,int seconds) {
    if(!a || af_hg_live!=a || !ready(a->ops) || !a->awaiting_birth ||
       a->action<AF_HG_BEFORE || a->action>AF_HG_AFTER || seconds<0 || seconds>=86400)return 0;
    const AFHolidayGroundhogOps *o=a->ops;void *c=o->context;
    a->clip.term=term(seconds);
    if(!a->clip.speaker)a->clip.speaker=o->find(c,0xD087);
    void *target=a->attention_mode?a->clip.groundhog:a->clip.speaker;
    if(target)o->attention(c,target);
    switch(a->action) {
    case AF_HG_BEFORE:
        if(seconds>=28800) {
            a->clip.fading_title=1;
            if(o->fade(c)==1) {a->clip.fading_title=0;*a->awaiting_birth=1;}
        }
        break;
    case AF_HG_BIRTH_WAIT:
        if(--a->timer<=0)a->action=AF_HG_BIRTH;
        break;
    case AF_HG_BIRTH:
        if(o->spawn(c,0xD081,5,8)==1) {
            void *actor=o->find(c,0xD081);
            /* Source assumes spawn publishes its actor before returning. Keep
             * the request pending if a broken provider violates that contract. */
            if(!actor)return 0;
            o->parent(c,actor,a->owner);a->clip.groundhog=actor;*a->awaiting_birth=0;
            a->attention_mode=1;o->music(c,AF_HG_QUIET_FIELD,360,0);
            a->timer=240;a->action=AF_HG_MUSIC_WAIT;
        }
        break;
    case AF_HG_MUSIC_WAIT:
        if(--a->timer<=0) {o->music(c,AF_HG_SPEECH_MUSIC,360,0);a->action=AF_HG_RETIRE_WAIT;}
        break;
    case AF_HG_RETIRE_WAIT:
        if(a->event_state==AF_HG_MAJIN_DONE) {
            a->timer=60;o->reverse_camera(c);o->music(c,AF_HG_END_MUSIC,360,0);
            a->attention_mode=0;a->action=AF_HG_SPEECH_WAIT;
        }
        break;
    case AF_HG_SPEECH_WAIT:
        if(--a->timer<=0)a->action=AF_HG_SPEECH_END;
        break;
    case AF_HG_SPEECH_END:
        if(a->event_state==AF_HG_SONCHO_DONE) {a->timer=20;a->action=AF_HG_FADE_WAIT;}
        break;
    case AF_HG_FADE_WAIT:
        if(--a->timer<=0) {
            af_hd_state.fading_title=1;o->music(c,AF_HG_END_QUIET,0,0);
            o->music(c,AF_HG_QUIET_RETURN,360,60);a->action=AF_HG_AFTER;
        }
        break;
    case AF_HG_AFTER:break;
    }
    a->event_state=AF_HG_NONE;return 1;
}
int af_holiday_groundhog_read(AFHolidayTransition *view,int *area) {
    if(!view)return 0;
    AFHolidayGroundhog *a=af_hg_live;
    if(a && (!ready(a->ops) || a->awaiting_birth!=area))return 0;
    view->groundhog_present=a!=0;
    view->groundhog.fading_title=a?a->clip.fading_title:0;
    view->groundhog_save_present=area!=0;view->groundhog_save._00=area?*area:0;
    view->common.event_title_fade_in_progress=af_hd_state.fading_title;
    return 1;
}
void af_holiday_groundhog_commit(const AFHolidayTransition *view,int *area,unsigned int phase) {
    if(!view)return;
    if(phase==AF_HT_BEFORE_SCENE && area && view->groundhog_save_present)*area=view->groundhog_save._00;
    if(phase==AF_HT_RETURN_STATE)af_hd_state.fading_title=view->common.event_title_fade_in_progress;
}
