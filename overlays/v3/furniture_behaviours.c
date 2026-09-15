/* Shared behaviour readers use the canonical sparse item record, not item IDs. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Item {
    u16 index, item, price;
    u8 size, enabled, name[16], catalogue_mask, action_sound, reserved[6];
};
_Static_assert(sizeof(struct Item) == 32, "Complete furniture metadata record");
_Static_assert(__builtin_offsetof(struct Item, action_sound) == 25, "Sound category field");
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_native_action_sound(int, int);
#ifdef __mips__
#define items ((const struct Item *)0x80498000u)
#define sounds ((const int *)0x8010D6C8u)
#else
extern struct Item af_test_furniture_records[1024];
extern int af_test_furniture_sounds[4];
#define items af_test_furniture_records
#define sounds af_test_furniture_sounds
#endif

int af_v3_furniture_action_sound(int index, int mode) {
    if ((u32)index < 947u) return af_v3_native_action_sound(index, mode);
    u32 slot = (u32)index - 1024u;
    if (slot >= 1024u || (u32)mode >= 2u) return -1;
    const struct Item *row = items + slot;
    u32 sound = row->action_sound;
    if (row->index != (u32)index || row->item != 0x3000u + slot*4u ||
        row->enabled != 1 || sound < 1u || sound > 2u ||
        !af_v3_furniture_import_profile((u32)index)) return -1;
    return sounds[(sound-1u)*2u + (u32)mode];
}
