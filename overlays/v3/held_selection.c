/* Shared selected-equipment lookup. Original native equipment keeps its switch.
   Parent items use their canonical collection identity's saved-profile bit;
   preparing an equipment record does not select that item. */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 item; s8 kind; u8 passive; u16 profile_byte; u8 mask, ready; } Entry;
#ifdef __mips__
#define header ((const u32 *)0x804A8500u)
#define profile ((const u8 *)0x80460020u)
#else
extern u32 af_test_held_selection[188];
extern u8 af_test_held_profile[192];
#define header af_test_held_selection
#define profile af_test_held_profile
#endif

static const Entry *entries(void) {
    if (header[0] != 0x41464853u || header[1] != 1u ||
        header[2] != 92u || header[3] != sizeof(Entry)) return 0;
    return (const Entry *)(header + 4);
}

int af_v3_player_selected_equipment(u32 item) {
    u32 index = item - 0x2200u;
    if (index < 36u || index >= 92u) return -1;
    const Entry *table = entries();
    if (!table) return -1;
    const Entry *row = table + index;
    if (row->item != item || row->ready != 1u || row->kind < 36 || row->kind >= 115 ||
        row->passive > 1u || row->profile_byte < 32u || row->profile_byte >= 160u ||
        !row->mask || (row->mask & (row->mask - 1u)) ||
        !(profile[row->profile_byte] & row->mask)) return -1;
    return row->kind;
}

int af_v3_player_passive_equipment(int kind) {
    if ((u32)kind - 2u < 32u) return 1; /* Original umbrellas. */
    if ((u32)kind - 36u >= 79u) return 0;
    const Entry *table = entries();
    if (!table) return 0;
    for (u32 i = 36; i < 92; ++i) {
        const Entry *row = table + i;
        if (row->kind == kind && row->passive == 1u &&
            af_v3_player_selected_equipment(0x2200u + i) == kind) return 1;
    }
    return 0;
}
