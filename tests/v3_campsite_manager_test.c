#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/campsite_manager.h"

AfCamper camper;
volatile camp_u32 native_installed=1;
camp_u8 native_event_index[128];
AfCampToday native_today[16];
camp_u32 native_changes;
const camp_u8 selected_furniture[0x14000]={
    [((0x335C-0x3000)/4)*80+2]=0x33,
    [((0x335C-0x3000)/4)*80+3]=0x5C,
    [((0x335C-0x3000)/4)*80+7]=1
};
static AfCamperAlias alias;
static AfCampPlace place;
static camp_u8 saved[40];
static int present,available,registered,register_ok,choose_ok,place_ok,remove_ok;
static int valid,field_id,keep,choices,allocations,placements,removals;
#define status native_today[0].status
static camp_u16 foreground;
static int manager;
static AfCampControl control={.type=70};

int native_field_valid(void) { return valid; }
camp_u16 native_field_id(void) { return field_id; }
camp_u8 *native_get_save(int event,int area) { assert(event==70 && !area);return present?saved:0; }
camp_u8 *native_reserve_save(int event,int area) {
    assert(event==70 && !area);++allocations;if(!available)return 0;present=1;return saved;
}
int native_clear_save(int event,int area) { assert(event==70 && !area);present=0;return 40; }
int native_check_keep(int event) { assert(event==70);return keep; }
void native_set_keep(int event) { assert(event==70);keep=1; }
void native_clear_keep(int event) { assert(event==70);keep=0; }
void native_set_status(int event,int flag) {
    assert(event==70);if(flag==0x20)status=0;status|=flag;native_changes|=flag;
}
void native_clear_status(int event,int flag) { assert(event==70);status&=~flag; }
AfCamperAlias *native_event(camp_u32 event) { assert(event==0xD08F);return registered?&alias:0; }
int af_v3_camper_register(camp_u32 mask,camp_u32 npc,camp_u32 cloth) {
    assert(mask==0xD08F && npc==0xE0ED && !cloth);
    if(!register_ok)return 0;
    registered=1;return 1;
}
void native_reset_appeared(void) { ++choices; }
void native_shuffle(int *p,int n,int swaps) { int i;assert(n==6 && swaps==236);for(i=0;i<n;++i)p[i]=i; }
int native_unseen(camp_u32 p) { return choose_ok && p==3; }
int native_grow(camp_u32 p) { assert(p==3);return 237; }
int selected_villager(int i) { return i==237; }
void native_mark_appeared(camp_u32 npc) { assert(npc==0xE0ED); }
AfCampPlace *native_get_place(int event,int area) { assert(event==70 && area==0x51);return placements?&place:0; }
int native_get_fg(camp_u16 *out,int x,int z,int ux,int uz) {
    assert(x==1 && z==1 && ux==8 && uz==8);*out=foreground;return 1;
}
AfCampPlace *native_place_tent(void *m,AfCampControl *c,camp_u16 item,camp_u8 area) {
    assert(m==&manager && c==&control && item==0x5849 && area==0x51);++placements;
    if(!place_ok){native_set_status(70,0x20);return 0;}
    foreground=0x5849;return &place;
}
int native_remove_tent(AfCampControl *c,camp_u8 area) {
    assert(c==&control && area==0x51);++removals;
    if(!remove_ok){native_set_status(70,0x20);return 0;}
    foreground=0;return 1;
}
static int start(void) { return af_v3_camper_event_start(&manager,&control); }
static void reset(void) {
    memset(&camper,0,sizeof(camper));memset(saved,0,sizeof(saved));
    camper.greeted=1;place=(AfCampPlace){1,1,8,8,0x5849,0};
    present=registered=field_id=keep=status=choices=allocations=placements=removals=foreground=0;
    memset(native_event_index,255,sizeof(native_event_index));native_event_index[70]=0;
    native_today[0].type=70;native_changes=0x84;
    native_installed=available=register_ok=choose_ok=place_ok=remove_ok=valid=1;
}
int main(void) {
    reset();assert(start()==1 && keep && registered && present && !status);
    assert(saved[0]==0xE0 && saved[1]==0xED && !camper.greeted && choices==1 && placements==1);
    camper.greeted=1;assert(start()==2 && camper.greeted && choices==1 && placements==1);
    foreground=0xF127;assert(start()==2 && placements==1);
    status=0x91;remove_ok=0;assert(!af_v3_camper_event_stop(&manager,&control) && keep && status==0x91 && native_changes==0x84);
    status=0;
    remove_ok=1;assert(af_v3_camper_event_stop(&manager,&control)==1 && !keep && !status && registered);
    assert(af_v3_camper_event_stop(&manager,&control)==2);
    reset();available=0;assert(!start() && !keep && !registered && !present && !status);
    available=1;assert(start()==1 && choices==1 && !status);
    reset();choose_ok=0;assert(!start() && !present && !registered && !keep && camper.greeted);
    choose_ok=1;assert(start()==1 && choices==2);
    reset();register_ok=0;assert(!start() && present && !keep && !placements && choices==1);
    register_ok=1;assert(start()==1 && choices==1);
    reset();status=0x81;place_ok=0;assert(!start() && registered && present && !keep && status==0x81 && native_changes==0x84);
    place_ok=1;assert(start()==1 && choices==1 && placements==2 && status==0x81);
    reset();field_id=0x3012;assert(start()==1 && registered && !placements);
    field_id=0;assert(start()==2 && placements==1);
    reset();valid=0;assert(!start() && !allocations && !placements);
    reset();registered=1;assert(!start() && !allocations && !choices && camper.greeted);
    reset();native_installed=0;assert(!start() && !allocations && !status);
    reset();native_event_index[70]=16;assert(!start() && !allocations);
    assert(!af_v3_camper_event_start(&manager,0));
    assert(af_v3_camper_event_in(&manager,&control)==1 && af_v3_camper_event_out(&manager,&control)==1);
    control.type=14;assert(!start() && !af_v3_camper_event_stop(&manager,&control));
    assert(!af_v3_camper_event_in(&manager,&control) && !af_v3_camper_event_out(&manager,&control));
    puts("pass: saved selection, indoor/outdoor lifecycle, registration and placement retries, and retained state");
    return 0;
}
