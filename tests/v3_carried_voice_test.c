#include <assert.h>
#include <stdio.h>
#include "carried_event.h"
static unsigned window,other,game_token,reads,resets,sounds,last_sound;
const u16 af_cw_system_sounds[2]={0x6F,0x175};
void *mMsg_Get_base_window_p(void) {return &window;}
int af_cw_prior_sound_animal(void *p) {assert(p==&window || p==&other);reads++;return 7;}
void af_cw_prior_message_init(void *p) {assert(p==&game_token);resets++;}
void af_cw_native_system_sound(u32 word) {last_sound=word;sounds++;}
extern int af_cw_sound_animal(void *);
extern void af_cw_message_init(void *);
int main(void) {
    assert(!af_cw_sound_animal(0) && !reads);
    assert(af_cw_sound_animal(&window)==7 && reads==1);
    mMsg_sound_set_voice_click(0);mMsg_sound_set_voice_click(&other);
    assert(af_cw_sound_animal(&window)==7 && reads==2);
    mMsg_sound_set_voice_click(&window);
    assert(!af_cw_sound_animal(&window) && reads==2);
    assert(af_cw_sound_animal(&other)==7 && reads==3);
    af_cw_message_init(&game_token);
    assert(resets==1 && af_cw_sound_animal(&window)==7 && reads==4);
    sAdo_SysTrgStart(0x6B);assert(sounds==1 && last_sound==0x6F);
    sAdo_SysTrgStart(0x16C);assert(sounds==2 && last_sound==0x175);
    sAdo_SysTrgStart(0);sAdo_SysTrgStart(0x816C);assert(sounds==2);
    puts("dialogue click lifetime, native delegation, and mapped system sounds pass");
    return 0;
}
