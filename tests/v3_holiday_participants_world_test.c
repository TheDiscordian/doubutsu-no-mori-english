/* Shared map readers with synthetic resources and native-service doubles.
 * No cartridge execution, random-algorithm equivalence, or rendering claim. */
#include <assert.h>
#include <string.h>
#include "holiday_participants.h"
#include "holiday_reserved.h"
const u32 af_hp_available=1;
const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={
    {.profile=0xD9,.event=15,.save=8,.part=7},
    {.profile=0xDA,.event=14,.save=9,.part=7},
    {.profile=0xDB,.event=1,.save=7,.part=7},
    {.source_name=0xD02D,.name=0xD0A0,.profile=0xDC,.event=15,.count=1,.part=3},
    {.source_name=0xD02E,.name=0xD0A1,.profile=0xDD,.event=15,.count=4,.part=3},
    {.source_name=0xD05F,.name=0xD0A5,.profile=0xDE,.event=14,.count=1,.part=3},
    {.source_name=0xD060,.name=0xD0A6,.profile=0xDF,.event=14,.count=4,.part=3},
    {.source_name=0xD058,.name=0xD0AA,.profile=0xE0,.event=1,.count=4,.part=3},
};
/* Complete format directory, with three synthetic shrine layouts. */
const u8 af_holiday_transition_maps[1496]={
    'A','F','H','M',0,1,0,17,0,0,0,20,0,0,5,216,
    [16+2*20]=0,15,0,5,1,6,0,31,0x24,0x14,0,0,0,0,0,4,0,0,1,100,
    [16+5*20]=0,14,0,5,1,6,0,31,0x24,0x14,0,0,0,0,0,4,0,0,1,124,
    [16+7*20]=0,1,0,4,1,8,0,31,0,0,0,0,0,0,0,4,0,0,1,148,
    [356]=0xD0,0x2D,1,1, 0xD0,0x2E,3,1, 0xD0,0x2F,5,1,
          0xD0,0x30,7,1, 0xD0,0x31,9,1, 0xD0,0x74,12,1,
    [380]=0xD0,0x5F,1,3, 0xD0,0x60,3,3, 0xD0,0x61,5,3,
          0xD0,0x62,7,3, 0xD0,0x63,9,3, 0xD0,0x74,12,3,
    [404]=0xD0,0x58,1,7, 0xD0,0x59,3,7, 0xD0,0x5A,5,7,
          0xD0,0x5B,7,7, 0xD0,0x5C,9,7, 0xD0,0x3D,1,12,
          0x58,0x31,5,12, 0xD0,0x74,12,12,
};
static unsigned int active;
static int errors,initials,refills,bindings,allow=1,player=1;
static u8 areas[3][5];
u8 af_hp_native_animals[15][0x528];
static int group(int event) {return event==15?0:event==14?1:event==1?2:-1;}
int af_holiday_native_type(unsigned int event) {return group(event)>=0?(int)event+71:-1;}
int af_hp_native_event_status(int event,int mask) {assert(mask==AF_HE_ACTIVE);return !!(active&(1u<<group(event-71)));}
void af_hp_native_event_error(int event,int mask) {assert(group(event-71)>=0 && mask==AF_HE_ERROR);++errors;}
int af_hp_native_pool_variant(void) {assert(!"Shrine must not query pool shape");return -1;}
void *mEv_get_save_area(int event,int slot) {assert(slot==15 && group(event)>=0);return areas[group(event)];}
AFHPPrivate *af_hp_private(void) {static AFHPPrivate p;return player?&p:0;}
void af_hp_native_joint_initial(u8 *area,int count) {
    ++initials;assert(count==4 || count==5);
    for(int i=0;i<5;i++)assert(area[i]==255);
    for(int i=0;i<count;i++)area[i]=(u8)i;
}
void af_hp_native_joint_removed(u8 *area,int count) {
    assert(count==4 || count==5);unsigned int seen=0;
    for(int i=0;i<count;i++)if(area[i]!=255) {assert(area[i]<15 && !(seen&(1u<<area[i])));seen|=1u<<area[i];}
}
void af_hp_native_joint_refill(u8 *area,int count) {(void)area;(void)count;++refills;}
int af_hp_native_resident_valid(int id,u16 name) {return id>=0 && id<15 && name==0xE000+id;}
int af_hp_native_sex(int looks) {assert(looks>=0 && looks<6);return looks&1;}
int af_hp_uniform(unsigned int source) {assert(!source || source==0x2414 || source==0x2415);return (int)source;}
int af_hp_resident_bind(u16 source,u16 npc,u16 cloth) {
    ++bindings;assert(npc>=0xE000 && npc<0xE00F);
    assert(cloth==0 || cloth==0x2414+!(af_hp_native_animals[npc-0xE000][11]&1));
    if(!allow)return -1;
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(r->count && source>=r->source_name && source-r->source_name<r->count)return r->name+source-r->source_name;
    }
    assert(!"Unregistered source role");return -1;
}
int af_decor_actor_resolve(u16 source) {return source==0x5831?0x5840:-1;}
int af_hp_native_structure(int x,int z,u16 name,int ux,int uz) {assert(name==0x5840);return x==ux && z==uz;}
float fqrand(void) {return .999f;}
int af_hp_world_previous_active(void) {return -1;}
int af_hp_world_previous_index(int event) {assert(event==3);return 7;}
unsigned int af_hp_world_previous_kind(int index) {assert(index==7);return 4;}
int af_hp_world_previous_count(int index) {assert(index==7);return 5;}
int af_hp_world_previous_all(int index) {assert(index==7);return 8;}
int af_hp_world_previous_position(int *x,int *z,int index,int slot) {assert(index==7 && slot==0);*x=6;*z=9;return 1;}
int af_hp_world_previous_named_position(u16 *name,int *x,int *z,int event,int slot) {assert(event==3);*name=0xD058;return af_hp_world_previous_position(x,z,7,slot);}
void af_hp_world_previous_initial(u8 *area,int event) {assert(event==3);area[0]=42;}
void af_hp_world_previous_refill(u8 *area,int event) {assert(event==3);area[0]=43;}
void af_hp_world_previous_name(u16 *name,int event,int animal,int slot) {assert(event==3 && animal==0 && slot==0);*name=0xD058;}
int af_hp_world_previous_random(u16 *name) {*name=0xE00E;return 1;}
int af_hp_world_previous_lap(int x,int z) {assert(x==0 && z==0);return 2;}
int af_hp_world_active(void),af_hp_world_index(int),af_hp_world_count(int),af_hp_world_all(int);
unsigned int af_hp_world_kind(int);
int af_hp_world_position(int *,int *,int,int),af_hp_world_named_position(u16 *,int *,int *,int,int);
void af_hp_world_initial(u8 *,int),af_hp_world_refill(u8 *,int),af_hp_world_name(u16 *,int,int,int);
int af_hp_world_random(u16 *),af_hp_world_lap(int,int);
int main(void) {
    for(int i=0;i<15;i++) {u16 name=(u16)(0xE000+i);memcpy(af_hp_native_animals[i],&name,2);af_hp_native_animals[i][11]=i%6;}
    int x=0,z=0;u16 name=0;
    assert(af_hp_world_active()==-1 && af_hp_world_index(3)==7);
    assert(af_hp_world_kind(7)==4 && af_hp_world_count(7)==5 && af_hp_world_all(7)==8);
    assert(af_hp_world_named_position(&name,&x,&z,3,0)==1 && name==0xD058 && x==6 && z==9);
    assert(af_hp_world_random(&name)==1 && name==0xE00E && af_hp_world_lap(0,0)==2);
    af_hp_world_initial(areas[0],3);assert(areas[0][0]==42);
    af_hp_world_refill(areas[0],3);assert(areas[0][0]==43);
    af_hp_world_name(&name,3,0,0);assert(name==0xD058);
    const int events[]={15,14,1},indices[]={17,20,22},first[]={0xD0A0,0xD0A5,0xD0AA};
    for(int r=0;r<3;r++) {
        int native=events[r]+71,count=r==2?4:5,index=indices[r];active=1u<<r;
        assert(af_hp_world_active()==native && af_hp_world_index(native)==index);
        assert(af_hp_world_kind(index)==4 && af_hp_world_count(index)==count && af_hp_world_all(index)==(r==2?8:6));
        af_hp_world_initial(areas[r],native);
        for(int i=0;i<count;i++) {
            name=(u16)(0xE000+i);af_hp_world_name(&name,native,i,i);assert(name==first[r]+i);
            assert(af_hp_world_named_position(&name,&x,&z,native,i)==1 && name==first[r]+i);
            assert(af_hp_world_position(&x,&z,index,i)==1 && x==1+i*2 && z==(r==2?7:1+r*2));
        }
        assert(af_hp_world_random(&name)==1 && name==0xE000+count-1);
        areas[r][1]=areas[r][0];areas[r][2]=15;areas[r][3]=255;areas[r][4]=0;
        af_hp_world_refill(areas[r],native);
        assert(areas[r][1]==255 && areas[r][2]==255 && areas[r][3]==255 && areas[r][4]==255);
        assert(af_hp_world_random(&name)==1 && name==0xE000);
        memset(areas[r],255,5);assert(!af_hp_world_random(&name));
    }
    assert(bindings==14 && initials==3 && refills==3 && !errors);
    active=4;
    assert(af_hp_world_lap(9,7)==1); /* unspawned fifth queue position */
    assert(af_hp_world_lap(5,12)==2 && af_hp_world_lap(15,0)==0);
    assert(!af_hp_world_named_position(&name,&x,&z,72,4)); /* no fabricated fifth actor */
    assert(af_hp_world_named_position(&name,&x,&z,72,5) && name==0xD091);
    assert(af_hp_world_named_position(&name,&x,&z,72,6) && name==0x5840);
    active=7;assert(af_hp_world_active()==86); /* source directory precedence */
    assert(!af_hp_world_kind(-1) && !af_hp_world_count(32) && !af_hp_world_all(99));
    assert(!af_hp_world_position(&x,&z,17,6) && !af_hp_world_position(0,&z,17,0));
    assert(!af_hp_world_named_position(&name,&x,&z,86,6));
    allow=0;areas[0][0]=0;name=0xE000;af_hp_world_name(&name,86,0,0);
    assert(errors==1 && name==0xD0A0); /* failed role cannot become an ordinary actor */
    player=0;af_hp_world_initial(areas[0],86);assert(initials==3);
    return 0;
}
