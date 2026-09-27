/* Shared source-calendar, season, weighted-selection, and spawn-position path.
 * The native caller owns persistence and engine queries. No per-species loader,
 * unbounded native array, or change to the player's existing species IDs.
 */
#include "creature_spawns.h"
_Static_assert(sizeof(SpawnRow)==8,"Fish spawn weight row");
static unsigned be16(const SpawnU8 *p) {return (unsigned)p[0]*256u+p[1];}
static unsigned be32(const SpawnU8 *p) {
    return (unsigned)p[0]*16777216u+(unsigned)p[1]*65536u+(unsigned)p[2]*256u+p[3];
}
static int leap(int y) {return !(y%4) && (y%100 || !(y%400));}
static int days(SpawnDate d) {
    static const unsigned char lengths[]={31,28,31,30,31,30,31,31,30,31,30,31};
    if (d.year<1900 || d.year>2200 || d.month<1 || d.month>12 || d.day<1 ||
            d.day>lengths[d.month-1]+(d.month==2 && leap(d.year))) return -1;
    int y=d.year-1, result=365*y+y/4-y/100+y/400+d.day-1;
    for (int m=1;m<d.month;m++) result+=lengths[m-1]+(m==2 && leap(d.year));
    return result;
}
int af_v3_spawn_time(unsigned hour) {
    if (hour>23) return -1;
    return hour<4 || hour>=21?0:hour<9?1:hour<16?2:3;
}
/* Source five-day term blending, with the same saved term/offset. The caller
 * must persist both fields; substituting a new random offset each visit is wrong.
 */
int af_v3_spawn_terms(SpawnTerms *out,SpawnSeason *saved,SpawnDate date,
                      SpawnRandom random,void *context) {
    int today=days(date), renew=0;
    if (!out || !saved || !random || today<0 || date.year>2199 || saved->term>23 || saved->offset>5) return 0;
    unsigned now=(unsigned)(date.month-1)*2u+(date.day>15);
    unsigned next=now==23?0:now+1;
    SpawnTerms terms={now,now,1.0f};
    int delta=(int)saved->term-(int)now;
    if ((delta>1 || delta< -1) && saved->term!=0 && now!=23) renew=1;
    else {
        SpawnDate start={date.year,(int)(saved->term/2)+1,(saved->term&1)?15:1};
        if (!(saved->term&1) && saved->term!=now && now==23) start.year++;
        int beginning=days(start)-(int)saved->offset;
        int elapsed=today-beginning;
        if (elapsed>=5) renew=1;
        else if (elapsed>=0) {
            terms.next=saved->term;
            terms.rate=(float)(5-elapsed)/6.0f;
        }
    }
    if (renew) {
        float r=random(context);
        if (!(r>=0.0f && r<1.0f)) return 0;
        saved->term=next;saved->offset=(unsigned)(r*6.0f);
    }
    *out=terms;return 1;
}
static int append(SpawnPlan *p,unsigned actor,unsigned area,float weight,unsigned selected) {
    if (actor>=36 && actor<=44 && !(selected&(1u<<(actor-36)))) return 1;
    if ((actor>=32 && actor<=34) || actor>44 || area>6 || !(weight>=0.0f)) return 0;
    if (weight==0.0f) return 1;
    if (p->count==AF_SPAWN_CAPACITY) return 0;
    p->rows[p->count++]=(SpawnRow){(SpawnU16)actor,(SpawnU16)area,weight};return 1;
}
/* Water: river=0, coastal sea=1, pond=2, fishing tourney=3, island=4.
 * Island data is retained, but an N64 town caller must not invent an island.
 * Brook trout and herabuna remain separate. Selection bits are actor 36..44.
 */
