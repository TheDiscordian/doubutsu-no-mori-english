/* Original layouts never masquerade as source event IDs. Imported layouts
 * use the complete source graph and the installed decoration registry. */
#include "holiday_transition.h"
#include "holiday_scene_native.h"
#include "holiday_native.h"
extern const unsigned char af_holiday_transition_maps[1496];
extern int af_holiday_transition_native_map(void);
extern int af_holiday_transition_native_collision(int,int);
extern int af_decor_actor_resolve(unsigned short);
static int status(void *context,unsigned int donor,unsigned int mask) {
    (void)context;
    int type=af_holiday_native_type(donor);
    if(type<0)return 0; /* Original-only events use their actual native layout. */
    unsigned int i=af_holiday_native_index[type];
    if(i==255)return 0;
    if(i>=AF_HN_DAYS || af_holiday_native_days[i].type!=(unsigned int)type)return -1;
    unsigned int value=af_holiday_native_days[i].status;
    return value&AF_HE_ERROR?0:!!(value&mask);
}
static int identity(void *context,unsigned int name) {
    (void)context;
    if(name>>12!=AF_HT_SOURCE_STRUCTURE || name>65535)return -1;
    return af_decor_actor_resolve((unsigned short)name);
}
static int rank(void *context) {
    (void)context;
    /* Complete original order, merged with the source layout order. These
     * are priority positions, NOT identity aliases. In particular both
     * native moon events keep their original pool layouts and native actors. */
    static const unsigned char types[15]={11,12,10,8,7,9,13,3,20,2,16,21,22,6,14};
    static const unsigned char ranks[15]={0,1,2,3,4,5,6,7,8,9,10,11,11,13,14};
    int type=af_holiday_transition_native_map();
    if(type==-1)return -1;
    for(unsigned int i=0;i<15;i++)if(type==types[i])return ranks[i];
    return -2;
}
static int original(void *context,int x,int z) {
    (void)context;return af_holiday_transition_native_collision(x,z);
}
int af_holiday_transition_bind(AFHolidayTransitionServices *s) {
    if(!s)return 0;
    *s=(AFHolidayTransitionServices){.maps=af_holiday_transition_maps,.map_bytes=1496,
        .status=status,.resolve=identity,.original_rank=rank,.original_collision=original};
    return af_holiday_scene_bind(s);
}
int af_holiday_transition_live_fade(void *context,void *manager,unsigned int donor,
        unsigned int native,unsigned int title,unsigned int landmark) {
    (void)context;AFHolidayTransitionServices services;
    if(!af_holiday_transition_bind(&services))return -1;
    return af_holiday_transition_native_fade(&services,manager,donor,native,title,landmark);
}
