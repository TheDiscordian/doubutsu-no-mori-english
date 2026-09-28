/* GAFE01 calendar, paper, finish, and privacy drawing on native display lists.
 * Converted models retain their source vertices/UVs. The menu owner retains
 * projection, transitions, event scheduling, input, and keyboard lifecycle. */
#include <PR/mbi.h>
#include "diary_draw.h"
#include "../hboard/editor.h"
#include "diary-art.inc"

#define PTR(p,o) (*(void **)((unsigned char *)(p)+(o)))
#define CALL(a,t,...) ((t (*)(__VA_ARGS__))(a))
static int room(void *g,unsigned int n) {
    unsigned int a=(unsigned int)PTR(g,0x298),b=(unsigned int)PTR(g,0x29C);
    return !(a&7) && !(b&7) && b>=a && n<=b-a;
}
static void dl(void *g,unsigned int model) {
    Gfx *p=PTR(g,0x298);gSPDisplayList(p++,model);PTR(g,0x298)=p;
}
static void push(void) {CALL(0x800E020Cu,void,void)();}
static void pop(void) {CALL(0x800E0244u,void,void)();}
static void translate(float x,float y,float z) {CALL(0x800E0314u,void,float,float,float,int)(x,y,z,1);}
static void matrix(void *g) {
    unsigned int at=CALL(0x800E13C4u,unsigned int,void *)(g);
    Gfx *p=PTR(g,0x298);gSPMatrix(p++,at,G_MTX_NOPUSH|G_MTX_LOAD|G_MTX_MODELVIEW);PTR(g,0x298)=p;
}
static void position(void *g,float x,float y,float scale) {
    CALL(0x800E041Cu,void,float,float,float,int)(16*scale,16*scale,1,0);
    translate(x,y,140);matrix(g);
}
static void colour(void *g,const unsigned char *prim,const unsigned char *env,unsigned int alpha) {
    Gfx *p=PTR(g,0x298);gDPPipeSync(p++);
    if(prim)gDPSetPrimColor(p++,0,255,prim[0],prim[1],prim[2],alpha);
    if(env)gDPSetEnvColor(p++,env[0],env[1],env[2],alpha);
    PTR(g,0x298)=p;
}
static void segment(void *g,const void *art) {
    Gfx *p=PTR(g,0x298);gSPSegment(p++,6,(unsigned int)art&0x1FFFFFFFu);PTR(g,0x298)=p;
}
static int valid(const AFDiaryDraw *d) {
    return d && d->art && !((unsigned int)d->art&15) && d->x>=-320 && d->x<=320 &&
        d->y>=-480 && d->y<=480 && d->scale>=0 && d->scale<=1 &&
        d->answer_scale>=0 && d->answer_scale<=1 && d->alpha<=255 &&
        d->control_y>=-300 && d->control_y<=300 &&
        d->arrow_x>=-320 && d->arrow_x<=320 &&
        d->event_length<=48 && (!d->event_length || d->event_label);
}
static void font(void *submenu,void *g,void *game,const unsigned char *s,unsigned int n,
                 float x,float y,const unsigned char *rgb,float scale) {
    if(!n || scale<=0)return;
    unsigned char *ovl=PTR(submenu,0x2C);
    ((struct af_hboard_matrix_pointer *)(ovl+0x106B4))->function(g);
    af_hboard_font_line(game,s,n,x,y,rgb[0],rgb[1],rgb[2],255,0,1,scale,scale,0);
}

