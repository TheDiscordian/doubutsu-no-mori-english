#include "camper.h"
#ifdef __mips__
#define set_info(actor, animal) do { \
    *(camp_u8 **)((actor) + 0x174) = (animal); \
    *(void **)((actor) + 0x178) = 0; \
} while (0)
#else
extern void camper_test_set_info(camp_u8 *, camp_u8 *);
#define set_info camper_test_set_info
#endif

void af_v3_camper_npc_info(camp_u8 *actor, int index) {
    AfCamperAlias *alias;
    if (native_installed != 1 || actor[2] != 3 || actor[6] != 0xD0 || actor[7] != 0x8F) {
        original_npc_info(actor, index);
        return;
    }
    alias = native_event(0xD08F);
    /* Like GC, visitors have an Animal but no town NpcList/home record. */
    set_info(actor, alias && alias->use && alias->npc == camper_id()
        && alias->npc >= 0xE000 && alias->npc < 0xE0EE ? camper.animal : 0);
}
