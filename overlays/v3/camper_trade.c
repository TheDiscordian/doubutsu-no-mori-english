/* Optional summer trades, retaining the native non-summer conversation body. */
#include "camper_trade.h"

/* Actual GAFE01-r0 ftr_listTent, in donor order; stable additive item IDs. */
static const u16 tent_items[10] = {
    0x335C, 0x3360, 0x3364, 0x336C, 0x3370,
    0x339C, 0x33A4, 0x33A8, 0x33AC, 0x33B0
};

int af_v3_camper_pocket(u16 *out) {
    const struct TradePrivate *priv = native_private;
    u8 slots[15];
    int count = 0;
    if (!priv) return -1;
    for (int i = 0; i < 15; ++i) {
        u16 item = priv->items[i];
        if (((priv->conditions >> (2 * i)) & 3u) != 0 ||
                (native_scene == 35 && item == camper_last_gift)) continue;
        if (native_item_kind(item, 2) == 1 ||
                (item & 0xFF00u) == 0x2600 || (item & 0xFF00u) == 0x2700)
            slots[count++] = (u8)i;
    }
    if (!count) return -1;
    int index = slots[(int)(native_random() * (float)count)];
    *out = priv->items[index];
    return index;
}

static int excluded(u16 item, const u16 *existing, int count) {
    if (item == native_rare_item) return 1;
    for (int i = 0; i < count; ++i)
        if (existing && item == existing[i]) return 1;
    return 0;
}

static u16 tent_reward(const u16 *existing, int existing_count) {
    u16 selected[10];
    int count = 0, eligible = 0;
    for (int i = 0; i < 10; ++i)
        if (native_item_kind(tent_items[i], 2) == 1)
            selected[count++] = tent_items[i];
    if (!count) return 0;
    /* Match the donor's small-list duplicate allowance after optional filtering.
       Disabled items never re-enter this list, even when every choice overlaps. */
    for (int i = 0; i < count; ++i)
        if (count < existing_count + 1 || !excluded(selected[i], existing, existing_count))
            ++eligible;
    /* Defensive optional-profile fallback: do not spin on an exhausted list. */
    if (!eligible) return 0;
    for (;;) {
        u16 item = selected[(int)(native_random() * (float)count)];
        if (count < existing_count + 1 || !excluded(item, existing, existing_count)) return item;
    }
}

static void summer_goods(u16 *out, const void *animal, int category,
                         const u16 *existing, int count, int tent) {
    /* The house roll follows the list roll, including on tent-list rewards. */
    if (category == 0 && (int)(native_random() * 10.0f) == 0) {
        *out = native_house_item(animal);
        if (*out) return;
    }
    if (tent && category == 0) {
        *out = tent_reward(existing, count);
        if (*out) return;
    }
    int list = 8;
    if (tent && (category == 3 || category == 4)) {
        /* Donor TENT stays selected for subsequent carpet/wall candidates.
           Both lack that list and fall back to physical list A, not ABC rarity.
           The native priority mapping selects that same A list without adding
           unsupported list indices to the shorter N64 descriptor table. */
        u8 priorities[3];
        native_goods_priority(priorities, category);
        list = priorities[0];
    }
    native_random_goods(0, out, 1, existing, count, category, list);
}

void af_v3_camper_trade(PocketPicker picker, const void *animal,
                         const int *categories, int count, int mode) {
    if (native_scene != 35) {
        native_trade_original(picker, animal, categories, count, mode);
        return;
    }
    u16 item;
    native_trade_state.item_index = picker(&item);
    if (native_trade_state.item_index >= 0) {
        native_item_name(item, 0);
        native_trade_state.items[0] = item;
    }
    int tent = 0;
    for (int i = 0; i < count; ++i) {
        int category = categories[i];
        if (category == 5) item = native_other_fruit();
        else if (category == 2) {
            u16 existing[3] = {native_trade_state.items[0], native_trade_state.items[1], native_private->shirt};
            summer_goods(&item, animal, category, existing, 3, tent);
        } else {
            if (category == 0 && (int)(native_random() * 100.0f) >= 80) tent = 1;
            summer_goods(&item, animal, category, native_trade_state.items, 2, tent);
        }
        native_trade_state.items[1 + i] = item;
        native_item_name(item, 1 + i);
    }
    item = mode ? 0x2512 : native_trade_state.items[1 + (int)(native_random() * (float)count)];
    native_trade_state.items[4] = item;
    native_item_name(item, 4);
}
