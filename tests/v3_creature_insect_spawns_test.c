#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "creature_insect_spawns.h"
int mCoBG_CheckWaterAttribute(unsigned a) {return (a>=12 && a<=21) || a==24;}
int mCoBG_CheckHole_OrgAttr(unsigned a) {
    return a<=2 || (a>=4 && a<=6) || a==10 || a==22 || a==25 || a==26 ||
        a==36 || (a>=43 && a<=46) || (a>=59 && a<=62);
}
typedef struct {float value;unsigned calls,count,fail;InsectBirth births[8];} Context;
static float rng(void *p) {Context *c=p;c->calls++;return c->value;}
static int create(void *p,const InsectBirth *b) {
    Context *c=p;if (c->count==c->fail) return 0;
    assert(c->count<8);c->births[c->count++]=*b;return 1;
}
static unsigned word(FILE *f) {
    unsigned char b[4];assert(fread(b,1,4,f)==4);
    return (unsigned)b[0]<<24|(unsigned)b[1]<<16|(unsigned)b[2]<<8|b[3];
}
static void plan(SpawnPlan *p,unsigned actor,unsigned area,float weight) {
    p->count=1;p->rows[0]=(SpawnRow){actor,area,weight};
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    unsigned bytes=word(f);unsigned char *data=malloc(bytes);assert(data);
    assert(fread(data,1,bytes,f)==bytes);
    struct {unsigned head;SpawnPlan p;unsigned tail;} guarded;
    unsigned cases=word(f);
    for (unsigned i=0;i<cases;i++) {
        unsigned month=word(f),next=word(f),time=word(f),mask=word(f),island=word(f);
        union {unsigned u;float f;} rate;rate.u=word(f);
        guarded.head=guarded.tail=0xAF151515;
        assert(af_v3_insect_spawn_plan(&guarded.p,data,bytes,(SpawnTerms){month,next,rate.f},time,mask,(int)island));
        unsigned count=word(f);assert(guarded.p.count==count);
        for (unsigned row=0;row<count;row++) {
            unsigned actor=word(f),area=word(f);rate.u=word(f);
            assert(guarded.p.rows[row].actor==actor && guarded.p.rows[row].area==area);
            assert(guarded.p.rows[row].weight==rate.f);
        }
        assert(guarded.head==0xAF151515 && guarded.tail==0xAF151515);
    }
    assert(fgetc(f)==EOF);fclose(f);
    SpawnPlan p=guarded.p,before=p;
    data[0]^=1;assert(!af_v3_insect_spawn_plan(&p,data,bytes,(SpawnTerms){0,0,1},0,255,0));
    assert(!memcmp(&p,&before,sizeof(p)));data[0]^=1;
    assert(!af_v3_insect_spawn_plan(&p,data,bytes-1,(SpawnTerms){0,0,1},0,255,0));
    for (unsigned h=0;h<24;h++) assert(af_v3_insect_spawn_time(h)==
        (h<4 || h>=23?0:h<8?1:h<16?2:h<17?3:h<19?4:5));
    assert(af_v3_insect_spawn_time(24)==-1);
    Context c={.value=.75f,.fail=8};SpawnSeason season={0,5};SpawnTerms terms;
    assert(af_v3_insect_spawn_terms(&terms,&season,(SpawnDate){2004,12,27},rng,&c));
    assert(terms.current==11 && terms.next==0 && terms.rate==5.0f/6.0f && !c.calls);
    assert(af_v3_insect_spawn_terms(&terms,&season,(SpawnDate){2005,1,1},rng,&c));
    assert(season.term==1 && season.offset==4 && terms.rate==1 && c.calls==1);
    season=(SpawnSeason){2,1};
    assert(af_v3_insect_spawn_terms(&terms,&season,(SpawnDate){2004,2,29},rng,&c));
    assert(terms.current==1 && terms.next==2 && terms.rate==5.0f/6.0f);
    assert(!af_v3_insect_spawn_terms(&terms,&season,(SpawnDate){2003,2,29},rng,&c));
    SpawnU16 fg[256]={0},deposits[16]={0};SpawnU32 collision[256]={0};
    InsectHabitat habitat={fg,deposits,collision,0,0};
    /* Each added species reaches its actual creation representation. */
    static const unsigned areas[]={2,11,7,0,10,0,8,3};
    for (unsigned type=32;type<40;type++) {
        for (unsigned i=0;i<256;i++) {fg[i]=0xFFFF;collision[i]=7;}
        unsigned at=7*16+5,area=areas[type-32];habitat.weather=type==32?1:0;
        fg[at]=area==0?0x804:area==2?0x845:area==8?0x2806:area==10?0x63:0;
        collision[at]=area==7?12:0;plan(&p,type,area,100);
        c=(Context){.value=0,.fail=8};
        assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==0);
        assert(af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,0)==1);
        assert(c.count==1 && c.births[0].actor==type && c.births[0].x==5 && c.births[0].z==7);
        assert(c.births[0].colony==(type==38) && c.calls==3);
    }
    for (unsigned i=0;i<256;i++) {fg[i]=0;collision[i]=0;}
    habitat.weather=0;c=(Context){.value=.25f,.fail=8};
    plan(&p,39,3,10);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    c.value=.06f;plan(&p,39,3,10);assert(af_v3_insect_spawn_choose(&p,&habitat,0,0,rng,&c)==-1);
    plan(&p,39,3,10);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==0);
    c.value=0;plan(&p,39,3,10);assert(af_v3_insect_spawn_choose(&p,&habitat,6,1,rng,&c)==-2);
    c.value=.999f;plan(&p,39,3,10);assert(af_v3_insect_spawn_choose(&p,&habitat,6,1,rng,&c)==0);
    /* Candy/spoiled turnips suppress all ordinary rows, including no-spawn mass. */
    fg[7*16+5]=0x2806;p=(SpawnPlan){3,{{39,3,100},{38,8,1},{41,13,100}}};c.value=.9f;
    assert(af_v3_insect_spawn_choose(&p,&habitat,0,0,rng,&c)==1 && p.rows[0].weight==0 && p.rows[2].weight==0);
    habitat.weather=2;plan(&p,38,8,100);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    habitat.weather=0;deposits[7]=1<<5;plan(&p,38,8,100);
    assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    deposits[7]=0;fg[7*16+5]=0x2F03;plan(&p,28,9,100);c=(Context){.value=0,.fail=8};
    assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==0);
    assert(af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,0)==1 && c.births[0].extra==6);
    fg[7*16+5]=0x868;plan(&p,28,0,100);c=(Context){.value=0,.fail=8};
    assert(af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,0)==1 && c.births[0].extra==4);
    /* Source flower fallback happens after flying eligibility was cleared. */
    for (unsigned i=0;i<256;i++) {fg[i]=0xFFFF;collision[i]=7;}
    plan(&p,0,12,100);c.value=0;
    assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==0 && p.rows[0].area==3);
    assert(!af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,0));
    habitat.weather=1;plan(&p,0,12,100);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    habitat.weather=0;collision[7*16+5]=12;plan(&p,34,7,100);habitat.block=0x80;
    assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    habitat.block|=0x8000;plan(&p,34,7,100);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==0);
    habitat.block=0;for (unsigned i=0;i<256;i++) {fg[i]=0;collision[i]=0;}
    /* Full source groups choose distinct tiles and stop when creation fails. */
    plan(&p,10,3,100);c=(Context){.value=.99f,.fail=8};
    int last=0;
    assert(af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,&last)==8 && c.calls==9 && last==1);
    for (unsigned i=0;i<8;i++) for (unsigned j=0;j<i;j++)
        assert(c.births[i].x!=c.births[j].x || c.births[i].z!=c.births[j].z);
    c=(Context){.value=.99f,.fail=2};
    assert(af_v3_insect_spawn_group(p.rows,&habitat,data,bytes,rng,create,&c,&last)==2 && last==0);
    assert(!af_v3_insect_spawn_tree(0x800) && !af_v3_insect_spawn_tree(0x808) && af_v3_insect_spawn_tree(0x867));
    p.count=65;assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    plan(&p,39,3,NAN);assert(af_v3_insect_spawn_choose(&p,&habitat,6,0,rng,&c)==-1);
    free(data);printf("%u insect calendars and complete shared habitat/creation checks pass\n",cases);
}
