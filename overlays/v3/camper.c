/* The donor owns an Animal for a masked camper. N64's alias alone does not. */
#include "camper.h"

int af_v3_camper_register(camp_u32 mask, camp_u32 npc, camp_u32 cloth) {
    AfCamperAlias *alias;
    if (native_installed != 1 || mask != 0xD08F || npc < 0xE000 || npc >= 0xE0EE
            || camper.magic != 0x41464341 || camper.guard[0] != 0xAFCA11ED
            || !selected_villager((int)npc - 0xE000)) return 0;
    alias = native_event(mask);
    /* Never reinitialise an Animal while a live actor can reference it. */
    if (alias) return alias->use && alias->npc == npc && camper_id() == npc;
    if (native_free_event() < 0 || (camper.greeted && !native_private)) return 0;
    native_clear_animal(camper.animal);
    /* This public native entry is already extended for every selected import,
     * including islanders and their complete additive starting outfits. */
    native_set_index(camper.animal, (int)npc - 0xE000);
    if (camper_id() != npc) return 0;
    if (!cloth) cloth = ((camp_u32)camper.animal[0x520] << 8) | camper.animal[0x521];
    else if (cloth != 0xFE20 && !selected_outfit(cloth)) cloth = 0x2400;
    /* The native initializer at 800A7A28 starts memories at +10, not the
     * header comment's +0C: the memory struct requires eight-byte alignment. */
    if (camper.greeted) native_set_memory(native_private, camper.animal + 0x10);
    return native_register(mask, npc, npc, cloth);
}
