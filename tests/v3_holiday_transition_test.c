/* Run complete generated donor functions through real adapter code and native
 * geometry I/O doubles. This does not execute a cartridge or verify pixels. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_transition.h"
#include "holiday-transition-data.h"
static unsigned int active[128],go_calls,geometry_calls,order_count;
static int unresolved,blocked,gate_ok,go_ok=1,correct_position,status_missing;
static char order[8];
static AFHolidayDoor requested;
static int original_priority=-1,original_result=2,original_calls;
static int original_rank(void *c) {(void)c;return original_priority;}
static int original_collision(void *c,int x,int z) {
    (void)c;assert(x==7 && z==7);original_calls++;return original_result;
}
static int event_status(void *c,unsigned int donor,unsigned int mask) {
    (void)c;assert(donor<128 && mask==AF_HE_ACTIVE);return status_missing?-1:(int)(active[donor]&mask);
}
static int resolve(void *c,unsigned int source) {
    (void)c;assert((source>>12)==AF_HT_SOURCE_STRUCTURE);return unresolved?-1:(int)(0x5000|(source&4095));
}
int af_holiday_transition_grid(int *bx,int *bz,int *ux,int *uz,AFHolidayPosition p) {
    geometry_calls++;*bx=(int)(p.x/640);*bz=(int)(p.z/640);
    *ux=(int)(p.x/40)&15;*uz=(int)(p.z/40)&15;return 1;
}
void af_holiday_transition_position(AFHolidayPosition *p,int bx,int bz,int ux,int uz) {
    geometry_calls++;*p=(AFHolidayPosition){bx*640+ux*40+20,0,bz*640+uz*40+20};
}
int af_holiday_transition_origin(float *x,float *z,int bx,int bz) {
    geometry_calls++;*x=bx*640;*z=bz*640;return 1;
}
int af_holiday_transition_area(int x,int z,unsigned short name,int ux,int uz) {
    geometry_calls++;assert((name>>12)==5);return x>=ux && x<=ux+1 && z>=uz && z<=uz+1;
}
int af_holiday_transition_landmark(int *x,int *z,unsigned int kind) {
    geometry_calls++;assert(kind==4 || kind==8);*x=2;*z=2;return 1;
}
int af_holiday_transition_police(int bx,int bz,int ux,int uz) {
    geometry_calls++;return bx==2 && bz==2 && ux==3 && uz==3;
}
int af_holiday_transition_space(int bx,int bz,int ux,int uz) {
    geometry_calls++;assert(bx>=0 && bz>=0 && ux>=0 && ux<16 && uz>=0 && uz<16);return !blocked;
}
int af_holiday_transition_gate(int *x,int *z,int bx,int bz,int ux,int uz) {
    geometry_calls++;(void)bx;(void)bz;(void)ux;(void)uz;*x=14;*z=14;return gate_ok;
}
static int go(void *c,AFHolidayTransition *s,const AFHolidayDoor *d,int flag) {
    (void)c;assert(!flag && (s->common.start_demo_request.type==13 || s->common.start_demo_request.type==14));
    requested=*d;go_calls++;order[order_count++]='G';return go_ok;
}
static void climate(void *c,int value) {(void)c;assert(value==6);order[order_count++]='C';}
static void tempo(void *c) {(void)c;order[order_count++]='T';}
static void warp(void *c,AFHolidayTransition *s) {
    (void)c;assert(s->skip_event_at_wade && s->common.event_door_data.next_scene_id==s->scene_no);
    assert(s->common.event_door_data.door_actor_name==65535 && s->common.event_door_data.wipe_type==6);
    assert(s->play.fb_fade_type==11 && s->play.fb_wipe_type==6 && s->common.transition.wipe_type==6);
    assert(!s->common.event_title_fade_in_progress);order[order_count++]='W';
}
static void bgm(void *c) {(void)c;order[order_count++]='B';}
static int correct(void *c) {(void)c;return correct_position;}
static AFHolidayTransition fresh(AFHolidayTransitionOps *ops) {
    AFHolidayTransition s={0};s.ops=ops;s.maps=maps;s.map_bytes=sizeof(maps);
    s.player_ok=1;s.scene_no=31;s.common.event_title_fade_in_progress=1;
    s.pool_block=(AFHolidayBlock){3,4};s.shrine_block=(AFHolidayBlock){2,2};
    s.station_block=(AFHolidayBlock){1,3};s.player_home_block=(AFHolidayBlock){4,3};
    s.player.world.position=(AFHolidayPosition){1340,100,1340};s.player.world.angle.y=0x4000;
    s.common.door_data.exit_position=(AFHolidayShortPosition){200,300,400};
    s.common.door_data.exit_orientation=5;return s;
}
/* Real native scene adapter against explicitly laid-out native memory and
 * external I/O doubles. The complete generated fade is unchanged. */
