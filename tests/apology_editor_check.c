#include <assert.h>
#include <stddef.h>
#include <string.h>
#include "edit.h"
#include "../overlays/hboard/editor.h"

void af_apology_editor_init(void *,void *);
void af_apology_editor_destruct(void *);
void af_apology_editor_command(void *,void *);
int af_apology_editor_exchange(struct af_hboard_native_editor *);
void af_apology_editor_cursor(struct af_hboard_native_editor *,short *,short *,int);
void af_apology_editor_key_draw(void *,const unsigned char *,int,float,float,int,int,int,int,int,int,float,float,int);

static union { max_align_t align; unsigned char bytes[0x10700]; } storage;
static union { max_align_t align; unsigned char bytes[0x50]; } menu;
static struct af_hboard_submenu_pointer submenu;
static struct af_hboard_native_editor ed;
static struct {unsigned char before[16],text[10],after[16];} input;
static int init_calls,done_calls,destruct_calls,cursor_calls,exchange_calls,draw_calls;
static unsigned char draw_text[2];
static int draw_len;

void af_hboard_editor_init(void *s,void *m){assert(s==&submenu && m==menu.bytes);++init_calls;}
void af_hboard_editor_destruct(void *s){assert(s==&submenu);++destruct_calls;}
void af_apology_original_command(void *s,void *m){assert(s==&submenu && m==menu.bytes);++done_calls;}
int af_apology_original_exchange(struct af_hboard_native_editor *p){assert(p==&ed);++exchange_calls;return 'A';}
void af_hboard_editor_cursor(struct af_hboard_native_editor *p,short *x,short *y,int n){
    assert(p==&ed);++cursor_calls;*x=(short)n;*y=9;
}
void af_hboard_font_line(void *game,const unsigned char *text,int len,float x,float y,
    int r,int g,int b,int alpha,int polygon,int proportional,float sx,float sy,int mode){
    assert(game==&ed && len>=1 && len<=2 && x==13.5f && y==27.0f && r==1 && g==2 && b==3);
    assert(alpha==255 && polygon==0 && proportional==0 && sx==0.875f && sy==0.875f && mode==0);
    ++draw_calls;draw_len=len;memcpy(draw_text,text,(size_t)len);
}
static void fresh(int kind){
    memset(&storage,0,sizeof(storage));memset(&menu,0,sizeof(menu));memset(&ed,0,sizeof(ed));
    memset(&input,0xA5,sizeof(input));memset(input.text,' ',10);
    submenu.overlay=storage.bytes;
    *(struct af_hboard_native_editor **)(storage.bytes+0x106E0)=&ed;
    *(unsigned char **)(storage.bytes+0x101E8)=input.text;
    *(int *)(storage.bytes+0x101E0)=kind;
    *(int *)(menu.bytes+0x38)=3;
    ed.input=input.text;ed.rows=1;ed.columns=10;ed.exchange=-1;
    af_apology_editor_init(&submenu,menu.bytes);
}
static void command(int cmd,int code){
    unsigned int i;
    ed.command=(unsigned char)cmd;ed.code=(unsigned char)code;
    af_apology_editor_command(&submenu,menu.bytes);
    for(i=0;i<16;++i)assert(input.before[i]==0xA5 && input.after[i]==0xA5);
}
static void draw(unsigned char key){
    af_apology_editor_key_draw(&ed,&key,1,13.5f,27.0f,1,2,3,255,0,0,0.875f,0.875f,0);
}
int main(void){
    int count,kind;short x,y;
    const unsigned char sun[10]={'U',' ','R',' ','m','y',' ',0x80,0xA7,'!'};
    const unsigned char skull[10]={'R','e','s','e','t',' ','=',' ',0x80,0xBA};
    const char *p;
    fresh(3);ed.prefix[4]=1;
    draw(0x84);assert(draw_len==2 && draw_text[0]==0x80 && draw_text[1]==0xA7);
    draw(0x81);assert(draw_len==2 && draw_text[0]==0x80 && draw_text[1]==0xBA);
    draw(0x85);assert(draw_len==1 && draw_text[0]=='=');
    draw('!');assert(draw_len==1 && draw_text[0]=='!');
    ed.prefix[4]=3;draw(0x84);assert(draw_len==1 && draw_text[0]==0x84);
    for(p="U R my ";*p;++p){command(AF_APOLOGY_INSERT,*p);assert(ed.processed==1);}
    ed.prefix[4]=1;command(AF_APOLOGY_INSERT,0x84);
    assert(ed.length==9 && ed.index==9 && input.text[7]==0x80 && input.text[8]==0xA7);
    count=exchange_calls;assert(af_apology_editor_exchange(&ed)==-1 && exchange_calls==count);
    ed.exchange='x';command(AF_APOLOGY_EXCHANGE,0);assert(ed.processed==0 && input.text[8]==0xA7);
    command(AF_APOLOGY_INSERT,'!');assert(!memcmp(input.text,sun,10));
    command(AF_APOLOGY_INSERT,'?');assert(ed.processed==0 && !memcmp(input.text,sun,10));
    af_apology_editor_cursor(&ed,&x,&y,10);assert(x==10 && y==0);
    af_apology_editor_cursor(&ed,&x,&y,8);assert(x==0 && y==0);
    count=done_calls;command(AF_APOLOGY_DONE,0);assert(done_calls==count+1);
    command(AF_APOLOGY_LEFT,0);assert(ed.index==9);
    command(AF_APOLOGY_BACKSPACE,0);assert(ed.index==7 && ed.length==8 && input.text[7]=='!');
    ed.index=ed.length;command(AF_APOLOGY_RIGHT,0);
    assert(ed.command==AF_APOLOGY_INSERT && ed.code==' ' && ed.length==9);

    fresh(3);ed.prefix[4]=1;
    for(p="Reset ";*p;++p)command(AF_APOLOGY_INSERT,*p);
    command(AF_APOLOGY_INSERT,0x85);command(AF_APOLOGY_INSERT,' ');command(AF_APOLOGY_INSERT,0x81);
    assert(ed.length==10 && !memcmp(input.text,skull,10));
    count=done_calls;ed.index=9;command(AF_APOLOGY_DONE,0);assert(done_calls==count && ed.processed==0);
    count=exchange_calls;assert(af_apology_editor_exchange(&ed)==-1 && exchange_calls==count);
    ed.index=10;ed.columns=6;command(AF_APOLOGY_BACKSPACE,0);assert(!memcmp(input.text,skull,10));
    ed.columns=10;*(int *)(storage.bytes+0x101E0)=4;
    command(AF_APOLOGY_BACKSPACE,0);assert(!memcmp(input.text,skull,10));

    /* Identical keyboard keys and handlers stay native outside apology kind. */
    for(kind=0;kind<5;++kind){
        if(kind==3)continue;
        fresh(kind);ed.prefix[4]=1;draw(0x84);assert(draw_len==1 && draw_text[0]==0x84);
        count=done_calls;command(AF_APOLOGY_INSERT,0x84);assert(done_calls==count+1 && ed.length==0);
        count=exchange_calls;assert(af_apology_editor_exchange(&ed)=='A' && exchange_calls==count+1);
        count=cursor_calls;af_apology_editor_cursor(&ed,&x,&y,4);assert(cursor_calls==count+1 && y==9);
    }
    fresh(3);count=destruct_calls;af_apology_editor_destruct(&submenu);assert(destruct_calls==count+1);
    ed.prefix[4]=1;draw(0x81);assert(draw_len==1 && draw_text[0]==0x81);
    count=done_calls;command(AF_APOLOGY_INSERT,'x');assert(done_calls==count+1);
    assert(init_calls==7 && draw_calls==10);
    return 0;
}