int af_diary_draw_calendar(void *submenu,void *game,const AFDiaryMenu *m,const AFDiary *data,
                          AFDiaryDates dates,const AFDiaryDraw *d) {
    unsigned char days[37],marks[37];
    if(!submenu || !PTR(submenu,0x2C) || !game || !valid(d) || !m ||
        af_diary_menu_grid(m,data,dates,days,marks)!=AF_DIARY_OK)return AF_DIARY_ARGUMENT;
    for(int i=0;i<37;i++)if(d->day_types[i]>4 || marks[i]>2)return AF_DIARY_ARGUMENT;
    void *g=PTR(game,0);if(!g || !room(g,11000+d->event_length*256))return AF_DIARY_FULL;
    unsigned int month=m->selected.month-1,year=m->selected.year,selected=37;
    if(m->state!=AF_DIARY_MONTH)for(unsigned int i=0;i<37;i++)if(days[i]==m->selected.day)selected=i;
    if(month>=12)return AF_DIARY_ARGUMENT;
    unsigned int saved=*(unsigned int *)0x801458B8u; /* native segment six */
    push();segment(g,d->art);position(g,d->x,d->y,1);dl(g,ART_needlework_before_model);
    dl(g,calendar_palettes[month]);dl(g,month?ART_calendar_background_2:ART_calendar_background_1);
    dl(g,ART_cal_win_tuki_model);dl(g,ART_cal_win_shita_model);dl(g,ART_cal_win_futi_model);
    dl(g,ART_cal_win_nitiyouT_model);dl(g,ART_cal_win_doyouT_model);dl(g,ART_cal_win_hijituT_model);
    dl(g,ART_cal_win_nen_before);
    for(unsigned int i=0;i<4;i++,year/=10) {dl(g,calendar_years[year%10]);dl(g,calendar_year_models[i]);}
    dl(g,calendar_months[month]);dl(g,ART_cal_win_monthT_model);dl(g,ART_calendar_box);
    for(unsigned int i=0;i<37;i++)if(i!=selected) {
        push();translate((i%7)*32,-(int)(i/7)*20,0);matrix(g);
        unsigned int t=d->day_types[i];colour(g,box_prim_table[t],box_env_table[t],255);
        dl(g,ART_cal_win_boxT_model);pop();
    }
    for(unsigned int i=0;i<37;i++)if(i!=selected && days[i]) {
        push();translate((i%7)*32,-(int)(i/7)*20,0);matrix(g);
        colour(g,number_prim_table[d->day_types[i]],0,255);dl(g,calendar_days[days[i]-1]);dl(g,ART_cal_win_suuji_model);
        if(marks[i]) {colour(g,icon_mark_prim_table[marks[i]],0,255);dl(g,ART_cal_icon_mark_model);}
        pop();
    }
    if(selected<37) {
        unsigned int t=d->day_types[selected];
        push();translate((selected%7)*32,-(int)(selected/7)*20,0);matrix(g);
        dl(g,ART_calendar_box_selected);colour(g,box_prim_table[t],box_env_table[t],255);dl(g,ART_cal_win_boxT_model);
        translate(0,4,0);matrix(g);colour(g,number2_prim_table[t],0,255);
        dl(g,calendar_days[days[selected]-1]);dl(g,ART_cal_win_suuji_model);
        if(marks[selected]) {colour(g,icon_mark_prim_table[marks[selected]],0,255);dl(g,ART_cal_icon_mark_model);}
        dl(g,ART_cal_icon_cursor_model);pop();
    }
    matrix(g);dl(g,ART_calendar_event);
    unsigned int event_type=m->events && selected<37?d->day_types[selected]:0;
    colour(g,box_prim_table[event_type],box_env_table[event_type],255);dl(g,ART_cal_win_eventT_model);
    if(m->events && d->event_attended)dl(g,ART_cal_icon_sakana_model);
    if(m->events>1) {
        static const unsigned char blue[]={0,0,255};
        push();translate(d->arrow_x,-1.5f,0);matrix(g);colour(g,blue,0,d->alpha);
        dl(g,m->event_index+1==m->events?ART_cal_icon_yajirushi_gfx2:ART_cal_icon_yajirushi_gfx);pop();
    }
    position(g,d->x,d->y,1);
    if(m->state==AF_DIARY_MONTH) {
        dl(g,ART_cal_hyouji_3DT_model);dl(g,ART_cal_hyouji_shitaT_model);
        dl(g,ART_cal_hyouji_b2_model);dl(g,ART_cal_hyouji_amojiT_model);
        if(m->month_delta>-11)dl(g,ART_cal_hyoji_yajiA_gfx);
        if(m->month_delta<11)dl(g,ART_cal_hyoji_yajiB_gfx);
        dl(g,d->stick_direction?ART_calendar_stick_tilt:ART_calendar_stick);
        if(d->stick_direction>0)CALL(0x800E041Cu,void,float,float,float,int)(-1,1,1,1);
        matrix(g);dl(g,ART_cal_hyouji_stT_model);
    } else {
        dl(g,ART_cal_hyouji2_shitaT_model);dl(g,ART_cal_hyouji2_bt_model);dl(g,ART_cal_hyouji2_b2_model);
        dl(g,ART_cal_hyouji2_bmojiT_model);dl(g,ART_cal_hyouji2_amojiT_model);
    }
    pop();segment(g,(void *)saved);
    if(m->events && d->event_length)font(submenu,g,game,d->event_label,d->event_length,128,161,number2_prim_table[event_type],0.875f);
    return AF_DIARY_OK;
}

