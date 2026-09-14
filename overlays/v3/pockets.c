/* Furniture searches include selected imports without changing saved pockets. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Pockets { u8 prefix[0x14]; u16 items[15], padding; u32 conditions; };
_Static_assert(__builtin_offsetof(struct Pockets, items) == 0x14, "Native pocket offset");
_Static_assert(__builtin_offsetof(struct Pockets, conditions) == 0x34, "Native condition offset");
extern u32 af_v3_room_value(u32, u32);
extern int af_v3_original_pocket_index(const struct Pockets *, u32, u32);
extern int af_v3_original_pocket_count(const struct Pockets *, u32, u32);

static int search(const struct Pockets *private, u32 condition, int count) {
    int total = 0;
    if (private) {
        for (u32 i = 0; i < 15; ++i) {
            if (((private->conditions >> (i * 2)) & 3u) == condition &&
                    af_v3_room_value(private->items[i], 2) == 1u) {
                if (!count) return (int)i;
                ++total;
            }
        }
    }
    return count ? total : -1;
}

int af_v3_pocket_index(const struct Pockets *private, u32 kind, u32 condition) {
    if ((u16)kind != 1) return af_v3_original_pocket_index(private, kind, condition);
    return search(private, condition, 0);
}

int af_v3_pocket_count(const struct Pockets *private, u32 kind, u32 condition) {
    if ((u16)kind != 1) return af_v3_original_pocket_count(private, kind, condition);
    return search(private, condition, 1);
}
