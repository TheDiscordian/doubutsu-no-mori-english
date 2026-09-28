#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_groundhog.h"
#include "holiday_demo.h"
AFHolidayGroundhog *af_hg_live;
AFHDDemoState af_hd_state;
static int saved,exists,capacity=1,fade_ok,spawn_ok,found=1;
static int searches,spawns,parents,attentions,reverse_count,deaths,music_count;
static unsigned int music[8][3];
static int owner,speaker,groundhog;
static void *last_attention;
static int *area(void *c,int reserve) {
    assert(c==&owner);
    if(reserve && capacity) {exists=1;saved=0;}
    return exists?&saved:0;
}
static void *find(void *c,unsigned int name) {
    assert(c==&owner);searches++;
    assert(name==0xD081 || name==0xD087);
    return name==0xD087?&speaker:found?&groundhog:0;
}
static int spawn(void *c,unsigned int name,int x,int z) {
    assert(c==&owner && name==0xD081 && x==5 && z==8);spawns++;return spawn_ok;
}
static void parent(void *c,void *actor,void *p) {
    assert(c==&owner && actor==&groundhog && p==&owner);parents++;
}
static void attention(void *c,void *actor) {
    assert(c==&owner && (actor==&speaker || actor==&groundhog));
    last_attention=actor;attentions++;
}
static int fade(void *c) {
    assert(c==&owner && af_hg_live && af_hg_live->clip.fading_title==1);return fade_ok;
}
static void audio(void *c,unsigned int operation,unsigned int ticks,unsigned int delay) {
    assert(c==&owner && music_count<8);
    music[music_count][0]=operation;music[music_count][1]=ticks;music[music_count++][2]=delay;
}
static void reverse(void *c) {assert(c==&owner);reverse_count++;}
static void death(void *c,void *actor) {assert(c==&owner && actor==&owner && !af_hg_live);deaths++;}
static const AFHolidayGroundhogOps ops={&owner,area,find,spawn,parent,attention,fade,audio,reverse,death};
static void frames(AFHolidayGroundhog *a,int n) {
    for(int i=0;i<n;i++)for(int j=0;j<2;j++)assert(af_holiday_groundhog_step(a,28800)==1);
}
int main(void) {
    AFHolidayGroundhog a,other;AFHolidayTransition view={0};
    AFHolidayGroundhogOps missing=ops;missing.music=0;
    assert(!af_holiday_groundhog_begin(&a,&owner,&missing,0));
    capacity=0;assert(!af_holiday_groundhog_begin(&a,&owner,&ops,0));
    assert(!af_hg_live && !exists);capacity=1;
    assert(af_holiday_groundhog_begin(&a,&owner,&ops,0));
    assert(exists && saved==0 && a.action==AF_HG_BEFORE);
    assert(!af_holiday_groundhog_begin(&other,&owner,&ops,0));
    af_holiday_groundhog_end(&other);assert(af_hg_live==&a && deaths==0);
    int times[]={26999,27000,27900,28500,28740};
    for(int i=0;i<5;i++) {
        assert(af_holiday_groundhog_step(&a,times[i]));assert(a.clip.term==i);
    }
    assert(af_holiday_groundhog_step(&a,28800));assert(a.clip.term==5);
    assert(!saved && a.clip.fading_title==1);
    assert(af_holiday_groundhog_read(&view,&saved));
    assert(view.groundhog_present && view.groundhog.fading_title==1 && view.groundhog_save_present);
    int wrong=0;assert(!af_holiday_groundhog_read(&view,&wrong));
    fade_ok=1;assert(af_holiday_groundhog_step(&a,28800));
    assert(saved==1 && !a.clip.fading_title);
    af_holiday_groundhog_end(&a);assert(!af_hg_live && deaths==1 && saved==1);
    /* A fresh native actor after the accepted scene change resumes the saved
     * birth state. The source's 600 ticks are 300 native frames, not 600. */
    assert(af_holiday_groundhog_begin(&a,&owner,&ops,28800));
    assert(a.action==AF_HG_BIRTH_WAIT && a.timer==600);
    frames(&a,299);assert(a.action==AF_HG_BIRTH_WAIT && a.timer==2);
    frames(&a,1);assert(a.action==AF_HG_BIRTH);
    assert(af_holiday_groundhog_step(&a,28800));assert(saved && spawns==1 && !parents);
    spawn_ok=1;found=0;assert(!af_holiday_groundhog_step(&a,28800));assert(saved && !parents);
    found=1;assert(af_holiday_groundhog_step(&a,28800));
    assert(!saved && parents==1 && a.clip.groundhog==&groundhog && a.timer==240);
    assert(a.action==AF_HG_MUSIC_WAIT && music_count==1);
    frames(&a,119);assert(a.timer==2 && last_attention==&groundhog);
    frames(&a,1);assert(a.action==AF_HG_RETIRE_WAIT && music_count==2);
    frames(&a,20);assert(a.action==AF_HG_RETIRE_WAIT && !reverse_count);
    assert(!af_holiday_groundhog_signal(&other,AF_HG_MAJIN_DONE));
    assert(!af_holiday_groundhog_signal(&a,3));
    assert(af_holiday_groundhog_signal(&a,AF_HG_MAJIN_DONE));
    assert(af_holiday_groundhog_step(&a,28800));
    assert(a.action==AF_HG_SPEECH_WAIT && a.timer==60 && reverse_count==1 && !a.event_state);
    frames(&a,29);assert(a.timer==2 && last_attention==&speaker);
    frames(&a,1);assert(a.action==AF_HG_SPEECH_END);
    frames(&a,20);assert(a.action==AF_HG_SPEECH_END && !af_hd_state.fading_title);
    assert(af_holiday_groundhog_signal(&a,AF_HG_SONCHO_DONE));
    assert(af_holiday_groundhog_step(&a,28800));assert(a.timer==20 && a.action==AF_HG_FADE_WAIT);
    frames(&a,9);assert(a.timer==2 && !af_hd_state.fading_title);
    frames(&a,1);assert(a.action==AF_HG_AFTER && af_hd_state.fading_title==1);
    assert(music_count==5);
    unsigned int expected[5][3]={{AF_HG_QUIET_FIELD,360,0},{AF_HG_SPEECH_MUSIC,360,0},
        {AF_HG_END_MUSIC,360,0},{AF_HG_END_QUIET,0,0},{AF_HG_QUIET_RETURN,360,60}};
    assert(!memcmp(music,expected,sizeof(expected)));
    assert(af_holiday_groundhog_read(&view,&saved));
    assert(view.common.event_title_fade_in_progress==1);
    frames(&a,20);assert(music_count==5 && reverse_count==1);
    af_holiday_groundhog_end(&a);assert(deaths==2 && !af_hg_live);
    assert(!af_holiday_groundhog_step(&a,28800));
    saved=1;assert(af_holiday_groundhog_read(&view,&saved));
    assert(!view.groundhog_present && view.groundhog_save._00==1);
    view.groundhog_save._00=0;
    af_holiday_groundhog_commit(&view,&saved,AF_HT_BEFORE_SCENE);
    assert(!saved && af_hd_state.fading_title==1);
    view.common.event_title_fade_in_progress=0;
    af_holiday_groundhog_commit(&view,&saved,AF_HT_RETURN_STATE);assert(!af_hd_state.fading_title);
    assert(af_holiday_groundhog_begin(&a,&owner,&ops,28801));assert(a.action==AF_HG_AFTER);
    af_holiday_groundhog_end(&a);exists=0;
    assert(af_holiday_groundhog_read(&view,0));assert(!view.groundhog_save_present && !view.groundhog_present);
    assert(searches>0 && attentions>0);puts("Complete Groundhog timing, signals, lifecycle, fade-state, and failure checks pass (native I/O doubled)");
    return 0;
}
