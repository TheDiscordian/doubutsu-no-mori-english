/* Catalogue-local indices retain the native (item - 1000) / 4 encoding. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Preview { u16 index; u8 padding[0x746]; u32 profile; };
_Static_assert(__builtin_offsetof(struct Preview, profile) == 0x748, "Catalogue profile offset");
#ifdef __mips__
#define active (*(u8 *volatile *)0x80136FD8u)
#define profiles ((const u32 *)0x80465800u)
#else
extern u8 *af_catalogue_active;
extern u32 af_catalogue_profiles[1267];
#define active af_catalogue_active
#define profiles af_catalogue_profiles
#endif
extern int af_v3_catalogue_owned(const u8 *, u32);
extern int af_v3_furniture_import_profile(u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern int af_v3_native_catalogue_bit(const u32 *, int);
extern void af_v3_original_catalogue_program(struct Preview *);
extern int af_v3_native_catalogue_available(u32, int, int, void *);

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
    /* The builder proves these selected pilots belong to the donor's ordinary
     * A/C shop lists. This local query only decides whether a catalogue price
     * is shown; it does not replace the native town's rarity selection. */
    return category == 0 && (u32)list < 3 &&
        af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2));
}
