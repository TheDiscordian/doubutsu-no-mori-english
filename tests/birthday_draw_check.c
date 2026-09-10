#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

typedef struct { unsigned a, b; } Gfx;
void af_birthday_draw(void *, void *, void *);
static unsigned char submenu[64], menu[64] __attribute__((aligned(16)));
static unsigned char overlay[0x10800] __attribute__((aligned(16)));
static unsigned char asset[22208], game[16], graph[0x300], matrix[64];
static unsigned short birthday[4] __attribute__((aligned(16)));
static Gfx commands[8], *end;
static unsigned calls, current_month, current_day, current_selection;
static const char *names[] = {"January","February","March","April","May","June",
    "July","August","September","October","November","December"};
static float window_x, window_y;

static void font_matrix(void *g) { assert(g==graph); }
void *af_birthday_test_pointer(const void *p, unsigned offset) {
    if(p==submenu&&offset==0x2C)return overlay;
    if(p==overlay&&offset==0x10710)return birthday;
    if(p==overlay&&offset==0x106B4)return (void *)font_matrix;
    if(p==menu&&offset==0x28)return asset;
    if(p==game&&offset==0)return graph;
    if(p==graph&&offset==0x298)return commands;
    assert(!"Unexpected native pointer access");return 0;
}
void af_birthday_test_graph_end(void *g,Gfx *p) { assert(g==graph);end=p; }
void af_birthday_scale(float x,float y,float z,int mode) { assert(x==16&&y==16&&z==1&&mode==0); }
void af_birthday_translate(float x,float y,float z,int mode) { assert(x==window_x&&y==window_y&&z==140&&mode==1); }
void *af_birthday_matrix(void *g) { assert(g==graph);return matrix; }
void af_birthday_number(unsigned char *out,unsigned n,int digits,int mode,int flag) {
    assert(n==current_day&&digits==2&&mode==0&&flag==1);
    out[0]='0'+n/10;out[1]='0'+n%10;
}
void af_birthday_font(void *g,const unsigned char *text,int length,float x,float y,
                     int r,int green,int b,int alpha,int a,int c,float sx,float sy,int mode) {
    char expected_day[3];const char *expected;
    const float xpos[]={119,97,171,198};
    assert(g==game&&calls<4&&alpha==255&&!a&&!c&&!mode);
    assert(x==window_x+xpos[calls]&&y==-window_y+(calls?124:88));
    assert(sx==(calls?1:0.875f)&&sy==sx);
    if(!calls){expected="When's your birthday?";assert(r==255&&green==255&&b==255);}
    else {
        if(calls==1)expected=current_month>=1&&current_month<=12?names[current_month-1]:"?";
        else if(calls==2){snprintf(expected_day,sizeof(expected_day),"%02u",current_day);expected=expected_day;}
        else expected="OK";
        if(current_selection==calls-1)assert(r==195&&green==0&&b==0);
        else assert(r==70&&green==145&&b==225);
    }
    assert(length==(int)strlen(expected));assert(!memcmp(text,expected,(unsigned)length));calls++;
}

static void put_float(void *p,unsigned offset,float value){memcpy((unsigned char *)p+offset,&value,4);}
int main(void) {
    unsigned month,selection;
    memcpy(asset+0x2DB8,"When's your birthday?",22);
    for(month=0;month<12;month++)memcpy(asset+0x2DD0+month*10,names[month],strlen(names[month])+1);
    memcpy(asset+0x2E48,"?",2);memcpy(asset+0x2E52,"OK",3);
    for(month=0;month<=13;month++)for(selection=0;selection<3;selection++) {
        unsigned char saved_asset[sizeof(asset)],saved_overlay[sizeof(overlay)];
        unsigned short saved_birthday[4];
        current_month=month;current_selection=selection;current_day=month==2?29:31;
        birthday[0]=month;birthday[1]=current_day;memcpy(birthday+2,&selection,4);
        window_x=month&1?12.5f:-16.0f;window_y=month&1?-24.0f:0;
        put_float(menu,0x18,window_x);put_float(menu,0x1C,window_y);
        put_float(overlay,0x10698,3.25f);put_float(overlay,0x1069C,-7.75f);
        memcpy(saved_asset,asset,sizeof(asset));memcpy(saved_overlay,overlay,sizeof(overlay));
        memcpy(saved_birthday,birthday,sizeof(birthday));
        memset(commands,0xA5,sizeof(commands));calls=0;end=0;
        af_birthday_draw(submenu,menu,game);
        assert(calls==4&&end==commands+6);
        assert(commands[0].a==0xDB060030&&commands[0].b==(unsigned)(uintptr_t)asset);
        assert(commands[1].a==0xDA380003&&commands[1].b==(unsigned)(uintptr_t)matrix);
        assert(commands[2].a==0xDE000000&&commands[2].b==0x0C000740);
        assert(commands[3].a==0xE8000000&&!commands[3].b);
        assert(commands[4].a==(0xF2000000|122<<12|15));
        assert(commands[4].b==((122+124)<<12|(15+124)));
        assert(commands[5].a==0xDE000000&&commands[5].b==0x0C0012C8);
        assert(commands[6].a==0xA5A5A5A5&&commands[7].b==0xA5A5A5A5);
        assert(!memcmp(saved_asset,asset,sizeof(asset))&&!memcmp(saved_overlay,overlay,sizeof(overlay)));
        assert(!memcmp(saved_birthday,birthday,sizeof(birthday)));
    }
    puts("Birthday drawing: full prompt/month/day/OK, 42 read-only layouts, commands and bounds pass");
    return 0;
}
