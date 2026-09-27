#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/creature_spawns.c"
typedef struct {float value;unsigned calls;} Random;
static float rng(void *p) {Random *r=p;r->calls++;return r->value;}
static int site(void *p,unsigned actor,unsigned x,unsigned z) {
    unsigned *calls=p;(*calls)++;
    assert(actor==43 && x>=2 && x<14 && z>=2 && z<14);
    return x==5 && z==7;
}
static float position_rng(void *p) {(void)p;return 0.5f;}
static unsigned read_word(FILE *f) {
    unsigned char b[4];assert(fread(b,1,4,f)==4);return be32(b);
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    unsigned size=read_word(f);unsigned char *data=malloc(size);assert(data);
    assert(fread(data,1,size,f)==size);
    unsigned cases=read_word(f);
    struct {unsigned before;SpawnPlan plan;unsigned after;} guarded;
    for(unsigned i=0;i<cases;i++) {
        unsigned water=read_word(f),time=read_word(f),mask=read_word(f),rain=read_word(f);
        SpawnTerms terms;terms.current=read_word(f);terms.next=read_word(f);
        union {unsigned u;float f;} rate;rate.u=read_word(f);terms.rate=rate.f;
        guarded.before=guarded.after=0xAA55BB66;
        assert(af_v3_spawn_plan(&guarded.plan,data,size,water,terms,time,mask,(int)rain));
        unsigned expected=read_word(f);assert(guarded.plan.count==expected);
        for(unsigned n=0;n<expected;n++) {
            unsigned actor=read_word(f),area=read_word(f);rate.u=read_word(f);
            assert(guarded.plan.rows[n].actor==actor && guarded.plan.rows[n].area==area);
            assert(guarded.plan.rows[n].weight==rate.f);
        }
        assert(guarded.before==0xAA55BB66 && guarded.after==0xAA55BB66);
    }
    assert(fgetc(f)==EOF);fclose(f);
    SpawnPlan preserved=guarded.plan;
    data[0]^=1;
    assert(!af_v3_spawn_plan(&guarded.plan,data,size,0,(SpawnTerms){0,0,1},0,511,0));
    assert(!memcmp(&preserved,&guarded.plan,sizeof(preserved)));data[0]^=1;
    assert(!af_v3_spawn_plan(&guarded.plan,data,size-1,0,(SpawnTerms){0,0,1},0,511,0));
    for(unsigned hour=0;hour<24;hour++)
        assert(af_v3_spawn_time(hour)==(hour<4||hour>=21?0:hour<9?1:hour<16?2:3));
    assert(af_v3_spawn_time(24)==-1);
    Random r={0.9f,0};SpawnTerms terms;SpawnSeason season={1,0};
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,1,14},rng,&r));
    assert(terms.current==0 && terms.next==0 && terms.rate==1 && r.calls==0);
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,1,15},rng,&r));
    assert(terms.current==0 && terms.next==1 && terms.rate==5.0f/6.0f);
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,1,19},rng,&r));
    assert(terms.current==1 && terms.next==1 && terms.rate==1.0f/6.0f);
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,1,20},rng,&r));
    assert(season.term==2 && season.offset==5 && terms.rate==1 && r.calls==1);
    season=(SpawnSeason){0,5};
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,12,27},rng,&r));
    assert(terms.current==23 && terms.next==0 && terms.rate==5.0f/6.0f);
    assert(!af_v3_spawn_terms(&terms,&season,(SpawnDate){2003,2,29},rng,&r));
    assert(af_v3_spawn_terms(&terms,&season,(SpawnDate){2004,2,29},rng,&r));
    SpawnPlan p={2,{{19,1,1},{36,5,1}}};
    r=(Random){0.75f,0};
    assert(af_v3_spawn_pick(&p,0,6,rng,&r)==1 && r.calls==2);
    r=(Random){0.75f,0};
    assert(af_v3_spawn_pick(&p,0x100,6,rng,&r)==0 && r.calls==1);
    r=(Random){0.0f,0};
    assert(af_v3_spawn_pick(&p,0x100,0,rng,&r)==-1 && r.calls==1);
    p.count=65;assert(af_v3_spawn_pick(&p,0,6,rng,&r)==-1);
    p.count=0;assert(af_v3_spawn_pick(&p,0,6,rng,&r)==-1);
    unsigned calls=0;SpawnPosition position;
    assert(af_v3_spawn_position(&position,43,site,position_rng,&calls));
    assert(position.actor==43 && position.x==5 && position.z==7 && calls==144);
    free(data);printf("%u source-bound full-calendar cases and shared spawn-path checks pass\n",cases);
    return 0;
}
