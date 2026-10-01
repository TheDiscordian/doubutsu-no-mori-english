/* Shared calendar -> read -> keyboard -> finish -> privacy -> commit flow.
 * GAFE01 m_calendar_ovl.c, m_diary_ovl.c and m_cpwarning_ovl.c supply the rules.
 * Animation/drawing is deliberately outside this controller. */
#include "diary_menu.h"
static int valid(const AFDiaryMenu *m,const AFDiaryMenuAccess *a) {
    return m && a && a->live && a->widths && m->viewer<AF_DIARY_VIEWERS && m->owner<4 &&
        m->state<=AF_DIARY_ERROR && m->month_delta>=-11 && m->month_delta<=11 &&
        m->selected.day && m->selected.day<=af_diary_days(m->selected.year,m->selected.month);
}
static void events(AFDiaryMenu *m,const AFDiaryMenuAccess *a) {
    unsigned int n=a->event_count?a->event_count(a->context,m->selected,m->owner):0;
    m->events=n>6?6:n;m->event_index=0;
}
int af_diary_menu_open(AFDiaryMenu *m,const AFDiaryMenuAccess *a,unsigned int viewer,
    unsigned int owner,AFDiaryDate today,AFDiaryDates dates) {
    if(!m || !a || !a->live || !a->widths || viewer>=AF_DIARY_VIEWERS || owner>=4)return AF_DIARY_ARGUMENT;
    int result=af_diary_calendar_refresh(a->live,owner,today,dates);
    if(result<0)return result;
    /* Donor mCD_calendar_wellcome_on does not mark visiting players. */
    if(viewer<AF_DIARY_PLAYERS) {
        result=af_diary_calendar_visit(a->live,viewer,today,dates);
        if(result<0)return result;
    }
    /* Do not construct a 2 KiB temporary menu on the native thread stack. */
    volatile unsigned char *p=(volatile unsigned char *)m;
    for(unsigned int i=0;i<sizeof(*m);i++)p[i]=0;
    m->viewer=viewer;m->owner=owner;m->today=m->selected=today;
    m->state=AF_DIARY_MONTH;return AF_DIARY_OK;
}
static int month(AFDiaryMenu *m,int delta) {
    if(delta<-11 || delta>11)return AF_DIARY_UNCHANGED;
    int n=(int)m->today.year*12+m->today.month-1+delta;
    if(n<12 || n>=65536*12)return AF_DIARY_UNCHANGED;
    m->selected=(AFDiaryDate){n/12,n%12+1,1};m->month_delta=delta;return AF_DIARY_OK;
}
int af_diary_menu_input(AFDiaryMenu *m,const AFDiaryMenuAccess *a,unsigned int trigger,
    int repeat_x,int scroll) {
    if(!valid(m,a) || repeat_x<-1 || repeat_x>1 || scroll<-10 || scroll>10)return AF_DIARY_ARGUMENT;
    switch(m->state) {
    case AF_DIARY_MONTH:
        if(trigger&(AF_DIARY_B|AF_DIARY_START))m->state=AF_DIARY_CLOSED;
        else if(repeat_x)return month(m,m->month_delta+repeat_x);
        else if(trigger&AF_DIARY_UP)return month(m,0);
        else if(trigger&AF_DIARY_A) {
            m->selected.day=m->month_delta?1:m->today.day;
            m->state=AF_DIARY_DAY;events(m,a);
        } else return AF_DIARY_UNCHANGED;
        break;
    case AF_DIARY_DAY: {
        int day=m->selected.day;
        if(trigger&AF_DIARY_B)m->state=AF_DIARY_MONTH;
        else if(trigger&AF_DIARY_A) {
            int result=af_diary_begin(&m->draft,a->live,m->viewer,m->owner,m->selected.month-1,a->widths);
            m->error=result<0?result:0;
            m->state=result==AF_DIARY_LOCKED?AF_DIARY_WARNING:result<0?AF_DIARY_ERROR:AF_DIARY_READ;
        } else if(trigger&AF_DIARY_LEFT)day--;
        else if(trigger&AF_DIARY_RIGHT)day++;
        else if(trigger&AF_DIARY_UP) {
            if(m->event_index) {m->event_index--;return AF_DIARY_OK;}
            day-=7;
        } else if(trigger&AF_DIARY_DOWN) {
            if(m->event_index+1<m->events) {m->event_index++;return AF_DIARY_OK;}
            day+=7;
        } else return AF_DIARY_UNCHANGED;
        if(day!=(int)m->selected.day) {
            if(day<1 || day>(int)af_diary_days(m->selected.year,m->selected.month))return AF_DIARY_UNCHANGED;
            m->selected.day=day;events(m,a);
        }
        break;
    }
    case AF_DIARY_READ:
        if(trigger&(AF_DIARY_A|AF_DIARY_B|AF_DIARY_START)) {
            m->state=(trigger&AF_DIARY_B) || m->draft.readonly?AF_DIARY_DAY:AF_DIARY_EDIT;
        } else if(scroll)return af_diary_scroll(&m->draft,scroll,a->widths);
        else return AF_DIARY_UNCHANGED;
        break;
    case AF_DIARY_CONFIRM:
        /* Same finished/keep-writing result values as EDITENDCHK. B resumes. */
        if(trigger&AF_DIARY_B) {m->state=AF_DIARY_EDIT;break;}
        if(trigger&(AF_DIARY_A|AF_DIARY_START)) {
            m->state=m->choice?AF_DIARY_EDIT:AF_DIARY_PRIVACY;
            if(!m->choice)m->choice=a->live->bytes[16+m->owner*AF_DIARY_PLAYER+98];
        } else if(trigger&AF_DIARY_UP)m->choice=0;
        else if(trigger&AF_DIARY_DOWN)m->choice=1;
        else return AF_DIARY_UNCHANGED;
        break;
    case AF_DIARY_PRIVACY:
        if(m->viewer!=m->owner || m->draft.player!=m->owner ||
           m->draft.month!=m->selected.month-1 || m->draft.readonly)return AF_DIARY_READONLY;
        if(trigger&AF_DIARY_A) {
            int result=af_diary_commit_locked(a->live,&m->draft,a->scratch,a->widths,
                a->capacity,a->context,m->choice);
            m->error=result<0?result:0;
            m->state=result<0?AF_DIARY_ERROR:AF_DIARY_DAY;
            return result;
        } else if(trigger&AF_DIARY_LEFT)m->choice=0;
        else if(trigger&AF_DIARY_RIGHT)m->choice=1;
        else return AF_DIARY_UNCHANGED; /* Source has no B-to-exit here. */
        break;
    case AF_DIARY_WARNING:
        if(!(trigger&(AF_DIARY_A|AF_DIARY_B|AF_DIARY_START)))return AF_DIARY_UNCHANGED;
        m->state=AF_DIARY_DAY;m->error=0;break;
    case AF_DIARY_ERROR:
        if(!(trigger&(AF_DIARY_A|AF_DIARY_B|AF_DIARY_START)))return AF_DIARY_UNCHANGED;
        /* Capacity errors preserve the editable draft. An invalid saved page or
         * externally changed source cannot safely resume that edit session. */
        m->state=m->error==AF_DIARY_CAPACITY?AF_DIARY_EDIT:AF_DIARY_DAY;
        m->error=0;break;
    default:return AF_DIARY_UNCHANGED;
    }
    return AF_DIARY_OK;
}
int af_diary_menu_edit(AFDiaryMenu *m,const AFDiaryMenuAccess *a,unsigned int command,int code) {
    if(!valid(m,a) || m->state!=AF_DIARY_EDIT)return AF_DIARY_ARGUMENT;
    if(m->viewer!=m->owner || m->draft.readonly)return AF_DIARY_READONLY;
    if(command==5) {m->state=AF_DIARY_CONFIRM;m->choice=0;return AF_DIARY_OK;}
    return af_diary_command(&m->draft,command,code,a->widths);
}
int af_diary_menu_grid(const AFDiaryMenu *m,const AFDiary *data,AFDiaryDates dates,
    unsigned char days[37],unsigned char marks[37]) {
    if(!m || !days || !marks || m->owner>=4 || !af_diary_valid(data))return AF_DIARY_ARGUMENT;
    AFDiaryDate d={m->selected.year,m->selected.month,1};
    int first=af_diary_weekday(d),count=af_diary_days(d.year,d.month);
    if(first<0 || first+count>37)return AF_DIARY_ARGUMENT;
    for(int i=0;i<37;i++)days[i]=marks[i]=0;
    for(int day=1;day<=count;day++) {
        d.day=day;
        /* Donor mCD_visiter_chk/mCD_soncho_chk suppress these marks when the
         * current viewer is a foreign player, even for a resident's calendar. */
        int mark=m->viewer==4?0:af_diary_calendar_mark(data,m->owner,m->today,d,dates);
        if(mark<0)return mark;
        days[first+day-1]=day;marks[first+day-1]=mark;
    }
    return AF_DIARY_OK;
}
