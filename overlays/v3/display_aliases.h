/* One metadata relationship serves conversion and every display reader.
 * Offsets 28/30 belong to the display's canonical 32-byte item record.
 * The forward index is immutable; selection is checked through the profile.
 */
#ifndef AF_V3_DISPLAY_ALIASES_H
#define AF_V3_DISPLAY_ALIASES_H
#define AF_V3_DISPLAY_ALIAS_RAM 0x804A0010u
#define AF_V3_DISPLAY_ALIAS_MAGIC 0x41464431u
#define AF_V3_DISPLAY_ALIAS_CAPACITY 58u
struct DisplayAliasIndex {
    unsigned int magic, count;
    struct { unsigned short parent, display; } rows[AF_V3_DISPLAY_ALIAS_CAPACITY];
};
#ifdef __mips__
#define display_alias_index ((const struct DisplayAliasIndex *)AF_V3_DISPLAY_ALIAS_RAM)
#define display_alias_items ((const unsigned short *)0x80498000u)
#else
extern struct DisplayAliasIndex af_v3_test_alias_index;
extern unsigned short af_v3_test_alias_items[1024*16];
#define display_alias_index (&af_v3_test_alias_index)
#define display_alias_items af_v3_test_alias_items
#endif

static inline const unsigned short *af_v3_raw_display_alias(unsigned int item) {
    if (item > 65535u || (item >> 12) != 3u) return 0;
    unsigned int slot = (item & 0xFFFu) >> 2;
    const unsigned short *row = display_alias_items + slot*16u;
    if (row[0] != 1024u+slot || row[1] != (item & 0xFFFCu) || !row[14]) return 0;
    return row+14;
}
#endif
