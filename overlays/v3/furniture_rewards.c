/* Optional reward categories share canonical records and native handovers. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Item {
    u16 index, item, price;
    u8 size, enabled, name[16], catalogue_mask, action_sound, preview, reward;
    u8 reserved[4];
};
_Static_assert(sizeof(struct Item) == 32, "Complete furniture metadata record");
_Static_assert(__builtin_offsetof(struct Item, reward) == 27, "Reward category field");
extern int af_v3_furniture_import_profile(u32);
extern void af_v3_native_reward_goods(void *, u16 *, int, const u16 *, int, int, int);
extern float af_v3_reward_random(void);
#ifdef __mips__
#define items ((const struct Item *)0x80498000u)
#define rare (*(const volatile u16 *)0x80135C00u)
#else
extern struct Item af_test_reward_records[1024];
extern u16 af_test_reward_rare;
#define items af_test_reward_records
#define rare af_test_reward_rare
#endif

static int selected(u32 slot, u32 route) {
    const struct Item *row = items + slot;
    return row->reward == route && row->enabled == 1 &&
        row->index == 1024u + slot && row->item == 0x3000u + slot*4u &&
        af_v3_furniture_import_profile(row->index);
}

u32 af_v3_furniture_reward_count(u32 route) {
    u32 count=0;
    if (route && route<=255u)
        for (u32 slot=0;slot<1024u;++slot) count+=selected(slot,route)!=0;
    return count;
}

static int excluded(u16 item, const u16 *existing, int count) {
    if (item==rare) return 1;
    for (int i=0;i<count;++i) if (existing[i]==item) return 1;
    return 0;
}

/* High byte: optional donor category; low byte: unchanged native fallback.
 * Only the verified single-gift call shape uses this adapter. Other calls
 * retain the original seven arguments and the native implementation.
 */
void af_v3_furniture_reward_goods(void *game, u16 *out, int count,
        const u16 *existing, int existing_count, int kind, int encoded) {
    u32 route = (u32)encoded >> 8;
    if (route && route <= 255u && out && count == 1 && !kind &&
            (u32)existing_count<=15u && (existing || !existing_count)) {
        u32 total = 0, eligible = 0;
        for (u32 slot = 0; slot < 1024u; ++slot) {
            if (selected(slot, route)) {
                ++total;
                eligible += !excluded(items[slot].item,existing,existing_count);
            }
        }
        /* Avoid the source selector's infinite rejection when an optional
         * one-item profile consists entirely of the current rare item. */
        int duplicates = total < (u32)existing_count+1u;
        if (total && (eligible || duplicates)) {
            for (;;) {
                u32 pick = (u32)(af_v3_reward_random() * (float)total);
                if (pick >= total) pick = total - 1u;
                for (u32 slot = 0; slot < 1024u; ++slot) {
                    if (selected(slot, route) && !pick--) {
                        if (duplicates || !excluded(items[slot].item,existing,existing_count)) {
                            *out = items[slot].item;
                            return;
                        }
                        break;
                    }
                }
            }
        }
    }
    af_v3_native_reward_goods(game, out, count, existing, existing_count,
                             kind, route && route <= 255u ? encoded & 255 : encoded);
}
