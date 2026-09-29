/* The donor's additional speech setting uses the native male voice sequence,
 * with its own volume/pitch. Original settings and complete native playback
 * remain unchanged. Both alternating records must receive the new settings. */
#include "reward_event.h"
typedef struct {
    u8 before_volume[8];f32 volume;
    u8 before_pitch[8];f32 pitch;u8 rest[12];
} RewardVoice;
_Static_assert(sizeof(RewardVoice)==0x24,"Native alternating voice record");
_Static_assert(__builtin_offsetof(RewardVoice,pitch)==0x14,"Native speech pitch");
extern volatile s32 af_rw_native_voice_spec;
extern volatile RewardVoice af_rw_native_voices[2];
extern const f32 af_rw_voice_parameters[2];
extern void af_rw_native_spec_change(int),af_rw_native_voice_emit(u8,s16,u8);
void af_rw_voice_spec(int spec) {
    if(spec!=9) {af_rw_native_spec_change(spec);return;}
    if(af_rw_native_voice_spec==9)return;
    /* Source setting 9 starts the same complete sequence as setting 2. */
    af_rw_native_spec_change(2);
    af_rw_native_voice_spec=9;
}
void af_rw_voice_emit(u8 code,s16 voice,u8 scale) {
    if(af_rw_native_voice_spec==9)for(unsigned int i=0;i<2;i++) {
        af_rw_native_voices[i].volume=af_rw_voice_parameters[0];
        af_rw_native_voices[i].pitch=af_rw_voice_parameters[1];
    }
    af_rw_native_voice_emit(code,voice,scale);
}