int af_diary_draw_page(void *submenu,void *game,const AFDiaryMenu *m,const unsigned char *widths,const AFDiaryDraw *d) {
    AFDiaryLayout layout;
    if(!submenu || !PTR(submenu,0x2C) || !game || !valid(d) || !m || m->draft.month>=12 ||
       af_diary_layout(m->draft.text,m->draft.length,m->draft.cursor,widths,&layout)!=AF_DIARY_OK)return AF_DIARY_ARGUMENT;
    unsigned int n=0;
    for(unsigned int i=0;i<layout.rows;i++) {
        float y=64-d->y+16*i;
        if(y>=-12 && y<228)n+=layout.lines[i].length;
    }
    void *g=PTR(game,0);if(!g || !room(g,5000+n*256))return AF_DIARY_FULL;
    unsigned int saved=*(unsigned int *)0x801458B8u;
    push();segment(g,d->art);position(g,d->x,d->y,1);dl(g,ART_dia_init_mode_letter);
    dl(g,ART_dia_win_wT_model);dl(g,ART_dia_win_fusenT_model);dl(g,diary_months[m->draft.month]);dl(g,ART_dia_win_tukiT_model);
    push();translate(diary_month_adjust[m->draft.month],0,0);matrix(g);dl(g,ART_dia_win_moji_model);pop();
    translate(0,-194,0);matrix(g);dl(g,ART_dia_win2_wT_model);dl(g,ART_dia_win2_fusenT_model);
    translate(0,-164,0);matrix(g);dl(g,ART_dia_win3_wT_model);dl(g,ART_dia_win3_fusenT_model);
    if(d->read_controls) {
        position(g,d->x,d->control_y,1);dl(g,ART_dia_init_mode);
        dl(g,ART_diary_read_button);dl(g,ART_diary_read_label);
        dl(g,ART_dia_win_bb_model);dl(g,ART_dia_win_mojiT_model);
    }
    pop();segment(g,(void *)saved);
    static const unsigned char ink[]={60,60,85};
    for(unsigned int i=0;i<layout.rows;i++) {
        float y=64-d->y+16*i;
        if(y<-12 || y>=228)continue;
        AFDiaryLine *line=&layout.lines[i];unsigned int length=line->length;
        const unsigned char *text=m->draft.text+line->start;
        if(length && text[length-1]==0xCD)length--;
        if(length)font(submenu,g,game,text,length,64+d->x,y,ink,1);
    }
    if(d->editing) {
        unsigned char *o=PTR(submenu,0x2C),*menu=o+0x10358;
        struct af_hboard_native_editor *ed=PTR(o,0x106E0);
        if(!ed || ed->input!=m->draft.text || *(unsigned int *)(menu+0x38)!=6 ||
           !ed->cursor_draw || !ed->end_draw)return AF_DIARY_ARGUMENT;
        /* Parent drawing precedes the keyboard. Bind its actual marker assets
         * here instead of relying on whatever segment twelve held last frame. */
        unsigned int previous=*(unsigned int *)0x801458D0u;
        unsigned int art=(unsigned int)PTR(menu,0x28)&0x1FFFFFFFu;
        *(unsigned int *)0x801458D0u=art;
        Gfx *p=PTR(g,0x298);gSPSegment(p++,12,art);PTR(g,0x298)=p;
        ((struct af_hboard_matrix_pointer *)(o+0x106B4))->function(g);
        ed->cursor_draw(submenu,game,64+d->x+layout.cursor.x-7,64-d->y+16*layout.cursor.row);
        ed->end_draw(submenu,game,64+d->x+layout.end.x+1-160,120-(64-d->y+16*layout.end.row));
        *(unsigned int *)0x801458D0u=previous;
        p=PTR(g,0x298);gSPSegment(p++,12,previous&0x1FFFFFFFu);PTR(g,0x298)=p;
    }
    return AF_DIARY_OK;
}