_Alignas(8) unsigned char af_holiday_transition_common[0xAB8];
static _Alignas(8) unsigned char native_game[0x2410],native_player[0x40];
static int native_manager[0x248/4];
void *af_holiday_native_game=native_game;
const int af_holiday_transition_scene=31;
static unsigned int native_calls,commit_before,commit_return;
static int native_read_ok=1,alternate=-1,native_groundhog;
int af_holiday_native_type(unsigned int donor) {return donor==20?91:donor==7?78:-1;}
void *af_holiday_transition_player(void *game) {assert(game==native_game);return native_player;}
int af_holiday_transition_demo_busy(void) {return 0;}
int af_holiday_transition_player_ok(void) {return 1;}
int af_holiday_transition_correct(void) {assert(native_calls);return correct_position;}
int af_holiday_transition_goto(void *game,const AFHolidayDoor *door,int flags) {
    assert(game==native_game && !flags && commit_before && !commit_return);
    assert(*(int *)(af_holiday_transition_common+0x780)==(native_groundhog?15:12));
    requested=*door;native_calls++;order[order_count++]='G';
    /* This state changes during goto; the predicate must run after goto. */
    correct_position=1;return go_ok;
}
void af_holiday_transition_warp(void) {assert(commit_return);order[order_count++]='W';}
void af_holiday_transition_bgm(void) {assert(commit_return);order[order_count++]='B';}
static int read_extension(void *c,AFHolidayTransition *s) {
    (void)c;
    assert(s->scene_no==31 && s->player.world.position.x==1340 && s->player.world.angle.y==0x4000);
    assert(s->pool_block.x==4 && s->pool_block.z==3 && s->station_block.x==3 && s->station_block.z==1);
    assert(s->shrine_block.x==2 && s->shrine_block.z==2 && s->player_home_block.x==3 && s->player_home_block.z==4);
    s->groundhog_present=native_groundhog;s->groundhog.fading_title=native_groundhog;
    s->play.block_table.block_x=s->play.block_table.block_z=2;
    return native_read_ok;
}
static void commit_extension(void *c,const AFHolidayTransition *s,unsigned int phase) {
    (void)c;
    if(phase==AF_HT_BEFORE_SCENE) {assert(!commit_before);commit_before++;return;}
    assert(phase==AF_HT_RETURN_STATE && native_calls && !commit_return && !s->common.event_title_fade_in_progress);
    AFHolidayDoor door;memcpy(&door,af_holiday_transition_common+0x78C,sizeof(door));
    assert(door.next_scene_id==31 && door.exit_position.x==200 && door.exit_position.z==400);
    assert(door.exit_orientation==5 && door.door_actor_name==65535 && door.wipe_type==6);
    assert(native_manager[0x244/4]==1 && native_game[0x1EE0]==11 && native_game[0x1EE1]==6);
    assert(af_holiday_transition_common[0x14B]==6);
    assert(*(short *)(af_holiday_transition_common+0x7E2)==(native_groundhog?78:91));
    assert(*(short *)(af_holiday_transition_common+0x7E4)==1);commit_return++;
}
static int alternate_demo(void *c) {(void)c;return alternate;}
static void native_tempo(void *c) {assert(commit_return);tempo(c);}
static void native_fresh(void) {
    memset(af_holiday_transition_common,0,sizeof(af_holiday_transition_common));
    memset(native_game,0,sizeof(native_game));memset(native_manager,0,sizeof(native_manager));
    AFHolidayPosition p={1340,100,1340};AFHolidayShortPosition angle={0,0x4000,0};
    memcpy(native_player+0x28,&p,sizeof(p));memcpy(native_player+0x34,&angle,sizeof(angle));
    const int blocks[]={3,4,1,1,3,1,2,2,1,4,3,1};memcpy(native_manager+0x214/4,blocks,sizeof(blocks));
    AFHolidayDoor d={.exit_orientation=5,.exit_position={200,300,400}};
    memcpy(af_holiday_transition_common+0x754,&d,sizeof(d));
    native_calls=commit_before=commit_return=order_count=0;correct_position=0;go_ok=1;
}
static void native_scene_check(void) {
    AFHolidayTransitionServices services={.maps=maps,.map_bytes=sizeof(maps),
        .status=event_status,.resolve=resolve,.read=read_extension,.commit=commit_extension,
        .alternate_demo=alternate_demo,.climate=climate,.tempo=native_tempo};
    native_fresh();assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==1);
    assert(native_calls==1 && commit_before==1 && commit_return==1 && !memcmp(order,"GCTWB",5));
    services.alternate_demo=0;native_fresh();
    assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==1);
    native_fresh();native_groundhog=1;
    assert(af_holiday_transition_native_fade(&services,native_manager,7,78,1,4)==-1 && !native_calls);
    native_groundhog=0;services.alternate_demo=alternate_demo;
    native_fresh();go_ok=0;
    assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==0);
    assert(native_calls==1 && commit_before==1 && !commit_return && order_count==1);
    assert(!native_manager[0x244/4] && *(int *)(af_holiday_transition_common+0x780)==12);
    native_fresh();native_read_ok=0;
    assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==-1 && !native_calls && !commit_before);
    native_read_ok=1;native_groundhog=1;
    assert(af_holiday_transition_native_fade(&services,native_manager,7,78,1,4)==-1 && !native_calls && !commit_before);
    assert(!*(int *)(af_holiday_transition_common+0x780)); /* No native-demo-13 alias. */
    alternate=13;
    assert(af_holiday_transition_native_fade(&services,native_manager,7,78,1,4)==-1 && !native_calls && !commit_before);
    alternate=15;
    assert(af_holiday_transition_native_fade(&services,native_manager,7,78,1,4)==1 && commit_return);
    native_fresh();native_groundhog=0;
    status_missing=1;
    assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==-1 && !native_calls && !commit_before);
    status_missing=0;
    assert(af_holiday_transition_native_fade(&services,native_manager,20,90,1,4)==-1 && !native_calls);
    services.tempo=0;
    assert(af_holiday_transition_native_fade(&services,native_manager,20,91,1,4)==-1 && !native_calls);
}
int main(void) {
    AFHolidayTransitionOps ops={.status=event_status,.resolve=resolve,.go=go,
        .climate=climate,.tempo=tempo,.warp=warp,.bgm=bgm,.correct=correct};
    assert(af_holiday_transition_native_geometry(&ops));
    AFHolidayTransition s=fresh(&ops);
    for(unsigned int i=0;i<sizeof(expected)/sizeof(expected[0]);i++) {
        const unsigned int *r=expected[i];memset(active,0,sizeof(active));active[r[0]]=1;s.pool_variant=r[1];
        assert(af_holiday_transition_collision(&s,r[2],r[3])==(int)r[4]);
    }
    memset(active,0,sizeof(active));s.pool_variant=0;
    assert(af_holiday_transition_collision(&s,7,7)==0);
    active[49]=active[1]=1;assert(af_holiday_transition_map(&s)==49);
    assert(af_holiday_transition_collision(&s,7,7)==0); /* Active null map masks later layout. */
    memset(active,0,sizeof(active));
    AFHolidayPosition pos={2200,50,920};AFHolidayShortPosition out;
    assert(af_holiday_transition_escape(&s,&out,&pos,4,20)==1); /* Native fixed station obstacle. */
    assert(out.x==2220 && out.z==980 && out.y==0);
    blocked=1;assert(af_holiday_transition_escape(&s,&out,&pos,4,20)==-1);
    gate_ok=1;assert(af_holiday_transition_escape(&s,&out,&pos,4,20)==1);
    assert(out.x==2500 && out.z==1220);blocked=0;gate_ok=0;
    pos=(AFHolidayPosition){2000,60,1900};
    assert(af_holiday_transition_escape(&s,&out,&pos,4,20)==0);
    assert(out.x==2000 && out.y==60 && out.z==1900);
    /* Every source gate prevents the transition, not merely the message. */
    for(int i=0;i<5;i++) {
        s=fresh(&ops);unsigned int calls=go_calls;order_count=0;
        if(i==0)s.demo_busy=1;
        if(i==1)s.player_ok=0;
        if(i==2)s.common.reset_flag=1;
        if(i==3)s.present_busy=1;
        if(i==4)s.common.my_room_message_control_flags=4;
        assert(af_holiday_transition_run(&s,20,1,4)==0 && go_calls==calls && order_count==0);
    }
    s=fresh(&ops);go_ok=0;order_count=0;
    assert(af_holiday_transition_run(&s,20,1,4)==0 && order_count==1 && order[0]=='G');
    assert(s.common.start_demo_request.type==13 && !s.skip_event_at_wade);
    go_ok=1;order_count=0;s=fresh(&ops);
    assert(af_holiday_transition_run(&s,20,1,4)==1 && order_count==5 && !memcmp(order,"GCTWB",5));
    assert(requested.next_scene_id==7 && requested.extra_data==4 && requested.wipe_type==6);
    assert(requested.exit_position.x==2320 && requested.exit_position.y==200 && requested.exit_position.z==850);
    assert(s.common.event_id==20 && s.common.event_title_flags==1);
    assert(s.common.event_door_data.exit_position.x==1340 && s.common.event_door_data.exit_position.y==100);
    assert(s.common.event_door_data.exit_orientation==2);
    s=fresh(&ops);correct_position=1;order_count=0;
    assert(af_holiday_transition_run(&s,64,9,32768)==1);
    assert(s.common.event_door_data.exit_position.x==200 && s.common.event_door_data.exit_position.z==400);
    assert(s.common.event_door_data.exit_orientation==5 && s.common.event_title_flags==9);correct_position=0;
    s=fresh(&ops);s.groundhog_present=1;s.groundhog.fading_title=1;
    s.play.block_table.block_x=s.play.block_table.block_z=2;order_count=0;
    assert(af_holiday_transition_run(&s,7,1,4)==1);
    assert(s.common.start_demo_request.type==14 && requested.extra_data==5 && requested.exit_orientation==4);
    assert(requested.exit_position.x==1600 && requested.exit_position.y==0 && requested.exit_position.z==1800);
    s=fresh(&ops);s.groundhog_save_present=1;s.groundhog_save._00=5;order_count=0;
    assert(af_holiday_transition_run(&s,7,1,4)==1 && !s.groundhog_save._00);
    assert(s.common.start_demo_request.type==13);
    s=fresh(&ops);active[1]=1;unresolved=1;unsigned int calls=go_calls;
    assert(af_holiday_transition_run(&s,1,1,4)==-1 && go_calls==calls && s.failed);
    unresolved=0;memset(active,0,sizeof(active));
    ops.original_rank=original_rank;ops.original_collision=original_collision;
    active[64]=1;original_priority=11; /* Native moons precede imported countdown. */
    assert(af_holiday_transition_map(&s)==AF_HT_ORIGINAL_LAYOUT);
    assert(af_holiday_transition_collision(&s,7,7)==2 && original_calls==1);
    active[20]=1;assert(af_holiday_transition_map(&s)==20); /* Earlier source layout wins. */
    memset(active,0,sizeof(active));active[1]=1;original_priority=6;original_result=0;
    assert(af_holiday_transition_collision(&s,7,7)==0 && original_calls==2); /* Native null masks later maps. */
    original_priority=17;assert(af_holiday_transition_collision(&s,7,7)==-1);
    original_priority=-1;ops.original_rank=0;ops.original_collision=0;
    memset(active,0,sizeof(active));ops.tempo=0;
    assert(af_holiday_transition_run(&s,20,1,4)==-1 && go_calls==calls);
    assert(geometry_calls);
    native_scene_check();
    puts("Complete source collision/search/fade and native scene adapters pass: ACTIVE/null priority, every layout position, escape/fallback, all gates, native request/return-state order, post-goto player predicate, Groundhog branches, and rejected incomplete providers. Native I/O is doubled.");
}
