#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "npc_registry.h"
enum {ACTOR_BYTES=2612,STRIDE=2656};
static unsigned char areas[3][STRIDE*2] __attribute__((aligned(16)));
static unsigned char descriptors[3][32],profiles[3][36],draw[100];
static const AFNpcStreamRecord streams[3]={{.name=0xD090},{.name=0xD091},{.name=0xD092}};
const AFNpcExtras af_v3_npc_extras={AF_NPC_EXTRA_MAGIC,1,3,44,{
    {0xD090,0xCC,3,ACTOR_BYTES,2,STRIDE,areas[0],descriptors[0],draw,streams,281,448,449},
    {0xD091,0xCD,0,ACTOR_BYTES,2,STRIDE,areas[1],descriptors[1],draw,streams+1,281,448,449},
    {0xD092,0xCE,1,ACTOR_BYTES,2,STRIDE,areas[2],descriptors[2],draw,streams+2,281,448,449}}};
static unsigned previous[6];static int old_actor,old_descriptor;
static const unsigned char filename[]={0};
void *af_npc_previous_descriptor(int profile) {++previous[0];assert(profile==0xCA);return &old_descriptor;}
int af_npc_previous_allocate(void **out,const void *profile,void *descriptor,const unsigned char *file,unsigned short name) {
    ++previous[1];assert(profile==profiles[0] && descriptor==descriptors[0] && file==filename && name==0xE000);
    *out=&old_actor;return 17;
}
void af_npc_previous_free(void *actor) {++previous[2];assert(actor==&old_actor);}
void af_npc_allocation_failed(void *descriptor,unsigned short name) {
    ++previous[3];assert(name>=0xD090 && name<=0xD092 && descriptor==descriptors[name-0xD090]);
}
int af_npc_previous_draw(void *out,unsigned int name) {++previous[4];assert(out && name==0xE000);return 19;}
unsigned int af_npc_previous_voice(const unsigned char *data) {++previous[5];assert(data);return 55;}
static void be16(unsigned char *p,unsigned value) {p[0]=value>>8;p[1]=value;}
static void be32(unsigned char *p,unsigned value) {be16(p,value>>16);be16(p+2,value);}
static void init(void) {
    memset(areas,0,sizeof(areas));memset(descriptors,0,sizeof(descriptors));
    for(unsigned i=0;i<3;++i) {
        be16(profiles[i],0xCC+i);profiles[i][2]=3;
        be16(profiles[i]+8,0xD090+i);be32(profiles[i]+12,ACTOR_BYTES);
        for(unsigned j=0;j<2;++j) {
            unsigned *h=(unsigned *)(areas[i]+j*STRIDE),*g=(unsigned *)(areas[i]+(j+1)*STRIDE-16);
            h[0]=AF_NPC_SLOT_MAGIC;h[1]=0;h[2]=0xD090+i;h[3]=0xCC+i;
            for(unsigned n=0;n<4;++n)g[n]=AF_NPC_SLOT_GUARD;
        }
    }
    be16(draw,448);be16(draw+2,449);draw[0x5F]=255;
}
static void native_init(void *a) {
    memset(a,0,ACTOR_BYTES);be16(a,0xCC);be16((unsigned char *)a+6,0xD090);
    ++descriptors[0][0x1E]; /* Original Actor_make owns this increment. */
}
int main(void) {
    init();assert(af_v3_npc_extra_descriptor(0xCC)==descriptors[0]);
    assert(af_v3_npc_extra_descriptor(0xCA)==&old_descriptor && previous[0]==1);
    void *a=NULL,*b=NULL,*c=(void *)1;
    assert(af_v3_npc_extra_allocate(&a,profiles[0],descriptors[0],filename,0xE000)==17 && a==&old_actor);
    af_v3_npc_extra_free(a);assert(previous[2]==1);
    for(unsigned i=1;i<3;++i) {
        assert(!af_v3_npc_extra_allocate(&a,profiles[i],descriptors[i],filename,0xD090+i));
        assert(!a && previous[3]==i);
    }
    assert(af_v3_npc_extra_allocate(&a,profiles[0],descriptors[0],filename,0xD090)==1);
    assert(a==areas[0]+16 && !af_v3_npc_extra_owned(a));native_init(a);
    assert(af_v3_npc_extra_owned(a)==af_v3_npc_extras.rows);
    assert(af_v3_npc_extra_allocate(&b,profiles[0],descriptors[0],filename,0xD090)==1);
    assert(b==areas[0]+STRIDE+16);native_init(b);
    assert(!af_v3_npc_extra_allocate(&c,profiles[0],descriptors[0],filename,0xD090) && !c);
    assert(descriptors[0][0x1E]==2 && previous[3]==3);
    unsigned char saved[ACTOR_BYTES];memcpy(saved,a,ACTOR_BYTES);
    af_v3_npc_extra_free(a);assert(descriptors[0][0x1E]==1 && !memcmp(saved,a,ACTOR_BYTES));
    assert(!af_v3_npc_extra_owned(a));af_v3_npc_extra_free(a);assert(descriptors[0][0x1E]==1);
    assert(af_v3_npc_extra_allocate(&c,profiles[0],descriptors[0],filename,0xD090)==1 && c==a);
    native_init(c);assert(descriptors[0][0x1E]==2);
    unsigned char out[104];memset(out,0xA5,sizeof(out));
    assert(af_v3_npc_extra_draw(out,0xD090)==1 && !memcmp(draw,out,100));
    for(unsigned i=100;i<104;++i)assert(out[i]==0xA5);
    assert(af_v3_npc_extra_voice(out)==281);
    out[80]^=1;assert(af_v3_npc_extra_voice(out)==55 && previous[5]==1);
    assert(af_v3_npc_extra_draw(out,0xE000)==19 && previous[4]==1);
    assert(af_v3_npc_stream_record(0xD090)==streams && !af_v3_npc_stream_record(0xE000));
    /* Corruption quarantines the slot without corrupting original NPC state. */
    ((unsigned *)(areas[0]+STRIDE-16))[3]^=1;
    assert(!af_v3_npc_extra_owned(a));af_v3_npc_extra_free(a);
    assert(descriptors[0][0x1E]==2 && ((unsigned *)areas[0])[1]==1 && previous[2]==1);
    af_v3_npc_extra_free(b);assert(descriptors[0][0x1E]==1);
    assert(!af_v3_npc_extra_allocate(&c,profiles[0],descriptors[0],filename,0xD090) && !c);
    init();be32(profiles[0]+12,2400);
    assert(!af_v3_npc_extra_allocate(&c,profiles[0],descriptors[0],filename,0xD090));
    assert(!c && ((unsigned *)areas[0])[1]==0);
    puts("additional NPC registry: allocation/free/guards, inactive records, native fallback, complete drawing and full voice pass");
}
