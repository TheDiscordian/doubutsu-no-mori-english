/* Source-category camping trades, retaining the ordinary conversation body. */
#include "camper_trade.h"

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

static void camping_goods(u16 *out, const void *animal, int category,
                         const u16 *existing, int count, int route) {
    /* The house roll follows the list roll, including on tent-list rewards. */
    if (category == 0 && (int)(native_random() * 10.0f) == 0) {
        *out = native_house_item(animal);
        if (*out) return;
    }
    if (route && category == 0) {
        reward_goods(0,out,1,existing,count,category,(route<<8)|8);
        return;
    }
    int list = 8;
    if (route && (category == 3 || category == 4)) {
        /* The donor camping list persists for subsequent carpet/wall candidates.
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
    int summer = native_scene == 35;
    if (!summer && (native_scene != 31 || !reward_count(19))) {
        native_trade_original(picker, animal, categories, count, mode);
        return;
    }
    u16 item;
    native_trade_state.item_index = picker(&item);
    if (native_trade_state.item_index >= 0) {
        native_item_name(item, 0);
        native_trade_state.items[0] = item;
    }
    int route = 0;
    for (int i = 0; i < count; ++i) {
        int category = categories[i];
        if (category == 5) item = native_other_fruit();
        else if (category == 2) {
            u16 existing[3] = {native_trade_state.items[0], native_trade_state.items[1], native_private->shirt};
            camping_goods(&item, animal, category, existing, 3, route);
        } else {
            if (category == 0 && (int)(native_random() * 100.0f) >= (summer ? 80 : 90))
                route = summer ? 23 : 19;
            camping_goods(&item, animal, category, native_trade_state.items, 2, route);
        }
        native_trade_state.items[1 + i] = item;
        native_item_name(item, 1 + i);
    }
    item = mode ? 0x2512 : native_trade_state.items[1 + (int)(native_random() * (float)count)];
    native_trade_state.items[4] = item;
    native_item_name(item, 4);
}
