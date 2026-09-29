#include <assert.h>
#include <stdlib.h>
#include "../overlays/v3/reward_house_owner.c"
static ACTOR actor;
static _Alignas(16) u32 descriptor[8];
void af_v3_save_halt(int code) {(void)code;abort();}
int main(void) {
    *(s16 *)&actor=0x66;
    *(u32 *)(actor.native+0x170)=(u32)(__UINTPTR_TYPE__)descriptor;
    descriptor[0]=0x3E90000;descriptor[2]=0x809BE720;descriptor[3]=0x809C0E50;
    for(unsigned i=0;i<3;++i) {
        descriptor[4]=0x80400000+i*0x10000;
        assert(af_rw_house_entry(&actor)==descriptor[4]+0xE64);
    }
    assert(!af_rw_house_entry(0));
    *(s16 *)&actor=0x65;assert(!af_rw_house_entry(&actor));*(s16 *)&actor=0x66;
    descriptor[0]++;assert(!af_rw_house_entry(&actor));descriptor[0]--;
    descriptor[2]++;assert(!af_rw_house_entry(&actor));descriptor[2]--;
    descriptor[3]--;assert(!af_rw_house_entry(&actor));descriptor[3]++;
    descriptor[4]++;assert(!af_rw_house_entry(&actor));
    descriptor[4]=0;assert(!af_rw_house_entry(&actor));
}