int af_v3_spawn_plan(SpawnPlan *out,const SpawnU8 *data,unsigned bytes,unsigned water,
                     SpawnTerms terms,unsigned time,unsigned selected,int rain) {
    if (!out || !data || bytes<32+296*4 || water>4 || time>3 || terms.current>23 ||
            terms.next>23 || !(terms.rate>=0.0f && terms.rate<=1.0f) || selected>511 ||
            be32(data)!=0x41465350u || be32(data+4)!=1 || be32(data+8)!=bytes ||
            be32(data+12)!=296 || be32(data+28)!=AF_SPAWN_CAPACITY) return 0;
    unsigned native=be32(data+16);
    if (native<32+296*4 || native>bytes || bytes-native<96) return 0;
    SpawnPlan plan;plan.count=0;
    if (water>=3) terms.rate=1.0f;
    for (unsigned pass=0;pass<2;pass++) {
        float rate=pass?1.0f-terms.rate:terms.rate;
        if (pass && rate==0.0f) break;
        unsigned term=pass?terms.next:terms.current;
        unsigned list=water<3?water*96+term*4+time:288+(water-3)*4+time;
        unsigned at=be16(data+32+list*4),count=be16(data+34+list*4);
        if (count>32 || at<32+296*4 || at>bytes || count>(bytes-at)/4) return 0;
        for (unsigned i=0;i<count;i++) {
            const SpawnU8 *r=data+at+i*4;
            if (!append(&plan,be16(r),r[2],(float)r[3]*rate,selected)) return 0;
        }
        if (water==0 && !append(&plan,1,0,(float)data[native+term*4+time]*rate,selected)) return 0;
        /* Donor coelacanth weight is not multiplied by the term ratio. */
        if (!pass && (water==1 || water==4) && rain && time!=2 &&
                !append(&plan,31,4,2.0f,selected)) return 0;
    }
    out->count=plan.count;
    for (unsigned i=0;i<plan.count;i++) out->rows[i]=plan.rows[i];
    return 1;
}
static int place(unsigned area,unsigned block) {
    if (area==0) return !!(block&0x8000u);
    if (area==1) return !!(block&0x100u);
    /* GAFE01-r0 checks RIVER here, not the later Australian RIVER|MARINE. */
    if (area==2) return !!(block&0x80u);
    return area<=6;
}
/* Preserve source rejection/retry and environment weighting. Filtering invalid
 * locations before the draw would change both the failure rate and RNG stream.
 */
int af_v3_spawn_pick(const SpawnPlan *plan,unsigned block,int rank,SpawnRandom random,void *context) {
    static const float rates[]={0.5f,0.75f,0.875f,1,1,1,1};
    if (!plan || !random || plan->count>AF_SPAWN_CAPACITY) return -1;
    unsigned char tried[AF_SPAWN_CAPACITY];
    for (unsigned i=0;i<AF_SPAWN_CAPACITY;i++) tried[i]=0;
    if (rank<0) rank=0;
    if (rank>6) rank=6;
    for (unsigned attempt=0;attempt<plan->count;attempt++) {
        float total=0.0f;
        for (unsigned i=0;i<plan->count;i++) {
            if (!(plan->rows[i].weight>=0.0f && plan->rows[i].weight<=255.0f) ||
                    plan->rows[i].area>6) return -1;
            if (!tried[i]) total+=plan->rows[i].weight;
        }
        if (!(total>0.0f)) return -1;
        float r=random(context);
        if (!(r>=0.0f && r<1.0f)) return -1;
        float chosen=total*r, remaining=total;
        int retry=0;
        for (unsigned i=0;i<plan->count;i++) if (!tried[i]) {
            remaining-=plan->rows[i].weight*rates[rank];
            if (remaining<0.0f) return -1;
            if (chosen>=remaining) {
                tried[i]=1;
                if (place(plan->rows[i].area,block)) return (int)i;
                retry=1;break;
            }
        }
        if (!retry) return -1;
    }
    return -1;
}
/* The engine callback checks the unit attribute, sand, and water/ground height
 * for this actor. Keep the source two-unit margin and one final random draw.
 */
int af_v3_spawn_position(SpawnPosition *out,unsigned actor,SpawnSite site,
                         SpawnRandom random,void *context) {
    if (!out || !site || !random || actor>44 || (actor>=32 && actor<=34)) return 0;
    unsigned short positions[144];unsigned count=0;
    for (unsigned z=2;z<14;z++) for (unsigned x=2;x<14;x++)
        if (site(context,actor,x,z)) positions[count++]=(unsigned short)(z*16+x);
    if (!count) return 0;
    float r=random(context);
    if (!(r>=0.0f && r<1.0f)) return 0;
    unsigned chosen=positions[(unsigned)(r*(float)count)];
    *out=(SpawnPosition){actor,chosen%16,chosen/16};return 1;
}
