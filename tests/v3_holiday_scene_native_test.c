#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_scene_native.h"
#include "holiday_demo.h"
#include "holiday_scene_climate_source.h"
static unsigned int calls[2],count;
static void capture(unsigned int address) {assert(count<2);calls[count++]=address;}
#define AF_HOLIDAY_SCENE_CALL(at) capture(at)
#include "holiday_scene_native.c"
static _Alignas(8) unsigned char game[0x100],actor[0x4E0];
void *af_hd_game=game;
AFHDDemoState af_hd_state;
const unsigned int af_holiday_scene_room_descriptor[8]={
    0x82D7F0,0x844400,0x80936710,0x8094F610,0x80300000,0x8094756C,0,0};
void **af_holiday_scene_room_clip;
static int variant;
int af_holiday_scene_pool_variant(void) {return variant;}
static int status(void *context,unsigned int type,unsigned int flags) {
    (void)context;(void)type;(void)flags;return 0;
}
static int resolve(void *context,unsigned int name) {(void)context;return (int)name;}
int main(void) {
    const unsigned char map[16]={0};
    AFHolidayTransitionServices services={.maps=map,.map_bytes=sizeof(map),.status=status,.resolve=resolve};
    assert(af_holiday_scene_bind(&services));
    AFHolidayTransition s={0};
    game[0xE4]=3;game[0xE5]=255;af_hd_state.fading_title=1;
    for(variant=0;variant<7;variant++) {
        assert(services.read(0,&s));assert(s.pool_variant==(unsigned int)variant);
        assert(s.play.block_table.block_x==3 && s.play.block_table.block_z==-1);
        assert(s.common.event_title_fade_in_progress==1 && !s.present_busy);
        assert(!s.groundhog_present && !s.groundhog_save_present);
    }
    variant=7;assert(!services.read(0,&s));variant=-1;assert(!services.read(0,&s));variant=0;
    services.tempo(0);assert(!count);
    void *clip[1]={0};af_holiday_scene_room_clip=clip;
    assert(services.read(0,&s));services.tempo(0);assert(!count);
    clip[0]=actor;assert(services.read(0,&s));assert(!s.common.my_room_message_control_flags);
    *(int *)(actor+0x47C)=1;assert(services.read(0,&s));assert(s.common.my_room_message_control_flags==4);
    services.tempo(0);assert(count==2 && calls[0]==0x803040B4 && calls[1]==0x80300788);
    assert(*(int *)(actor+0x47C)==1); /* A read cannot clear another owner's request. */
    s.common.event_title_fade_in_progress=0;
    services.commit(0,&s,AF_HT_BEFORE_SCENE);assert(af_hd_state.fading_title==1);
    services.commit(0,&s,AF_HT_RETURN_STATE);assert(!af_hd_state.fading_title);
    services.climate(0,6);assert(!af_hd_state.fading_title);
    mFI_SetClimate(mFI_CLIMATE_0);
    assert(!mFI_GetClimate() && !mFI_CheckBeforeScenePerpetual());
    mFI_SetClimate(mFI_CLIMATE_NUM);assert(l_mFI_climate==mFI_CLIMATE_2);
    assert(!mFI_GetClimate() && !mFI_CheckBeforeScenePerpetual());
    mFI_ChangeClimate_ForEventNotice();assert(l_mFI_climate==mFI_CLIMATE_4);
    assert(!mFI_GetClimate() && !mFI_CheckBeforeScenePerpetual());
    mFI_ChangeClimate_ForEventNotice();assert(l_mFI_climate==mFI_CLIMATE_0);
    assert(!mFI_GetClimate() && !mFI_CheckBeforeScenePerpetual());
    assert(services.alternate_demo(0)==14);
    af_hd_game=0;assert(!services.read(0,&s));af_hd_game=game;
    services.resolve=0;assert(!af_holiday_scene_bind(&services));
    puts("Live scene services: seven pool shapes, signed acre coordinates, real console request, relocated tempo/gyroid capture, and ordered fade-state commit pass. Native I/O is doubled.");
}
