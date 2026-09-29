#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include "../overlays/v3/reward_shrine_owner.c"
static ACTOR actor;
static _Alignas(16) u32 descriptor[8];
void af_v3_save_halt(int code) {(void)code;abort();}
int main(void) {
    *(u32 *)(actor.native+0x170)=(u32)(__UINTPTR_TYPE__)descriptor;
    descriptor[0]=0x8D8EC0;descriptor[2]=0x80A0A1F0;descriptor[3]=0x80A0B2D8;
    for(unsigned i=0;i<3;++i) {
        descriptor[4]=0x80400000+i*0x10000;
        assert(af_rw_shrine_entry(&actor,0x80A0A240)==descriptor[4]+0x50);
        assert(af_rw_shrine_entry(&actor,0x80A0A358)==descriptor[4]+0x168);
        assert(af_rw_shrine_entry(&actor,0x80A0A7A4)==descriptor[4]+0x5B4);
        assert(af_rw_shrine_entry(&actor,0x80A0AB44)==descriptor[4]+0x954);
    }
    assert(!af_rw_shrine_entry(0,0x80A0A240));
    assert(!af_rw_shrine_entry(&actor,0x80A0A241) && !af_rw_shrine_entry(&actor,0x80A0B030));
    descriptor[0]++;assert(!af_rw_shrine_entry(&actor,0x80A0A240));descriptor[0]--;
    descriptor[2]++;assert(!af_rw_shrine_entry(&actor,0x80A0A240));descriptor[2]--;
    descriptor[3]--;assert(!af_rw_shrine_entry(&actor,0x80A0A240));descriptor[3]++;
    descriptor[4]++;assert(!af_rw_shrine_entry(&actor,0x80A0A240));
    descriptor[4]=0;assert(!af_rw_shrine_entry(&actor,0x80A0A240));
    return 0;
}
