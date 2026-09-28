#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/diary_menu.h"
#include "../overlays/v3/diary_room.h"

static AFDiary live,scratch,unchanged;
static AFDiaryMenu menu;
static unsigned char widths[256];
static int reject,calls;
static int capacity(void *context,const AFDiary *candidate) {
    assert(context==&calls);calls++;
    assert(af_diary_valid(candidate));return reject?-1:1;
}
static unsigned int event_count(void *context,AFDiaryDate day,unsigned int owner) {
    assert(context==&calls);assert(owner<4);return day.day==15?3:0;
}
static AFDiaryMenuAccess access={&live,&scratch,widths,capacity,&calls,event_count};
static AFDiaryDates dates={23,9,29};
static AFDiaryDate today={2026,9,15};
static void button(unsigned int key) {assert(af_diary_menu_input(&menu,&access,key,0,0)>=0);}
static void open_diary(int viewer,int owner) {
    assert(af_diary_menu_open(&menu,&access,viewer,owner,today,dates)==1);
    button(AF_DIARY_A);assert(menu.state==AF_DIARY_DAY);
    button(AF_DIARY_A);
}
static void menu_flow(void) {
    memset(widths,6,sizeof(widths));widths['i']=3;widths['W']=10;
    af_diary_reset(&live);
    for(unsigned int p=0;p<4;p++) {
        open_diary(p,p);assert(menu.state==AF_DIARY_READ);
        button(AF_DIARY_START);assert(menu.state==AF_DIARY_EDIT);
        assert(af_diary_menu_edit(&menu,&access,8,'A'+p)==1);
        assert(af_diary_menu_edit(&menu,&access,8,0xCD)==1);
        assert(af_diary_menu_edit(&menu,&access,8,'i')==1);
        assert(af_diary_menu_edit(&menu,&access,5,0)==1);
        button(AF_DIARY_DOWN);button(AF_DIARY_A);assert(menu.state==AF_DIARY_EDIT);
        assert(menu.draft.cursor==3 && menu.draft.text[0]=='A'+p);
        assert(af_diary_menu_edit(&menu,&access,5,0)==1);
        button(AF_DIARY_B);assert(menu.state==AF_DIARY_EDIT);
        assert(af_diary_menu_edit(&menu,&access,5,0)==1);
        button(AF_DIARY_START);assert(menu.state==AF_DIARY_PRIVACY);
        button(AF_DIARY_RIGHT);button(AF_DIARY_B);assert(menu.state==AF_DIARY_PRIVACY);
        unchanged=live;reject=1;int before=calls;
        assert(af_diary_menu_input(&menu,&access,AF_DIARY_A,0,0)==AF_DIARY_CAPACITY);
        assert(calls==before+1 && menu.state==AF_DIARY_ERROR);
        assert(!memcmp(&live,&unchanged,sizeof(live)));
        assert(menu.draft.text[0]=='A'+p && menu.draft.original[0]==' ');
        button(AF_DIARY_B);assert(menu.state==AF_DIARY_EDIT && menu.draft.cursor==3);
        reject=0;assert(af_diary_menu_edit(&menu,&access,5,0)==1);
        button(AF_DIARY_A);button(AF_DIARY_RIGHT);button(AF_DIARY_A);
        assert(menu.state==AF_DIARY_DAY);
        assert(af_diary_page(&live,p,p,8)[0]=='A'+p);
        open_diary((p+1)%4,p);assert(menu.state==AF_DIARY_WARNING);
        button(AF_DIARY_A);assert(menu.state==AF_DIARY_DAY);
        assert(af_diary_lock(&live,p,p,0)==1);
        button(AF_DIARY_A);assert(menu.state==AF_DIARY_READ && menu.draft.readonly);
        assert(af_diary_menu_edit(&menu,&access,8,'!')<0);
        button(AF_DIARY_START);assert(menu.state==AF_DIARY_DAY);
    }
    assert(af_diary_menu_open(&menu,&access,0,0,today,dates)==1);
    for(int i=0;i<11;i++)assert(af_diary_menu_input(&menu,&access,0,-1,0)==1);
    assert(menu.selected.year==2025 && menu.selected.month==10);
    assert(af_diary_menu_input(&menu,&access,0,-1,0)==0);
    button(AF_DIARY_UP);assert(!menu.month_delta && menu.selected.month==9);
    for(int i=0;i<11;i++)assert(af_diary_menu_input(&menu,&access,0,1,0)==1);
    assert(menu.selected.year==2027 && menu.selected.month==8);
    assert(af_diary_menu_input(&menu,&access,0,1,0)==0);
    button(AF_DIARY_UP);button(AF_DIARY_A);assert(menu.selected.day==15 && menu.events==3);
    button(AF_DIARY_DOWN);button(AF_DIARY_DOWN);assert(menu.selected.day==15 && menu.event_index==2);
    button(AF_DIARY_DOWN);assert(menu.selected.day==22 && !menu.event_index);
    button(AF_DIARY_UP);assert(menu.selected.day==15);
    button(AF_DIARY_LEFT);assert(menu.selected.day==14);
    button(AF_DIARY_UP);assert(menu.selected.day==7);
    button(AF_DIARY_UP);assert(menu.selected.day==7);
    unsigned char days[37],marks[37];
    assert(af_diary_menu_grid(&menu,&live,dates,days,marks)==1);
    assert(days[0]==0 && days[1]==0 && days[2]==1 && days[31]==30 && days[32]==0);
    assert(marks[16]==1);button(AF_DIARY_B);button(AF_DIARY_START);assert(menu.state==AF_DIARY_CLOSED);
    /* Owner refresh must not erase the visitor's calendar on a stale house. */
    af_diary_reset(&live);assert(af_diary_calendar_visit(&live,1,today,dates)==1);
    assert(af_diary_menu_open(&menu,&access,1,2,today,dates)==1);
    assert(af_diary_calendar_mark(&live,1,today,today,dates)==1);
}

