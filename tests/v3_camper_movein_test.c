#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;
typedef unsigned int u32;
const volatile u32 native_installed = 1;
static u8 saved[40], animal[0x528], town[15*0x528];
static int has_save, lookups;
const u8 *native_event_save(int event, int area) {
    assert(event == 70 && area == 0); ++lookups;
    return has_save ? saved : 0;
}
int native_animal_search(u8 *animals, u32 id, int count) {
    for (int i=0;i<count;++i)
        if ((u32)(animals[i*0x528]*256+animals[i*0x528+1])==id) return i;
    return -1;
}
int native_animal_free(const u8 *a) {
    return a[0x4E1]==255 && a[0x4E2]==255 && (a[0]&0xF0)!=0xE0;
}
int af_v3_camper_movein_candidate(u8 *,u32,int);
int af_v3_camper_transfer_blocked(const u8 *);
static void identity(u8 *p,u32 id) { p[0]=id>>8;p[1]=id; }
int main(void) {
    const u32 identities[]={0xE000,0xE0EA,0xE0ED};
    for (unsigned i=0;i<sizeof(identities)/sizeof(*identities);++i) {
        u32 id=identities[i];identity(animal,id);identity(saved,id);has_save=0;
        assert(af_v3_camper_movein_candidate(town,id,15)==-1);
        assert(af_v3_camper_transfer_blocked(animal)==0);
        has_save=1;
        assert(af_v3_camper_movein_candidate(town,id,15)==0);
        assert(af_v3_camper_transfer_blocked(animal)==1);
        identity(saved,id^1);
        assert(af_v3_camper_movein_candidate(town,id,15)==-1);
        assert(af_v3_camper_transfer_blocked(animal)==0);
        identity(town+3*0x528,id);lookups=0;
        assert(af_v3_camper_movein_candidate(town,id,15)==3);
        assert(lookups==0);memset(town,0,sizeof(town));
    }
    identity(saved,0xD08F);identity(animal,0xD08F);lookups=0;
    assert(af_v3_camper_movein_candidate(town,0xD08F,15)==-1);
    assert(af_v3_camper_transfer_blocked(animal)==0);assert(lookups==0);
    animal[0x4E1]=animal[0x4E2]=255;
    assert(af_v3_camper_transfer_blocked(animal)==1);assert(lookups==0);
    puts("pass: saved camper exclusion and native candidate/empty semantics");
}
