/* One source-derived terrain path for fish spawning and coastal patrol. */
#include "creature_water.h"
#define FISH_U16(p,n) (*(unsigned short *)((unsigned char *)(p)+(n)))
#define FISH_S16(p,n) (*(short *)((unsigned char *)(p)+(n)))
#define FISH_U32(p,n) (*(unsigned *)((unsigned char *)(p)+(n)))
#define FISH_VECTOR(p,n) (*(FishVector *)((unsigned char *)(p)+(n)))

static int sand(FishVector position) {
    const unsigned *unit=af_water_unit(position);
    if (!unit) return 1; /* No collision data cannot be a valid spawn site. */
    unsigned attribute=*unit&63u;
    return attribute==10 || attribute==22 || attribute==25 || attribute==26 ||
           attribute==36 || attribute==37 || attribute==38;
}
static float depth(FishVector position) {
    float ground=af_water_ground(0,position,0.0f);
    return af_water_height(position,"v3-fish",0)-ground;
}
int af_v3_water_site(void *context,unsigned actor,unsigned x,unsigned z) {
    FishWaterBlock *block=context;
    if (!block || !block->collision || x>=16 || z>=16 || actor>44 ||
            (actor>=32 && actor<=34)) return 0;
    unsigned attribute=block->collision[z*16+x]&63u;
    if (actor==19) return attribute==13; /* Large char: waterfall. */
    int ocean=actor==31 || (actor>=39 && actor<=42);
    if (ocean && attribute!=24) return 0;
    if (!ocean && !af_water_is_water(attribute)) return 0;
    if (ocean || ((actor==22 || actor==35) && attribute==24)) {
        FishVector position;
        af_water_centre(&position,block->bx,block->bz,(int)x,(int)z);
        return !sand(position) && depth(position)>=20.0f;
    }
    return 1;
}
int af_v3_water_nearshore(void *actor) {
    const signed char *bytes=actor;
    unsigned kind=af_water_block(bytes[8],bytes[9]);
    if (!(kind&0x800u) || (kind&0x400000u)) return 0;
    for (unsigned i=0;i<4;i++) {
        FishVector position=FISH_VECTOR(actor,0x28);
        if (i<2) position.z+=i==0?-80.0f:80.0f;
        else position.x+=i==2?-80.0f:80.0f;
        if (!af_water_is_water(af_water_attribute(position,0))) return 1;
    }
    return 0;
}
static int turn(void *actor,short angle,int restore) {
    if (restore) FISH_VECTOR(actor,0x28)=FISH_VECTOR(actor,0x3C);
    FISH_S16(actor,0x36)=FISH_S16(actor,0xDE)=angle;
    FISH_U16(actor,0x23C)|=0x40u;return 1;
}
int af_v3_water_wall(void *actor) {
    unsigned result=FISH_U32(actor,0x98);
    if ((result>>21)&31u) {
        unsigned count=(result>>18)&7u;
        /* The native actor owns exactly three wall records. */
        if (count>3) return turn(actor,0,1);
        for (unsigned i=0;i<count;i++)
            if (!FISH_S16(actor,0xAA+i*4)) return turn(actor,FISH_S16(actor,0xA8+i*4),0);
    }
    FishVector position=FISH_VECTOR(actor,0x28);
    position.z-=10.0f;
    /* Retain the source attribute query and its ordering. */
    (void)af_water_attribute(position,0);
    float water_depth=depth(position);
    if (sand(position) || water_depth<20.0f) return turn(actor,0,1);
    if (!af_v3_water_nearshore(actor)) return turn(actor,(short)0x8000u,1);
    return 0;
}
