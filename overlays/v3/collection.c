/* Imported ownership follows native collection and live player-slot clearing. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern struct AfSaveRuntime af_collection_state;
extern u8 af_collection_players[4 * 0xBD0], *af_collection_active;
#define state (&af_collection_state)
#define players af_collection_players
#define active af_collection_active
#endif
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern int af_v3_furniture_import_profile(u32);
extern void af_v3_original_collect(u32);
extern void af_v3_original_private_clear(u8 *);

static u32 player_slot(const u8 *private) {
    for (u32 i = 0; i < 4; ++i)
        if (private == players + i * 0xBD0u) return i;
    return 4;
}

static int selected(u32 item) {
    return (item >> 12) == 3 &&
        af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2));
}

void af_v3_catalogue_record(u32 argument) {
    u32 item = (unsigned short)argument;
    if ((item >> 12) != 3) {
        af_v3_original_collect(argument);
        return;
    }
    if (!selected(item)) return;
    af_v3_require_save_state();
    u32 player = player_slot(active);
    /* A visiting player's Controller Pak catalogue needs its own transport.
     * Never silently credit a resident's slot or drop the acquired ownership. */
    if (player == 4) af_v3_save_halt(AF_SAVE_ARGUMENT);
    int result = af_v3_save_collect(state->working, player, item, 1);
    if (result < 0) af_v3_save_halt(result);
}

int af_v3_catalogue_owned(const u8 *private, u32 item) {
    u32 player = player_slot(private);
    if (player == 4 || !selected(item)) return 0;
    af_v3_require_save_state();
    int result = af_v3_save_collect(state->working, player, item, 0);
    if (result < 0) af_v3_save_halt(result);
    return result;
}

void af_v3_catalogue_clear(u8 *private) {
    u32 player = player_slot(private);
    if (player < 4) {
        af_v3_require_save_state();
        u8 *catalogue = state->working + AF_SAVE_PROFILE + player * 128u;
        for (u32 i = 0; i < 128; ++i) catalogue[i] = 0;
#ifdef AF_V3_CLOTHING_PROFILE
        catalogue = state->working + AF_SAVE_PROFILE + 512 + player*32;
        for (u32 i = 0; i < 32; ++i) catalogue[i] = 0;
#endif
    }
    af_v3_original_private_clear(private);
}
