#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CLOTHING_PROFILE 1
#include "../overlays/v3/save_codec.c"

int main(void) {
    unsigned char state[AF_SAVE_STATE] = {0}, bank[AF_SAVE_BANK] = {0};
    unsigned char decoded[AF_SAVE_STATE], old[AF_SAVE_PROFILE] = {0};
    state[32+26] = 16;
    bank[8] = bank[0x2F68] = 0x30;
    bank[9] = bank[0x2F69] = 1;
    for (unsigned int player=0; player<4; ++player) {
        for (unsigned int rotation=0; rotation<4; ++rotation) {
            assert(af_v3_save_collect(state,player,0x3350+rotation,1)==1);
            assert(af_v3_save_collect(state,player,0x3350+rotation,0)==1);
        }
        assert(state[AF_SAVE_PROFILE+player*128+26]==16);
    }
    assert(af_v3_save_pack(bank,sizeof(bank),state)==AF_SAVE_OK);
    memset(decoded,0xA5,sizeof(decoded));
    assert(af_v3_save_check(bank,sizeof(bank),state,decoded)==AF_SAVE_OK);
    assert(memcmp(decoded,state,sizeof(state))==0);
    memset(decoded,0xA5,sizeof(decoded));
    assert(af_v3_save_check(bank,sizeof(bank),old,decoded)==AF_SAVE_PROFILE_MISSING);
    for (unsigned int i=0; i<sizeof(decoded); ++i) assert(decoded[i]==0xA5);
    /* An added profile remains compatible; all four residents retain ownership. */
    memcpy(old,state,sizeof(old)); old[32+27] = 1;
    assert(af_v3_save_check(bank,sizeof(bank),old,decoded)==AF_SAVE_OK);
    assert(memcmp(decoded,old,sizeof(old))==0);
    assert(memcmp(decoded+AF_SAVE_PROFILE,state+AF_SAVE_PROFILE,AF_SAVE_CATALOGUE)==0);
    puts("speed-bag rotations, four residents, save round trip, and missing-profile rejection pass");
    return 0;
}
