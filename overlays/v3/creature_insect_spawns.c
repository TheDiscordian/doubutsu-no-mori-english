/* Complete insect monthly/time selection and habitat-to-creation path.
 * Donor calendars are generated from the verified REL; native foreground and
 * terrain identities are interpreted here, never by GameCube object offsets.
 */
#include "creature_insect_spawns.h"
extern int mCoBG_CheckWaterAttribute(unsigned),mCoBG_CheckHole_OrgAttr(unsigned);
static unsigned be16(const SpawnU8 *p) {return (unsigned)p[0]*256u+p[1];}
static unsigned be32(const SpawnU8 *p) {
    return (unsigned)p[0]*16777216u+(unsigned)p[1]*65536u+(unsigned)p[2]*256u+p[3];
}
static int leap(int y) {return !(y%4) && (y%100 || !(y%400));}
static int days(SpawnDate date) {
    static const SpawnU8 lengths[]={31,28,31,30,31,30,31,31,30,31,30,31};
    if (date.year<1900 || date.year>2200 || date.month<1 || date.month>12 || date.day<1 ||
            date.day>lengths[date.month-1]+(date.month==2 && leap(date.year))) return -1;
    int y=date.year-1,result=365*y+y/4-y/100+y/400+date.day-1;
    for (int m=1;m<date.month;m++) result+=lengths[m-1]+(m==2 && leap(date.year));
    return result;
}
int af_v3_insect_spawn_time(unsigned hour) {
    if (hour>23) return -1;
    return hour<4 || hour>=23?0:hour<8?1:hour<16?2:hour<17?3:hour<19?4:5;
}
int af_v3_insect_spawn_terms(SpawnTerms *out,SpawnSeason *saved,SpawnDate date,
                             SpawnRandom random,void *ctx) {
    int today=days(date);
    if (!out || !saved || !random || today<0 || date.year>2199 ||
            saved->term>11 || saved->offset>5) return 0;
    unsigned now=(unsigned)date.month-1;
    SpawnTerms terms={now,now,1.0f};
    int delta=(int)saved->term-(int)now;
    int renew=(delta>1 || delta< -1) && saved->term!=0 && now!=11;
    if (!renew) {
        SpawnDate start={date.year,(int)saved->term+1,1};
        if (saved->term!=now && now==11) start.year++;
        int elapsed=today-(days(start)-(int)saved->offset);
        if (elapsed>=5) renew=1;
        else if (elapsed>=0) {terms.next=saved->term;terms.rate=(float)(5-elapsed)/6.0f;}
    }
    if (renew) {
        float r=random(ctx);
        if (!(r>=0.0f && r<1.0f)) return 0;
        saved->term=(now+1)%12;saved->offset=(unsigned)(r*6.0f);
    }
    *out=terms;return 1;
}
static int packet(const SpawnU8 *data,unsigned bytes) {
    if (!data || bytes<32+78*4+12+82 || be32(data)!=0x41464953u ||
            be32(data+4)!=1 || be32(data+8)!=bytes || be32(data+12)!=78 ||
            be32(data+24)!=41 || be32(data+28)!=AF_SPAWN_CAPACITY) return 0;
    unsigned extras=be32(data+16),births=be32(data+20);
    return extras>=32+78*4 && extras<=bytes-94 && births==extras+12 && births==bytes-82;
}
static int append(SpawnPlan *out,unsigned actor,unsigned area,float weight,unsigned selected) {
    if (actor>41 || actor==40 || area>13 || (actor==41)!=(area==13) ||
            !(weight>=0.0f && weight<=255.0f)) return 0;
    if (actor>=32 && actor<=39 && !(selected&(1u<<(actor-32)))) return 1;
    /* Keep zero rows: the source copies complete terms and filters later. */
    if (out->count==AF_SPAWN_CAPACITY) return 0;
    out->rows[out->count++]=(SpawnRow){(SpawnU16)actor,(SpawnU16)area,weight};return 1;
}
int af_v3_insect_spawn_plan(SpawnPlan *out,const SpawnU8 *data,unsigned bytes,
                            SpawnTerms terms,unsigned time,unsigned selected,int island) {
    if (!out || !packet(data,bytes) || terms.current>11 || terms.next>11 ||
            !(terms.rate>=0.0f && terms.rate<=1.0f) || time>5 || selected>255 ||
            (island!=0 && island!=1)) return 0;
    SpawnPlan plan;plan.count=0;
    if (island) terms.rate=1.0f;
    unsigned end=be32(data+16);
    for (unsigned pass=0;pass<2;pass++) {
        float rate=pass?1.0f-terms.rate:terms.rate;
        if (pass && rate==0.0f) break;
        unsigned month=pass?terms.next:terms.current;
        unsigned list=island?72+time:month*6+time;
        unsigned at=be16(data+32+list*4),count=be16(data+34+list*4);
        if (at<32+78*4 || at>end || count>21 || count>(end-at)/4) return 0;
        for (unsigned i=0;i<count;i++) {
            const SpawnU8 *row=data+at+i*4;
            if (!append(&plan,be16(row),row[2],(float)row[3]*rate,selected)) return 0;
        }
    }
    for (unsigned i=0;i<3;i++) {
        const SpawnU8 *row=data+end+i*4;
        if (!append(&plan,be16(row),row[2],(float)row[3],selected)) return 0;
    }
    out->count=plan.count;
    for (unsigned i=0;i<plan.count;i++) out->rows[i]=plan.rows[i];
    return 1;
}
int af_v3_insect_spawn_tree(unsigned item) {
    /* Full-grown native/source environmental IDs, including V3 gold trees.
     * No-fruit stages, saplings, bee trees, and palms are not donor spawn trees.
     */
    static const SpawnU16 trees[]={0x804,0x5F,0x60,0x69,0x80C,0x814,0x81C,
        0x824,0x82C,0x831,0x836,0x83B,0x853,0x861,0x78,0x79,0x82,
        0x868,0x7F,0x80,0x867};
    for (unsigned i=0;i<sizeof(trees)/sizeof(*trees);i++) if (item==trees[i]) return 1;
    return 0;
}
static int fg_area(unsigned area) {return area==1 || area==2 || area==3 || area==8 || area==9 || area==10 || area==12;}
static int site(const InsectHabitat *h,unsigned area,unsigned x,unsigned z,int availability) {
    unsigned item=h->foreground[z*16+x],attr=h->collision[z*16+x]&63u;
    if (availability && fg_area(area) && (h->deposits[z]&(1u<<x))) return 0;
    switch (area) {
        case 0:return af_v3_insect_spawn_tree(item);
        case 1:case 2:case 12:return item>=0x845 && item<=0x84A;
        case 3:return !item;
        case 4:return attr<=5 || attr==9;
        case 5:return attr==9;
        case 6:return mCoBG_CheckWaterAttribute(attr);
        case 7:return attr>=12 && attr<=21;
        case 8:return item==0x2806;
        case 9:return item==0x2F03;
        case 10:return item>=0x63 && item<=0x67;
        case 11:return !item && mCoBG_CheckHole_OrgAttr(attr);
        case 13:return 1;
    }
    return 0;
}
static int available(const InsectHabitat *h,unsigned area) {
    if (area==13) return 1;
    if ((area==1 || area==12) && h->weather==1) return 0;
    if (area==2 && h->weather!=1) return 0;
    if ((area==8 || area==9) && (h->weather==1 || h->weather==2)) return 0;
    if (area==7 && !(h->block&0x8000u) && (h->block&(0x100u|0x80u|0x800u))) return 0;
    for (unsigned z=2;z<14;z++) for (unsigned x=2;x<14;x++) if (site(h,area,x,z,1)) return 1;
    return 0;
}
int af_v3_insect_spawn_choose(SpawnPlan *plan,const InsectHabitat *h,int rank,int native,
                              SpawnRandom random,void *ctx) {
    static const float rates[]={.5f,.75f,.875f,1,1,1,1};
    if (!plan || plan->count>AF_SPAWN_CAPACITY || !h || !h->foreground || !h->collision ||
            !h->deposits || !random || (native!=0 && native!=1) || (h->block&0x400000u)) return -1;
    for (unsigned i=0;i<plan->count;i++) {
        SpawnRow row=plan->rows[i];
        if (row.actor>41 || row.actor==40 || row.area>13 ||
                (row.actor==41)!=(row.area==13) || !(row.weight>=0 && row.weight<=255)) return -1;
    }
    int food=0;
    for (unsigned area=0;area<14;area++) {
        int valid=available(h,area);
        if (valid && area==8) food|=1;
        if (valid && area==9) food|=2;
        /* Source ordering matters: area 3 was already cleared before area 12
         * falls back to flying. Do not re-filter its rewritten rows. */
        if (area==12 && h->weather!=1)
            for (unsigned i=0;i<plan->count;i++) if (plan->rows[i].area==12)
                plan->rows[i].area=valid?1:3;
        if (!valid) for (unsigned i=0;i<plan->count;i++)
            if (plan->rows[i].area==area) plan->rows[i].weight=0;
    }
    float total=0;
    for (unsigned i=0;i<plan->count;i++) {
        SpawnRow *row=plan->rows+i;
        if (food && !((row->area==8 && (food&1)) || (row->area==9 && (food&2)))) row->weight=0;
        if (native && (row->actor<32 || row->actor>39)) row->weight=0;
        total+=row->weight;
    }
    /* Native mode preserves the original manager as one 100-weight opportunity.
     * Source mode retains no-spawn mass and field-rank scaling exactly. */
    if (!(total>0)) return native?-2:-1;
    float r=random(ctx);
    if (!(r>=0 && r<1)) return -1;
    float chosen=r*(native?total+100.0f:food || total>100?total:100.0f);
    if (native) {if (chosen<100.0f) return -2;chosen-=100.0f;}
    if (rank<0) rank=0;
    if (rank>6) rank=6;
    float rate=food || native?1:rates[rank];
    for (unsigned i=0;i<plan->count;i++) {
        chosen-=plan->rows[i].weight*rate;
        if (chosen<0) return (int)i;
    }
    return -1;
}
static int take(SpawnU16 *sites,unsigned *count,unsigned *x,unsigned *z,SpawnRandom random,void *ctx) {
    if (!*count) return 0;
    float r=random(ctx);
    if (!(r>=0 && r<1)) return 0;
    unsigned chosen=(unsigned)(r*(float)*count);
    for (unsigned row=0;row<12;row++) for (unsigned col=2;col<14;col++)
        if (sites[row]&(1u<<col)) {
            if (!chosen) {
                sites[row]&=(SpawnU16)~(1u<<col);--*count;
                *x=col;*z=row+2;return 1;
            }
            --chosen;
        }
    return 0;
}
int af_v3_insect_spawn_group(const SpawnRow *row,const InsectHabitat *h,
                             const SpawnU8 *data,unsigned bytes,SpawnRandom random,
                             InsectCreate create,void *ctx,int *last_result) {
    if (last_result) *last_result=0;
    if (!row || !h || !h->foreground || !h->collision || !random || !create ||
            !packet(data,bytes) || row->actor>41 || row->actor==40 || row->area>13) return -1;
    if (row->actor==41 || row->area>=12) return 0;
    SpawnU16 sites[12]={0};unsigned count=0;
    for (unsigned z=2;z<14;z++) for (unsigned x=2;x<14;x++) if (site(h,row->area,x,z,0)) {
        sites[z-2]|=(SpawnU16)(1u<<x);++count;
    }
    InsectBirth birth={row->actor,0,0,0,row->actor==38};
    if (!take(sites,&count,&birth.x,&birth.z,random,ctx)) return 0;
    const SpawnU8 *sizes=data+be32(data+20)+row->actor*2;
    if (sizes[0]!=((row->actor==10 || row->actor==27)?6:1) ||
            sizes[1]!=((row->actor==10 || row->actor==27)?3:0)) return -1;
    /* Even a zero range consumes the donor's group-size random draw. */
    float r=random(ctx);
    if (!(r>=0 && r<1)) return -1;
    unsigned n=sizes[0]+(unsigned)(r*(float)sizes[1]);int made=0;
    for (unsigned i=0;i<n;i++) {
        unsigned item=h->foreground[birth.z*16+birth.x];birth.extra=0;
        if (row->actor==28) birth.extra=af_v3_insect_spawn_tree(item)?4:item==0x2F03?6:0;
        int result=!!create(ctx,&birth);
        if (last_result) *last_result=result;
        if (!result) break;
        ++made;
        if (i+1<n && !take(sites,&count,&birth.x,&birth.z,random,ctx)) {
            if (last_result) *last_result=0;
            break;
        }
    }
    return made;
}
