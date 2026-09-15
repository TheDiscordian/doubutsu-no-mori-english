/* Catalogue-local indices retain the native (item - 1000) / 4 encoding. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#ifdef AF_V3_FURNITURE_TABLES
#include "furniture_tables.h"
#else
#define AF_V3_FURNITURE_CAPACITY 1267
#define AF_V3_FURNITURE_PROFILES 0x80465800u
#endif
struct Preview {
    u16 index; u8 padding[10]; float model_y; u8 padding2[0x738];
    u32 profile, unused74c; u16 type, timer; u32 price; float scale, height;
};
_Static_assert(__builtin_offsetof(struct Preview, profile) == 0x748, "Catalogue profile offset");
_Static_assert(sizeof(struct Preview) == 0x760, "Complete catalogue preview size");
#ifdef __mips__
#define active (*(u8 *volatile *)0x80136FD8u)
#define profiles ((const u32 *)AF_V3_FURNITURE_PROFILES)
#else
extern u8 *af_catalogue_active;
extern u32 af_catalogue_profiles[AF_V3_FURNITURE_CAPACITY];
#define active af_catalogue_active
#define profiles af_catalogue_profiles
#endif
extern int af_v3_catalogue_owned(const u8 *, u32);
extern int af_v3_furniture_import_profile(u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern int af_v3_native_catalogue_bit(const u32 *, int);
extern void af_v3_original_catalogue_program(struct Preview *);
extern int af_v3_native_catalogue_available(u32, int, int, void *);
#ifdef AF_V3_CLOTHING_CATALOGUE
extern void af_v3_original_catalogue_furniture_init(struct Preview *, u32);
#ifdef AF_V3_ALOHA_DISPLAY
static u32 display_pocket(u32 item) {
    item&=0xFFFCu;
    if (item==0x3AFCu || item==0x3868u || item==0x386Cu)
        return 0x3400u+((item-0x3800u)>>2);
    return 0;
}
#endif

void af_v3_catalogue_furniture_init(struct Preview *preview, u32 argument) {
    af_v3_original_catalogue_furniture_init(preview, argument);
    if (
#ifdef AF_V3_ALOHA_DISPLAY
            display_pocket((u16)argument) && af_v3_furniture_import_profile(1024u+((argument&0xFFFu)>>2))
#else
            ((u16)argument & 0xFFFCu) == 0x3AFCu && af_v3_furniture_import_profile(1727)
#endif
            ) {
        /* The native init already owns construction, geometry DMA, lighting,
         * animation, and price. Match its original clothing presentation. */
        preview->model_y = -4.0f;
        preview->scale = 1.0f;
        preview->height = 38.0f;
    }
}
#endif

int af_v3_catalogue_bit(const u32 *bits, int index) {
    if (index < 2048) return af_v3_native_catalogue_bit(bits, index);
    if (index > 3071 || !active || (const u8 *)bits != active + 0xAF0) return 0;
    return af_v3_catalogue_owned(active, 0x1000u + (u32)index * 4u);
}

void af_v3_catalogue_program(struct Preview *preview) {
    if (!preview) af_v3_save_halt(-1);
    u32 index = preview->index;
    if (index < 947) {
        af_v3_original_catalogue_program(preview);
        return;
    }
    if (index < 2048 || index > 3071 || !af_v3_furniture_import_profile(index - 1024))
        af_v3_save_halt(-7);
    /* Resident static profiles use the same native bank DMA and drawing code.
     * No copied program is needed; the original 2400-byte model buffer remains. */
    preview->profile = profiles[index - 1024];
}

int af_v3_catalogue_available(u32 argument, int category, int list, void *game) {
    u32 item = (u16)argument;
    if ((item >> 12) != 3) return af_v3_native_catalogue_available(argument, category, list, game);
#ifdef AF_V3_CLOTHING_CATALOGUE
#ifdef AF_V3_ALOHA_DISPLAY
    u32 garment=display_pocket(item);
    if (garment)
        return category==0 && (u32)list<3 && af_v3_furniture_import_profile(1024u+((item&0xFFFu)>>2)) &&
            af_v3_native_catalogue_available(garment,2,list,game);
#else
    if ((item & 0xFFFCu) == 0x3AFCu)
        return category == 0 && (u32)list < 3 && af_v3_furniture_import_profile(1727) &&
            af_v3_native_catalogue_available(0x34BFu, 2, list, game);
#endif
#endif
#ifdef AF_V3_GARDEN_ITEMS
    /* The donor excludes the post-office mailbox from ordering, but permits
     * the lottery gnome. Native furniture preview queries include list 5. */
    if ((item & 0xFFFCu) == 0x3294u) return 0;
    if ((item & 0xFFFCu) == 0x32A0u)
        return category == 0 && list == 5 && af_v3_furniture_import_profile(1192);
#endif
#ifdef AF_V3_WESTERN_ITEMS
    if ((item & 0xFFFCu) == 0x32BCu || (item & 0xFFFCu) == 0x3334u)
        return category == 0 && list == 3 &&
            af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2));
#endif
    /* The builder proves these selected pilots belong to the donor's ordinary
     * A/C shop lists. This local query only decides whether a catalogue price
     * is shown; it does not replace the native town's rarity selection. */
    return category == 0 && (u32)list < 3 &&
        af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2));
}