int af_diary_draw_prompt(void *submenu,void *game,const AFDiaryMenu *m,const AFDiaryDraw *d) {
    if(!submenu || !PTR(submenu,0x2C) || !game || !valid(d) || !m || m->choice>1)return AF_DIARY_ARGUMENT;
    void *g=PTR(game,0);if(!g || !room(g,22000))return AF_DIARY_FULL;
    unsigned int saved=*(unsigned int *)0x801458B8u;
    static const unsigned char red[]={95,20,20},selected[]={30,30,215},faded[]={110,110,140};
    push();segment(g,d->art);
    unsigned int state=d->prompt_state?d->prompt_state:m->state;
    if(state==AF_DIARY_CONFIRM) {
        static const unsigned char blue[]={80,80,230};
        float y=d->y-300*(1-d->scale);
        position(g,d->x,y,1);dl(g,ART_lat_kakunin_DL_mode);dl(g,ART_lat_kakunin_wakuT_model);
        colour(g,blue,0,d->alpha);dl(g,ART_lat_kakunin_c_model);
        if(d->answers_visible) {
            position(g,d->x+65,y-74,1);
            CALL(0x800E041Cu,void,float,float,float,int)(d->answer_scale,d->answer_scale,1,1);
            matrix(g);dl(g,ART_lat_kakunin_DL_mode);dl(g,ART_lat_sentaku2_winT_model);
            if(d->answer_scale==1) {position(g,d->x+65,y-74-16*m->choice,1);dl(g,ART_lat_sentaku2_c_model);}
        }
        pop();segment(g,(void *)saved);
        font(submenu,g,game,diary_text_finish_question,sizeof(diary_text_finish_question),107+d->x,194-y,blue,1);
        if(d->answers_visible) {
            float x=225+d->x-45*d->answer_scale,text_y=194-y-43*d->answer_scale;
            font(submenu,g,game,diary_text_finish_yes,sizeof(diary_text_finish_yes),x,text_y,m->choice?faded:selected,d->answer_scale);
            font(submenu,g,game,diary_text_finish_rewrite,sizeof(diary_text_finish_rewrite),x,text_y+16*d->answer_scale,m->choice?selected:faded,d->answer_scale);
        }
        return AF_DIARY_OK;
    }
    position(g,d->x,d->y,d->scale);
    Gfx *p=PTR(g,0x298);gDPSetBlendColor(p++,255,255,255,40);PTR(g,0x298)=p;
    dl(g,ART_dia_att_winT_model);
    if(state==AF_DIARY_PRIVACY) {
        translate(m->choice?19:-19,-29,0);matrix(g);dl(g,ART_dia_att_cursor_model);
    }
    pop();segment(g,(void *)saved);
    float s=d->scale,x=160+d->x-112*s,y=120-d->y-56*s;
    if(state==AF_DIARY_PRIVACY) {
        font(submenu,g,game,diary_text_privacy_question_1,sizeof(diary_text_privacy_question_1),x+54*s,y+28*s,red,s);
        font(submenu,g,game,diary_text_privacy_question_2,sizeof(diary_text_privacy_question_2),x+30*s,y+52*s,red,s);
        font(submenu,g,game,diary_text_privacy_yes,sizeof(diary_text_privacy_yes),x+94*s,y+76*s,m->choice?faded:selected,s);
        font(submenu,g,game,diary_text_privacy_no,sizeof(diary_text_privacy_no),x+133*s,y+76*s,m->choice?selected:faded,s);
    } else {
        const unsigned char *text=diary_text_invalid;unsigned int n=sizeof(diary_text_invalid);
        if(state==AF_DIARY_WARNING) {text=diary_text_locked;n=sizeof(diary_text_locked);}
        else if(m->error==AF_DIARY_CAPACITY) {text=diary_text_capacity;n=sizeof(diary_text_capacity);}
        else if(m->error==AF_DIARY_CHANGED) {text=diary_text_changed;n=sizeof(diary_text_changed);}
        for(unsigned int first=0,i=0;i<=n;i++)if(i==n || text[i]==0xCD) {
            font(submenu,g,game,text+first,i-first,x+12*s,y+28*s,red,s);first=i+1;y+=16*s;
        }
    }
    return AF_DIARY_OK;
}
