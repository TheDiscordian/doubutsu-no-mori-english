#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/holiday_fishing_live.h"
AFHFLive af_hf_live;
AFHFPerson af_hf_controller_person;
const AFHFTime af_hf_native_clock={0,0,12,7,0,6,2026};
const AFHFB af_hf_native_players[4][0xBD0]={
    {'A','l','e','x',' ',' ','T','o','w','n',' ',' ',0,1,0,2}};
const AFHFB *af_hf_native_player=af_hf_native_players[0];
#define EMPTY {[0x4E1]=255,[0x4E2]=255}
const AFHFB af_hf_native_animals[15][0x528]={
    {0xE0,5},EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY};
static AFHFB wire[AF_HF_BYTES],event[32],field[3][16];
static int missing,fail_name,calls;
float af_hf_native_random(void) {return 0.5f;}
int af_hf_native_event_npc(AFHFH *out) {*out=0xE005;return 1;}
int af_hf_native_name(AFHFB *out,unsigned int size,unsigned int id) {
    assert(size==8 && id==0xE005);calls++;
    if(fail_name)return 0;
    memcpy(out,"Longname",8);return 1;
}
AFHFB *af_hf_native_event_area(int type,int id) {assert(type==20 && !id);return missing?0:event;}
AFHFB *af_v3_fishing_data(void) {return wire;}
void *af_hf_native_window(void) {return field;}
void af_hf_native_string(void *window,int slot,const AFHFB *data,int n) {
    assert(window==field && slot>=0 && slot<3 && n>=0 && n<=16);
    memset(field[slot],' ',16);memcpy(field[slot],data,(unsigned int)n);
}
int main(void) {
    af_holiday_fish_wire_reset(wire);
    memset(event+26,0xA5,6);assert(af_hf_live_enter());assert(!af_hf_live_enter());
    assert(af_hf_live_event(29,0)==&af_hf_live.event);
    assert(!af_hf_live_event(54,0) && !af_hf_live_event(29,1));
    AFHFB name[8],number[16];af_hf_live_name(name,0xE005);assert(!memcmp(name,"Longname",8));
    af_hf_live_random_name(name);assert(!memcmp(name,"Longname",8) && calls==2);
    AFHFPerson p;af_holiday_fish_native_person(&p,af_hf_native_player);
    assert(af_hf_live.records.services.player_index(0,&p)==0);
    p.player_name[7]='X';assert(af_hf_live.records.services.player_index(0,&p)==-1);
    memcpy(p.player_name,name,8);p.player_id=p.land_id=0xFFFF;
    af_hf_live.event.size=64;af_hf_live.event.person=p;
    af_hf_live.event.position[0]=-80;af_hf_live.event.position[1]=200;
    af_hf_live.event.talk=5;af_hf_live.event.flag=1;
    af_hf_live_record(&p,64);assert(!af_hf_live.failed);
    assert(af_hf_live_number(number,64,0x29E)==5 && !memcmp(number,"64 cm",5));
    af_hf_live_topname();assert(!memcmp(field[0],"Longname",8) && !memcmp(field[1],"64 cm",5));
    af_hf_live_leave();assert(!af_hf_live.active);
    assert(event[3]==64 && !memcmp(event+4,"Longna",6));
    for(int i=26;i<32;i++)assert(event[i]==0xA5);
    assert(af_hf_live_enter());assert(!memcmp(af_hf_live.event.person.player_name,"Longname",8));
    assert(af_hf_live.event.position[0]==-80 && af_hf_live.event.talk==5);
    AFHFB old[AF_HF_BYTES],old_event[32];memcpy(old,wire,sizeof(old));memcpy(old_event,event,32);
    fail_name=1;af_hf_live_name(name,0xE005);assert(af_hf_live.failed);
    af_hf_live.event.size=1;af_hf_live_leave();
    assert(!memcmp(old,wire,sizeof(old)) && !memcmp(old_event,event,32));fail_name=0;
    missing=1;assert(!af_hf_live_enter());missing=0;
    af_holiday_fish_wire_reset(wire);wire[5]=AF_HF_INCHES;memset(event,0,26);
    assert(af_hf_live_enter());assert(af_hf_live_size(0)==9 && af_hf_live_size(2)==21);
    assert(af_hf_live_number(number,21,0x29E)==9 && !memcmp(number,"21 inches",9));
    assert(!af_hf_live_number(number,28,0x29E));af_hf_live_leave();
    assert(af_hf_live_message(0x10E8)==0x3061);
    assert(af_hf_live_message(0x2FB6)==0x3061+73 && af_hf_live_message(-1)==-1);
    puts("Fishing native bridge: full names, event/record persistence, both units, display, and failure preservation pass");
    return 0;
}
