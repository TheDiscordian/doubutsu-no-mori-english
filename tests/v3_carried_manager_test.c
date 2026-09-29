/* Execute the complete prepared source callbacks against real quest-state
 * services. Native placement/player inventory are explicit test doubles. */
#define main retained_state_tests
#define fqrand af_test_calendar_random
#include "v3_carried_quest_test.c"
#undef fqrand
#undef main
#include "../overlays/v3/holiday_owner.h"
extern int af_cw_manager_start(void *,AFHolidayControl *),af_cw_manager_stop(void *,AFHolidayControl *);
extern int af_cw_manager_in(void *,AFHolidayControl *),af_cw_manager_out(void *,AFHolidayControl *);
const volatile u8 af_cw_native_player=2;
static unsigned short pockets[16];
static u8 conditions[16];
static AFHolidayPlace place;
static int make_calls,show_calls,show_result=1,stopped,draws;
void *af_cw_native_private(void){return pockets;}
float fqrand(void){
    /* Include a duplicate pair; the source must reroll, not duplicate acres. */
    static const float sequence[]={.01f,.01f,.01f,.01f,.25f,.25f,.45f,.50f,.65f,.75f,.85f,.01f};
    return sequence[draws++%12];
}
int af_holiday_native_check_status(int type,int flag){CHECK(type==115 && flag==AF_HE_STOP);return stopped;}
AFHolidayPlace *af_holiday_native_get_place(int type,u8 id){CHECK(type==115 && id==0x51);return &place;}
int af_holiday_placement_native_free(void *m,unsigned type,unsigned name,unsigned id,int adjust,int seed,AFHolidayPlace **out){
    CHECK(m==&place && type==115 && name==0xD0CD && id==0x51 && adjust==5 && seed==114+0xD06F+0x51);
    make_calls++;*out=&place;return 1;
}
int af_holiday_placement_native_show_type(void *m,unsigned type,unsigned id,AFHolidayBlock *forward){
    CHECK(m==&place && type==115 && id==0x51);show_calls++;*forward=(AFHolidayBlock){3,4};return show_result;
}
int mPr_GetPossessionItemIdxWithCond(void *p,unsigned short item,int condition){
    CHECK(p==pockets && !condition);
    for(int i=0;i<16;i++)if(pockets[i]==item && !conditions[i])return i;
    return -1;
}
void mPr_SetPossessionItem(void *p,int index,unsigned short item,int condition){
    CHECK(p==pockets && index>=0 && index<16 && !item && !condition);
    pockets[index]=item;
}
int main(void){
    reset_cards();reset_directory();af_cw_available=1;selected=1;
    CHECK(af_holiday_native_append(115,15,0x0101,0x0C1F)==1);
    AFHolidayControl control={.type=115};
    CHECK(af_cw_manager_start(&place,&control)==1 && make_calls==1 && draws==12);
    AFCarriedQuestCommon *c=&af_cw_state.common;
    CHECK(c->flags==0x8000 && *af_cw_placement()==&place);
    for(int i=0;i<5;i++){
        CHECK(c->x[i]>=1 && c->x[i]<=5 && c->z[i]>=2 && c->z[i]<=5);
        for(int j=0;j<i;j++)CHECK(c->x[i]!=c->x[j] || c->z[i]!=c->z[j]);
    }
    CHECK(af_cw_manager_start(&place,&control)==2 && draws==12 && make_calls==2);
    /* The found flag only resumes a hunt for the current player and date. */
    has_saved=1;unsigned short flags=1u<<2;
    /* The source compares native u16 years. Use the RTC's same representation
     * instead of assuming the host shares the target's endianness. */
    memcpy(saved+2,&flags,2);memcpy(saved+4,af_cw_native_rtc+6,2);saved[6]=5;saved[7]=6;
    CHECK(af_cw_manager_start(&place,&control)==2 && (c->flags&0x4000));
    c->flags&=~0x4000;saved[7]=5;
    CHECK(af_cw_manager_start(&place,&control)==2 && !(c->flags&0x4000));
    flags=0x8000;memcpy(saved+2,&flags,2);int previous=make_calls;
    CHECK(af_cw_manager_start(&place,&control)==2 && make_calls==previous);
    for(int i=0;i<3;i++){show_result=i;CHECK(af_cw_manager_in(&place,&control)==i);}
    CHECK(show_calls==3 && control.block.x==4 && control.block.z==3);
    *af_cw_placement()=0;show_result=1;
    CHECK(af_cw_manager_in(&place,&control)==1); /* debug alias does not own placement */
    CHECK(!af_cw_manager_out(&place,&control));stopped=1;CHECK(af_cw_manager_out(&place,&control)==1);
    for(int i=0;i<10;i++)pockets[i]=0x2D28+i%5;
    pockets[10]=0x2D28;conditions[10]=1;pockets[11]=0x2200;
    CHECK(af_cw_manager_stop(&place,&control)==1 && !*af_cw_placement() && !bound_common);
    for(int i=0;i<10;i++)CHECK(!pockets[i]);
    CHECK(pockets[10]==0x2D28 && pockets[11]==0x2200);
    CHECK(af_cw_manager_stop(&place,&control)==2);
    /* Disabled, unrelated, and absent-manager calls cannot spawn or consume. */
    selected=0;CHECK(!af_cw_manager_start(&place,&control) && !af_cw_manager_stop(&place,&control));
    CHECK(!af_cw_manager_in(&place,&control));selected=1;af_cw_available=0;
    CHECK(!af_cw_manager_start(&place,&control));af_cw_available=1;control.type=114;
    CHECK(!af_cw_manager_start(&place,&control));control.type=115;
    CHECK(!af_cw_manager_start(0,&control));
    puts("Complete source Wisp manager: five unique acres, hunt restore/date checks, returned spirits, all appearance results, stop/cull, protected inventory, and disabled admission pass. Native services are doubled.");
    return 0;
}
