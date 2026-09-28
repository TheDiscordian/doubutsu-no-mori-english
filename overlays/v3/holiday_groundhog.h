#ifndef AF_V3_HOLIDAY_GROUNDHOG_H
#define AF_V3_HOLIDAY_GROUNDHOG_H
#include "holiday_transition.h"
/* Normalised source controller; neither game's actor/common structures are
 * cast to this view. The native owner supplies checked actor identities. */
enum {
    AF_HG_BEFORE,AF_HG_BIRTH_WAIT,AF_HG_BIRTH,AF_HG_RETIRE_WAIT,
    AF_HG_MUSIC_WAIT,AF_HG_SPEECH_WAIT,AF_HG_SPEECH_END,AF_HG_FADE_WAIT,AF_HG_AFTER
};
enum {AF_HG_NONE,AF_HG_MAJIN_DONE,AF_HG_SONCHO_DONE};
enum {AF_HG_QUIET_FIELD,AF_HG_SPEECH_MUSIC,AF_HG_END_MUSIC,AF_HG_END_QUIET,AF_HG_QUIET_RETURN};
typedef struct AFHolidayGroundhog AFHolidayGroundhog;
typedef struct {
    void *context;
    /* Actual event common area, four bytes, retained across scene changes.
     * reserve=0 queries; reserve=1 reserves when absent. */
    int *(*area)(void *,int reserve);
    void *(*find)(void *,unsigned int source_name);
    int (*spawn)(void *,unsigned int source_name,int unit_x,int unit_z);
    void (*parent)(void *,void *actor,void *owner);
    void (*attention)(void *,void *actor);
    int (*fade)(void *);
    /* stop_type is the source audio transition word, NOT a frame duration. */
    void (*music)(void *,unsigned int operation,unsigned int stop_type,unsigned int delay_ticks);
    void (*reverse_camera)(void *);
    void (*death)(void *,void *owner);
} AFHolidayGroundhogOps;
struct AFHolidayGroundhog {
    void *owner;
    const AFHolidayGroundhogOps *ops;
    int *awaiting_birth;
    int action,event_state,timer,attention_mode;
    struct {int term;void *groundhog,*speaker;int fading_title;} clip;
};
extern AFHolidayGroundhog *af_hg_live;
int af_holiday_groundhog_begin(AFHolidayGroundhog *,void *,const AFHolidayGroundhogOps *,int seconds);
void af_holiday_groundhog_end(AFHolidayGroundhog *);
/* One complete donor 60-Hz update; native owner calls twice per 30-Hz frame. */
int af_holiday_groundhog_step(AFHolidayGroundhog *,int seconds);
int af_holiday_groundhog_signal(AFHolidayGroundhog *,unsigned int event);
/* Supply the actual common area even when no control actor is currently live. */
int af_holiday_groundhog_read(AFHolidayTransition *,int *area);
void af_holiday_groundhog_commit(const AFHolidayTransition *,int *area,unsigned int phase);
#endif
