#include <assert.h>
#include <stddef.h>
#include <string.h>
#include "editor.h"

const unsigned short af_grid_tables[240]={
    [0]='!', [10]='q', [80]='1', [90]='Q', [91]='W', [109]=0xCD,
    [214]=AF_GRID_SKULL, [220]=AF_GRID_SUN
};
static union {max_align_t align;unsigned char bytes[0x10700];} storage;
static union {max_align_t align;unsigned char bytes[0x50];} menu;
static struct af_hboard_submenu_pointer submenu;
static struct af_hboard_native_editor ed;
static unsigned char input[128],snapshot[128];
static unsigned short held,pressed;
static int joyx,joyy,inits,destructs;

unsigned short af_grid_get_button(void){return held;}
unsigned short af_grid_get_trigger(void){return pressed;}
int af_grid_get_x(void){return joyx;}
int af_grid_get_y(void){return joyy;}
void af_apology_editor_init(void *s,void *m){assert(s==&submenu && m==menu.bytes);++inits;}
void af_apology_editor_destruct(void *s){assert(s==&submenu);++destructs;}

static void fresh(int rows,int kind){
    memset(&storage,0,sizeof(storage));memset(&menu,0,sizeof(menu));memset(&ed,0,sizeof(ed));
    memset(input,0xA5,sizeof(input));memcpy(snapshot,input,sizeof(input));
    submenu.overlay=storage.bytes;
    *(struct af_hboard_native_editor **)(storage.bytes+0x106E0)=&ed;
    *(unsigned char **)(storage.bytes+0x101E8)=input;
    *(int *)(storage.bytes+0x101E0)=kind;
    *(int *)(menu.bytes+0x38)=3;
    ed.input=input;ed.columns=10;ed.rows=(short)rows;ed.index=4;ed.length=6;ed.exchange='A';
    ed.column=4;ed.row=0;ed.prefix[12]=5;
    held=pressed=0;joyx=joyy=0;
    af_grid_editor_init(&submenu,menu.bytes);
    assert(af_grid_owned(&submenu) && af_grid_context.state.upper==1);
    assert(ed.prefix[0]==8 && ed.prefix[1]==8 && ed.prefix[3]==0 && ed.prefix[6]==255 && ed.prefix[7]==255);
    assert(ed.prefix[12]==5);
}
static void step(unsigned short h,unsigned short p){
    held=h;pressed=p;af_grid_editor_prepare(&submenu);af_grid_editor_input(&submenu);
    assert(!memcmp(snapshot,input,sizeof(input)));
    assert(ed.index==4 && ed.length==6 && ed.column==4 && ed.row==0 && ed.exchange=='A');
}
int main(void){
    fresh(1,0);
    step(0x8000,0x8000);assert(ed.command==AF_GRID_INSERT && ed.code=='1');
    step(0x8000,0);assert(ed.command==AF_GRID_NONE);
    step(0x400,0x400);assert(af_grid_context.state.row==1);
    step(0x8000,0x8000);assert(ed.code=='Q' && ed.prefix[4]==3);
    step(0x20,0x20);step(0x8000,0x8000);assert(ed.code=='q');
    step(0x8020,0x8000);assert(ed.command==AF_GRID_EXCHANGE && ed.exchange=='A');
    step(0x4000,0x4000);assert(ed.command==AF_GRID_BACKSPACE);
    step(0x1000,0x1000);assert(ed.command==AF_GRID_DONE);
    af_grid_context.state.upper=1;af_grid_context.state.row=2;af_grid_context.state.column=9;
    step(0x8000,0x8000);assert(ed.command==AF_GRID_NONE);
    ed.rows=4;step(0x8000,0x8000);assert(ed.command==AF_GRID_INSERT && ed.code==0xCD);

    fresh(1,3);assert(af_grid_apology(&submenu));
    af_grid_context.state.page=2;af_grid_context.state.row=2;
    step(0x8000,0x8000);assert(ed.command==AF_GRID_INSERT && ed.code==0x84 && ed.prefix[4]==1);
    af_grid_context.state.row=1;af_grid_context.state.column=4;
    step(0x8000,0x8000);assert(ed.command==AF_GRID_INSERT && ed.code==0x81 && ed.prefix[4]==1);
    *(int *)(storage.bytes+0x101E0)=0;
    step(0x8000,0x8000);assert(ed.command==AF_GRID_NONE && ed.prefix[4]==3);
    ed.input=input+1;step(0x8000,0x8000);assert(ed.command==AF_GRID_NONE && af_grid_context.error==1);
    af_grid_editor_destruct(&submenu);assert(destructs==1 && !af_grid_owned(&submenu));
    af_grid_editor_input(&submenu);assert(ed.command==AF_GRID_NONE);
    assert(inits==2);
    return 0;
}
