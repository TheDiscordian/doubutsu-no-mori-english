/* Complete field-sound routing for the added insect programs. */
#include "creature_insects.h"

extern const u16 af_insect_trigger_words[2];
extern void af_insect_native_sound(u32,u32,xyz_t *);
extern void af_insect_native_trigger(u32,xyz_t *);
extern void af_insect_native_chirp(u32,u32,xyz_t *);

void sAdo_OngenPos(u32 instance,u32 sound,xyz_t *position) {
    if (!position) return;
    if (sound==NA_SE_MOLE_CRICKET_HIDE) {
        /* GC routes 44 through its per-instance randomized chirp scheduler.
         * This is not an ordinary sustained channel. */
        af_insect_native_chirp(instance,sound,position);
    } else if (sound==NA_SE_25 || sound==NA_SE_26 ||
               sound==NA_SE_MOLE_CRICKET_OUT || sound==NA_SE_KA_BUZZ) {
        /* Retain CF's high-bit mode. The native dispatcher strips that bit
         * only after storing the mode, then selects the imported 4F program. */
        af_insect_native_sound(instance,sound,position);
    }
}

void sAdo_OngenTrgStart(u32 sound,xyz_t *position) {
    if (!position) return;
    if (sound==NA_SE_6A) af_insect_native_trigger(af_insect_trigger_words[0],position);
    else if (sound==NA_SE_438) af_insect_native_trigger(af_insect_trigger_words[1],position);
}