RoomCarryNative af_test_carry_native;
RoomCarryProfile *af_test_carry_profiles[AF_V3_FURNITURE_CAPACITY];
RoomCarryWork af_test_carry_work;
const u8 *af_test_diary_layers;
u8 *af_test_diary_houses;
RoomGoodsOverlay *af_test_diary_owner_overlay;
static RoomRig actors[2];
static unsigned char used[2]={1,1},layers[AF_V3_FURNITURE_CAPACITY],house_data[4*0xB48];
static unsigned short foreground[256],selected,field;
static RoomCarryProfile profile;
static unsigned char player[0x40];
static int held,null_owner,resident,open_result,opened,fallback;
u16 af_diary_native_selected(void) {return selected;}
int af_diary_native_open(void *game,int who) {assert(game==player);assert(who==resident);opened++;return open_result;}
static int original(RoomCarryOwner *actor,void *game,AFDiaryContact *lo,AFDiaryContact *hi) {
    assert(actor && game==player && lo && hi);fallback++;return 9;
}
static u16 *get_fg(s16 layer) {assert(layer==1);return foreground;}
static u8 *get_player(void *game) {assert(game==player);return player;}
static int button_held(u16 key) {assert(key==0x8000);return held;}
static u16 get_field(void) {return field;}
static int is_null(void *id) {assert(id==house_data+(field-0x6000)*0xB48);return null_owner;}
static int get_owner(void *id) {assert(id==house_data+(field-0x6000)*0xB48);return resident;}
void *af_test_diary_resolve(u32 address) {
    switch(address) {
    case 0x8093DB64:return original;case 0x80936A10:return get_fg;
    case 0x800B1C84:return get_player;case 0x80078D30:return button_held;
    case 0x80087C88:return get_field;case 0x800B7914:return is_null;
    case 0x800B7FD4:return get_owner;default:assert(0);return 0;
    }
}
static void room_flow(void) {
    af_test_carry_work=(RoomCarryWork){actors,used,2};
    af_test_diary_layers=layers;af_test_diary_houses=house_data;
    actors[0]=(RoomRig){.index=10,.id=0,.position={100,0,100},.shape_type=4};
    actors[1]=(RoomRig){.index=11,.id=1,.position={100,0,100},.shape_type=4,.layer=1};
    af_test_carry_profiles[10]=af_test_carry_profiles[11]=&profile;layers[10]=1;
    float position[3]={100,0,140};memcpy(player+0x28,position,sizeof(position));
    AFDiaryContact lo={1,0},hi={1,1};
    for(int i=0;i<16;i++) {
        foreground[34]=0x2B00+i;
        assert(af_diary_room_tap(&af_test_carry_work,&lo,&hi,foreground,layers,
            af_test_carry_profiles,AF_V3_FURNITURE_CAPACITY,1u<<i,position)==1);
        assert(!af_diary_room_tap(&af_test_carry_work,&lo,&hi,foreground,layers,
            af_test_carry_profiles,AF_V3_FURNITURE_CAPACITY,(u16)~(1u<<i),position));
    }
    union { void *alignment;unsigned char bytes[0x500]; } owner={0};
    RoomGoodsOverlay overlay={0x82D7F0,0x844400,0x80936710,0x8094F610,(u8 *)&owner};
    RoomCarryOwner *actor=(RoomCarryOwner *)owner.bytes;af_test_diary_owner_overlay=&overlay;
    selected=65535;field=0x6002;resident=3;open_result=1;
    *(s16 *)(owner.bytes+0x174)=1;
    assert(af_diary_room_move(actor,player,&lo,&hi)==1 && opened==1 && !fallback);
    assert(!*(s16 *)(owner.bytes+0x174));
    *(s16 *)(owner.bytes+0x174)=6;held=1;
    assert(af_diary_room_move(actor,player,&lo,&hi)==9 && fallback==1);held=0;
    *(s16 *)(owner.bytes+0x4CC)=7;
    assert(af_diary_room_move(actor,player,&lo,&hi)==9 && fallback==2);
    *(s16 *)(owner.bytes+0x4CC)=0;selected=0;
    assert(af_diary_room_move(actor,player,&lo,&hi)==9 && fallback==3);selected=65535;
    null_owner=1;assert(!af_diary_room_move(actor,player,&lo,&hi) && opened==1);
    null_owner=0;*(s16 *)(owner.bytes+0x174)=1;open_result=0;
    assert(!af_diary_room_move(actor,player,&lo,&hi) && opened==2 && fallback==3);
    lo.id=-1;assert(!af_diary_room_tap(&af_test_carry_work,&lo,&hi,foreground,layers,
        af_test_carry_profiles,AF_V3_FURNITURE_CAPACITY,65535,position));
}
int main(void) {menu_flow();room_flow();puts("Diary calendar/read/edit/privacy and all sixteen surface styles pass");return 0;}
