/* Keep the donor's per-conversation click mode separate from native status
 * bits. The original voice selector still honours the player's silent setting.
 * Message initialization, not the later appear request, ends this lifetime. */
#include "carried_event.h"
extern int af_cw_prior_sound_animal(void *);
extern void af_cw_prior_message_init(void *);
extern void af_cw_native_system_sound(u32);
extern const u16 af_cw_system_sounds[2];
static void *click_window;

void mMsg_sound_set_voice_click(void *window) {
    if(window && window==mMsg_Get_base_window_p())click_window=window;
}
int af_cw_sound_animal(void *window) {
    return window && window!=click_window?af_cw_prior_sound_animal(window):0;
}
void af_cw_message_init(void *game) {
    click_window=0;
    af_cw_prior_message_init(game);
}
void sAdo_SysTrgStart(u32 word) {
    if(word==0x6B)af_cw_native_system_sound(af_cw_system_sounds[0]);
    else if(word==0x16C)af_cw_native_system_sound(af_cw_system_sounds[1]);
}
