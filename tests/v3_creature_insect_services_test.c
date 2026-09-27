#include "creature_insect_effects.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

const u16 af_insect_trigger_words[2]={0x71,0x451};
static xyz_t position={12,30,45};
static u32 owner,sound;
static int route,count,type,prio,a,b,fail;
static u16 item;
static s16 angle;
static GAME *game=(GAME *)(uintptr_t)0x1234;
static AfInsectEffect effect;
static void capture(u32 o,u32 s,xyz_t *p,int r) {
    assert(p==&position);owner=o;sound=s;route=r;count++;
}
void af_insect_native_sound(u32 o,u32 s,xyz_t *p) { capture(o,s,p,1); }
void af_insect_native_trigger(u32 s,xyz_t *p) { capture(0,s,p,2); }
void af_insect_native_chirp(u32 o,u32 s,xyz_t *p) { capture(o,s,p,3); }
static void request(int t,xyz_t p,int priority,s16 y,GAME *g,u16 name,s16 x,s16 z) {
    assert(!memcmp(&p,&position,sizeof p));assert(g==game);
    type=t;prio=priority;angle=y;item=name;a=x;b=z;count++;
}
static AfInsectEffect *create(s16 t,xyz_t p,xyz_t *off,GAME *g,void *arg,
        u16 name,int priority,s16 x,s16 z) {
    assert(!off && arg==&angle);
    request(t,p,priority,angle,g,name,x,z);
    if (fail) return 0;
    memset(&effect,0,sizeof effect);
    effect.scale.x=effect.scale.y=effect.scale.z=0.01f;
    effect.timer=15;effect.arg1=z;effect.velocity.y=4;
    return &effect;
}
static AfInsectEffectClip clip={.request=request,.create=create};
AfInsectEffectClip *af_insect_effect_clip=&clip;

int main(void) {
    const u32 loops[]={0x25,0x26,0x45,0xCF};
    for (unsigned i=0;i<4;i++) {
        count=0;sAdo_OngenPos(0xA123,loops[i],&position);
        assert(count==1 && route==1 && sound==loops[i] && owner==0xA123);
    }
    count=0;sAdo_OngenPos(42,0x44,&position);
    assert(count==1 && route==3 && sound==0x44 && owner==42);
    sAdo_OngenTrgStart(0x6A,&position);assert(route==2 && sound==0x71);
    sAdo_OngenTrgStart(0x438,&position);assert(route==2 && sound==0x451);
    count=0;sAdo_OngenTrgStart(0x6A,0);sAdo_OngenPos(42,0x44,0);
    sAdo_OngenPos(42,0x77,&position);sAdo_OngenTrgStart(0x77,&position);assert(count==0);
    for (int id=69;id<=70;id++) {
        af_insect_effect(id,position,1,123,game,0,id==69?1:4,0);
        assert(type==id && prio==1 && angle==123 && item==0 && a==(id==69?1:4) && b==0);
    }
    af_insect_effect(84,position,2,-123,game,0xFFFF,0,0x4005);
    assert(type==85 && prio==2 && angle==-123 && item==0xFFFF && a==0 && b==0x4005);
    for (int variant=0;variant<9;variant++) for (int mole=0;mole<2;mole++) {
        s16 flags=(s16)(variant|(mole?0x8000:0));
        AfInsectEffect *e=af_insect_mud_create(85,position,0,game,&angle,0xFFFF,2,0,flags);
        assert(e==&effect && b==flags && e->scale.x==0.01f && e->timer==15);
        e=af_insect_mud_create(85,position,0,game,&angle,0xFFFF,2,0,(s16)(flags|0x4000));
        assert(e==&effect && b==flags && e->arg1==flags && e->specific[2]==1);
        assert(e->scale.x==0.005f && e->scale.y==0.005f && e->scale.z==0.005f);
        assert(e->timer==15 && e->velocity.y==4);
    }
    fail=1;assert(!af_insect_mud_create(85,position,0,game,&angle,0xFFFF,2,0,0x4000));
    af_insect_effect_clip=0;count=0;
    af_insect_effect(84,position,2,0,game,0xFFFF,0,0x4000);
    assert(!af_insect_mud_create(85,position,0,game,&angle,0xFFFF,2,0,0x4000) && !count);
    puts("Complete field sound routing, high-bit mode, water, and small/native mud: passed");
}
