#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/holiday_fishing_angler.h"
AFHFLive af_hf_live;
AFHFPerson af_hf_controller_person;
AFHFTime af_hf_controller_clock;
AFHFClipState af_hf_clip_state;
const AFHFClip *af_hf_native_clip;
const AFHFTime af_hf_native_clock={0,0,12,7,0,6,2026};
const AFHFB af_hf_native_players[4][0xBD0]={
    {'A','l','e','x',' ',' ','T','o','w','n',' ',' ',0,1,0,2}};
const AFHFB *af_hf_native_player=af_hf_native_players[0];
#define EMPTY {[0x4E1]=255,[0x4E2]=255}
const AFHFB af_hf_native_animals[15][0x528]={
    {0xE0,5},EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY,EMPTY};
static AFHFB wire[AF_HF_BYTES],event[32],field[3][16];
static int missing,fail_name,calls,halted,last_message,fallback_number;
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
void af_fishing_native_set(void *w,int s,const AFHFB *p,int n) {af_hf_native_string(w,s,p,n);}
void af_hf_native_continue(void *w,int n) {assert(w==field);last_message=n;}
void af_hf_native_start_message(int n) {last_message=n;}
int af_hf_native_message_number(void *w) {assert(w==field);return last_message;}
int af_hf_native_number(AFHFB *p,int n,int unit) {
    (void)p;assert(n==88 && unit==0x29E);fallback_number++;return 5;
}
void af_hf_native_halt(void) {halted++;}
static int source_message(AFHFH item) {
    if(item==0x2301)return af_hf_live_message(0x10F7);
    if(item==0x2305)return af_hf_live_message(0x1112);
    return af_hf_live_message(0x10F2);
}
static void source_random_top(void) {
    assert(af_hf_live.active && af_hf_controller_clock.hour==12);
    af_hf_live.event.size=af_hf_live_npc_size(12);
}
const AFHFClip af_hf_source_clip={source_message,source_random_top,af_hf_live_topname,af_hf_live_size};
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

    /* A winner from an existing save keeps its native key while displaying the
       same complete English name recovered by the accepted V2 reader. */
    af_holiday_fish_wire_reset(wire);memset(event,0,26);event[3]=65;
    memcpy(event+4,af_fishing_aliases+64,6);
    const AFHFB town[6]={0x98,0xA6,0x8F,0xA1,32,32};memcpy(event+10,town,6);
    memset(event+16,255,4);memcpy(old_event,event,32);
    assert(af_hf_live_enter());af_hf_live_topname();
    assert(!memcmp(field[0],af_fishing_aliases+64+8,8));af_hf_live_leave();
    assert(!memcmp(event,old_event,32));

    /* Ordinary N64 calls remain ordinary until the imported stall owns the
       actual native clip. Source callbacks here double only the engine seam. */
    af_hf_angler_continue(field,0x10E8);assert(last_message==0x10E8);
    assert(af_hf_angler_number(number,88,0x29E)==5 && fallback_number==1);
    const AFHFClip *previous=&af_hf_source_clip;af_hf_native_clip=previous;
    int owner,other;
    assert(af_hf_clip_lifecycle(&owner,0));assert(!af_hf_clip_lifecycle(&other,0));
    assert(af_hf_native_clip==&af_hf_bridge_clip);
    assert(af_hf_native_clip->message(0x2301)==0x10F7);
    assert(af_hf_native_clip->message(0x2328)==af_hf_live_message(0x10F7));
    for(int delta=0;delta<3;delta++) {
        int value=af_hf_native_clip->message(0x2305)+delta;
        af_hf_angler_continue(field,value);assert(last_message==af_hf_live_message(0x1112+delta));
    }
    af_hf_angler_continue(field,0x10F7);assert(last_message==0x10F7);
    af_hf_angler_start_message(0x10E8);assert(last_message==af_hf_live_message(0x10E8));
    af_hf_angler_continue(field,0x1110);assert(af_hf_angler_message_number(field)==0x1110);
    event[3]=67;AFHFNativePerson key;memcpy(&key,af_hf_native_player,16);
    af_hf_angler_winner(key);assert(!memcmp(event+4,af_hf_native_player,16));
    assert(af_hf_live_enter());int found=0;
    for(unsigned int i=0;i<5;i++)if(af_hf_live.records.fishRecord[i].size==67 &&
        af_hf_live.records.fishRecord[i].pid.player_id==1)found++;
    assert(found==1);af_hf_live_leave();
    af_hf_native_clip->topname();assert(!memcmp(field[0],"Alex    ",8));
    af_holiday_fish_wire_reset(wire);wire[5]=AF_HF_INCHES;memset(event,0,26);
    assert(af_hf_native_clip->size(2)==21);
    assert(af_hf_angler_number(number,21,0x29E)==9 && !memcmp(number,"21 inches",9));
    af_hf_native_clip->random_top();assert(event[3]>0 && event[3]<=27);
    assert(!halted);missing=1;assert(af_hf_native_clip->size(2)==-1 && halted==1);missing=0;
    assert(!af_hf_clip_lifecycle(&other,1));assert(af_hf_clip_lifecycle(&owner,1));
    assert(af_hf_native_clip==previous && !af_hf_clip_state.owner);
    assert(af_hf_clip_lifecycle(&owner,0));af_hf_native_clip=0;
    assert(af_hf_clip_lifecycle(&owner,1) && !af_hf_native_clip);
    puts("Fishing host bridge: names, legacy keys, both units, winner capture, dialogue, clip lifetime, and native fallback pass");
    return 0;
}
