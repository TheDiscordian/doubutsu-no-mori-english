#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "holiday_reserved.h"
#include "holiday_dedicated.h"
#include "holiday-maps-data.h"
static AFHolidayPlace stored;
static int present,outside,unresolved,no_room,fg_ok=1,errors,sets,reserves,kept[128],statuses[128],fade=1,show=1;
static unsigned int clean_count,actor_count,fg_count,control_count,effects,wade;
static int outdoors(void *c) {(void)c;return !outside;}
static int landmark(void *c,unsigned int kind,AFHolidayBlock *b) {
    (void)c;assert(kind==0 || kind==4 || kind==32768);*b=(AFHolidayBlock){3,2};return 1;
}
static unsigned int resolve(void *c,unsigned int name) {(void)c;assert(name<=65535);return unresolved?0:0xD090;}
static AFHolidayPlace *get(void *c,unsigned int native,unsigned int id) {
    (void)c;assert(native==80 && id==7);return present?&stored:0;
}
static AFHolidayPlace *reserve(void *c,unsigned int native,unsigned int id) {
    (void)c;assert(native==80 && id==7);reserves++;
    if(no_room)return 0;
    present=1;return &stored;
}
static int foreground(void *c,const AFHolidayPlace *p) {(void)c;assert(p==&stored);sets++;return fg_ok;}
static void error(void *c,unsigned int type) {(void)c;assert(type==80);errors++;}
static intptr_t operation(void *c,unsigned int op,int donor,int a,int b,int id) {
    (void)c;(void)b;(void)id;assert(donor>=-1 && donor<128);
    switch(op) {
    case AF_HD_KEEP:return kept[donor];
    case AF_HD_SET_KEEP:kept[donor]=1;return 0;
    case AF_HD_CLEAR_KEEP:kept[donor]=0;return 0;
    case AF_HD_STATUS:return statuses[donor]&a;
    case AF_HD_SET_STATUS:statuses[donor]|=a;return 0;
    case AF_HD_CLEAR_STATUS:statuses[donor]&=~a;return 0;
    case AF_HD_FADE:assert(a==1 || a==9);return fade;
    case AF_HD_CLEAN:clean_count++;return 0;
    case AF_HD_FOREGROUND:fg_count++;return 1;
    case AF_HD_ACTOR:actor_count++;return 1;
    case AF_HD_DELETE_FOREGROUND:case AF_HD_DELETE_FOREGROUND_UNCHECKED:case AF_HD_CLEAR_PLACE:return 0;
    case AF_HD_CONTROL:control_count++;return 1;
    case AF_HD_SHOW:return show;
    case AF_HD_EFFECT:case AF_HD_DELETE_EFFECT:effects++;return 0;
    case AF_HD_UNABLE_WADE:wade=a;return 0;
    default:assert(0);return 0;
    }
}
int main(void) {
    unsigned int positions=0;
    for(unsigned int i=0;i<sizeof(expected)/sizeof(*expected);i++) {
        const unsigned int *e=expected[i];AFHolidayMap result;
        assert(af_holiday_map_get(maps,sizeof(maps),e[0],e[1],e[2],&result)==1);
        assert(result.source_name==e[3] && result.x==e[4] && result.z==e[5]);positions++;
    }
    AFHolidayMap row,untouched;memset(&row,0x5A,sizeof(row));untouched=row;
    assert(af_holiday_map_get(maps,sizeof(maps),49,0,0,&row)==0 && !memcmp(&row,&untouched,sizeof(row)));
    assert(af_holiday_map_get(maps,sizeof(maps),29,7,0,&row)==-1);
    assert(af_holiday_map_get(maps,sizeof(maps),1,0,8,&row)==-1);
    assert(af_holiday_map_get(maps,sizeof(maps),1,999,7,&row)==1);
    assert(row.source_name==0xD074 && row.x==11 && row.z==6);
    assert(af_holiday_map_get(maps,sizeof(maps),1,0,5,&row)==1 && row.source_name==0xD03D);
    unsigned char bad[sizeof(maps)];memcpy(bad,maps,sizeof(maps));bad[32]=0xFF;
    assert(af_holiday_map_get(bad,sizeof(bad),1,0,7,&row)==-1);
    AFHolidayReservedOps ops={0,outdoors,landmark,resolve,get,reserve,foreground,error};
    assert(af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,0)==&stored);
    assert(stored.name==0xD090 && stored.unit.x==11 && stored.unit.z==6 && stored.flags==1);
    assert(stored.block.x==2 && stored.block.z==3 && reserves==1);
    stored.unit.x=13;assert(af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,0)==&stored);
    assert(stored.unit.x==13 && reserves==1);
    assert(af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,1)==&stored && sets==1);
    fg_ok=0;assert(!af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,1) && errors==1);
    outside=1;assert(!af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,1) && errors==1);
    outside=0;present=0;unresolved=1;
    assert(!af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,0) && reserves==1 && errors==2);
    unresolved=0;no_room=1;
    assert(!af_holiday_reserved_make(maps,sizeof(maps),&ops,1,80,0,7,7,0) && errors==3);

    const unsigned int owners[]={64,12,13,15,14,16,20,1,35,11,41,43,56,37};
    AFHolidayDedicatedCommon common={-1,-1};AFHolidayDedicated ctx={0,operation,&common,1,1};
    for(unsigned int i=0;i<14;i++) {
        unsigned int t=owners[i];int noop=t==11 || t==41;
        common=(AFHolidayDedicatedCommon){-1,-1};
        assert(af_holiday_dedicated(&ctx,t,0)==1 && kept[t]==!noop);
        assert(af_holiday_dedicated(&ctx,t,0)==(noop?1:2));
        if(t==16)assert(wade==1 && common.fieldday_event_id==16);
        if(t>=12 && t<=15)assert(common.fieldday_event_id==(int)t);
        show=-1;assert(af_holiday_dedicated(&ctx,t,2)==(noop || t==16?0:2));
        show=0;assert(af_holiday_dedicated(&ctx,t,2)==0);
        show=1;assert(af_holiday_dedicated(&ctx,t,2)==(noop || t==16?0:1));
        statuses[t]=2;assert(af_holiday_dedicated(&ctx,t,3)==(noop || t==16?0:1));
        assert(af_holiday_dedicated(&ctx,t,1)==!noop && !kept[t]);
        if(t==16)assert(!wade);
        fade=0;assert(af_holiday_dedicated(&ctx,t,0)==noop && !kept[t]);fade=1;
        ctx.pool_block_exists=ctx.shrine_block_exists=0;
        assert(af_holiday_dedicated(&ctx,t,0)==noop);
        if(!noop)assert(statuses[t]&32);
        ctx.pool_block_exists=ctx.shrine_block_exists=1;
    }
    assert(clean_count && actor_count && fg_count && control_count && effects);
    assert(af_holiday_dedicated(&ctx,255,0)==-1 && af_holiday_dedicated(&ctx,1,5)==-1);
    printf("All %u source placements and 14 complete owner callbacks pass shared layout, identity rejection, reserved placement, transitions, culling, and failure checks. Native operations are doubled.\n",positions);
}
