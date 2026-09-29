#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_voice_native.c"
volatile s32 af_rw_native_voice_spec=4;
volatile RewardVoice af_rw_native_voices[2];
static int changes,emissions,last_spec;
void af_rw_native_spec_change(int spec) {
    changes++;last_spec=spec;af_rw_native_voice_spec=spec;
}
void af_rw_native_voice_emit(u8 code,s16 voice,u8 scale) {
    assert(code==5 && voice==284 && scale==1);emissions++;
}
int main(void) {
    unsigned char before[sizeof(af_rw_native_voices)];
    memset((void *)af_rw_native_voices,0xA5,sizeof(af_rw_native_voices));
    memcpy(before,(const void *)af_rw_native_voices,sizeof(before));
    af_rw_voice_emit(5,284,1);
    assert(!memcmp(before,(const void *)af_rw_native_voices,sizeof(before)) && emissions==1);
    af_rw_voice_spec(9);assert(changes==1 && last_spec==2 && af_rw_native_voice_spec==9);
    af_rw_voice_spec(9);assert(changes==1);
    af_rw_voice_emit(5,284,1);assert(emissions==2);
    for(unsigned i=0;i<2;i++) {
        assert(af_rw_native_voices[i].volume==0.7f && af_rw_native_voices[i].pitch==0.65f);
        memcpy(before+i*0x24+8,(const void *)&af_rw_native_voices[i].volume,4);
        memcpy(before+i*0x24+0x14,(const void *)&af_rw_native_voices[i].pitch,4);
    }
    assert(!memcmp(before,(const void *)af_rw_native_voices,sizeof(before)));
    af_rw_voice_spec(3);assert(changes==2 && last_spec==3 && af_rw_native_voice_spec==3);
    puts("Additional speech: source volume/pitch on both native voices, shared male sequence, unchanged unrelated state, and ordinary setting delegation pass. No audio is played.");
}
