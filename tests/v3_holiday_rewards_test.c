/* Synthetic selection/transaction state with the complete prepared donor table. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/holiday_rewards.c"
struct Context { unsigned player,full,gives,marks,item; int claim_error; };
static unsigned char selected[65536],flags[4][28];
static unsigned resolve(void *p,unsigned source) {
    (void)p;assert(source<65536);
    return selected[source] ? (source^0x4000u) : 0;
}
static int claimed(void *p,unsigned event) {
    struct Context *c=p;assert(c->player<4 && event<28);
    return c->claim_error ? -1 : flags[c->player][event];
}
static int give(void *p,unsigned item) {
    struct Context *c=p;
    if (c->full) return 0;
    ++c->gives;c->item=item;return 1;
}
static void mark(void *p,unsigned event) {
    struct Context *c=p;assert(c->player<4 && event<28 && !flags[c->player][event]);
    assert(c->gives==c->marks+1);++c->marks;flags[c->player][event]=1;
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    unsigned char data[1024];size_t n=fread(data,1,sizeof(data),f);assert(feof(f));fclose(f);
    assert(n==370 && af_v3_holiday_valid(data,(unsigned)n));
    struct Context context={0};struct AfHolidayOps ops={&context,resolve,claimed,give,mark};
    struct AfHolidayOffer offer,untouched;memset(&untouched,0xA5,sizeof(untouched));
    memset(selected,1,sizeof(selected));
    for (unsigned event=0;event<28;++event) for (unsigned gender=0;gender<2;++gender) {
        unsigned first=half(data+16+event*8),count=half(data+18+event*8);
        if (data[20+event*8]==2) {first+=gender;count=1;}
        assert(af_v3_holiday_count(data,(unsigned)n,event,gender,&ops)==(int)count);
        for (unsigned roll=0;roll<count;++roll) {
            assert(af_v3_holiday_offer(data,(unsigned)n,event,gender,roll,&ops,&offer));
            assert(offer.event==event && offer.gender==gender && offer.variant==first+roll);
            assert(offer.source_item==half(data+240+(first+roll)*2));
            assert(offer.item==(offer.source_item^0x4000u));
        }
        offer=untouched;
        assert(!af_v3_holiday_offer(data,(unsigned)n,event,gender,count,&ops,&offer));
        assert(!memcmp(&offer,&untouched,sizeof(offer)));
    }
    /* Only selected variants participate; the ordinal is not a donor ID. */
    memset(selected,0,sizeof(selected));
    unsigned event=4,first=half(data+16+event*8),source=half(data+240+(first+7)*2);
    selected[source]=1;
    assert(af_v3_holiday_count(data,(unsigned)n,event,0,&ops)==1);
    assert(af_v3_holiday_offer(data,(unsigned)n,event,0,0,&ops,&offer));
    assert(offer.variant==first+7 && offer.source_item==source);
    struct AfHolidayOffer valid=offer;
    selected[source]=0;assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
    assert(!context.gives && !context.marks);
    selected[source]=1;context.full=1;
    assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
    assert(!context.gives && !context.marks && !flags[0][event]);
    context.full=0;context.claim_error=1;
    assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
    context.claim_error=0;
    /* Tampered transient offers never award a different item or trophy. */
    for (unsigned i=0;i<5;++i) {
        offer=valid;unsigned *fields=(unsigned *)&offer;fields[i]=0xFFFFFFFFu;
        assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
    }
    offer=valid;
    for (unsigned player=0;player<4;++player) {
        context.player=player;
        assert(af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
        assert(context.gives==player+1 && context.marks==player+1);
        assert(context.item==offer.item && flags[player][event]);
        assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,&offer));
        assert(!af_v3_holiday_offer(data,(unsigned)n,event,0,0,&ops,&offer));
    }
    unsigned char changed[1024];memcpy(changed,data,n);
    for (unsigned size=0;size<n;++size) assert(!af_v3_holiday_valid(data,size));
    assert(!af_v3_holiday_valid(data,(unsigned)n+1));
    assert(!af_v3_holiday_valid(NULL,(unsigned)n));
    const unsigned offsets[]={0,4,6,8,10,12,14,16,18,20,21,22,240};
    for (unsigned i=0;i<sizeof(offsets)/sizeof(offsets[0]);++i) {
        memcpy(changed,data,n);changed[offsets[i]]=255;
        if (offsets[i]==240) changed[240]=changed[241]=0;
        assert(!af_v3_holiday_valid(changed,(unsigned)n));
    }
    assert(af_v3_holiday_count(data,(unsigned)n,28,0,&ops)==-1);
    assert(af_v3_holiday_count(data,(unsigned)n,0,2,&ops)==-1);
    assert(af_v3_holiday_count(data,(unsigned)n,0,0,NULL)==-1);
    assert(!af_v3_holiday_commit(data,(unsigned)n,NULL,&offer));
    assert(!af_v3_holiday_commit(data,(unsigned)n,&ops,NULL));
    puts("Complete selectors, sparse choices, four-player receipts, full pockets, and malformed inputs pass");
    return 0;
}
