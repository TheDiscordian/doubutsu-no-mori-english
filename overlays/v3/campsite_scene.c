/* Additive summer-campsite scene bindings; no event or NPC substitution. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#ifdef __mips__
#define packet ((const u8 *)0x804A1000u)
#define scene_table ((u8 *)0x8010EAA0u)
#define native_block_info ((int (*)(void *, const void *))0x8008609Cu)
#define native_set_bg ((void (*)(void *, const void *, u16, u8, u16, int, int))0x80085918u)
#define native_set_fg ((void (*)(void *, const void *, u16))0x800859F4u)
#else
extern u8 af_campsite_packet[0x1000], af_campsite_scene_table[35 * 20];
extern int af_campsite_native_block_info(void *, const void *);
extern void af_campsite_native_set_bg(void *, const void *, u16, u8, u16, int, int);
extern void af_campsite_native_set_fg(void *, const void *, u16);
#define packet af_campsite_packet
#define scene_table af_campsite_scene_table
#define native_block_info af_campsite_native_block_info
#define native_set_bg af_campsite_native_set_bg
#define native_set_fg af_campsite_native_set_fg
#endif

static u16 be16(const u8 *p) { return ((u16)p[0] << 8) | p[1]; }
static int valid_packet(void) {
    return be16(packet) == 0x4146 && be16(packet + 2) == 0x4350
        && be16(packet + 4) == 0 && be16(packet + 6) == 1
        && be16(packet + 8) == 0 && be16(packet + 10) == 0x1000
        && be16(packet + 12) == 35 && be16(packet + 14) == 51;
}

/* The native caller clears the descriptor's byte 19, so this lives in the
 * loaded writable package, never in ROM or a temporary stack allocation. */
__attribute__((section(".entry")))
void *af_v3_campsite_scene_status(int scene) {
    if ((unsigned int)scene < 35u) return scene_table + scene * 20;
    if (scene == 35 && valid_packet()) return (void *)(packet + 0x20);
    return (void *)0;
}

int af_v3_campsite_room_sound(int scene) {
    /* Retain the complete native mapping. The gameplay overlay relocates, so
     * its linked 80804240 address is not a callable resident function address. */
    switch (scene) {
        case 20: return 1;
        case 6: case 9: case 12: case 14: case 18: case 21: case 31:
        case 35: return 2;
        case 17: case 22: case 23: case 24: case 25: case 29: return 3;
        default: return 0;
    }
}

int af_v3_campsite_block_info(void *field, const void *combination) {
    u8 *info = field;
    if (!info) return -1;
    if (be16(info) != 0x3012) return native_block_info(field, combination);
    if (!valid_packet() || info[0x166] != 1 || info[0x167] != 1
            || !combination || be16(combination) != 0x05BC) return -1;
#ifdef __mips__
    u8 *block = *(u8 **)(info + 0x148);
    if (!block || ((u32)block & 3u) || !*(void **)(block + 0x584)) return -1;
#else
    /* Host fixtures supply pointers separately; native fields remain 32-bit. */
    extern u8 *af_campsite_test_block;
    u8 *block = af_campsite_test_block;
    if (!block) return -1;
#endif
    /* Retain the engine's collision decoding, per-unit base-height cache,
     * sound-source positions, complete foreground copy, and haniwa markers. */
    native_set_bg(block, packet + 0x40, 0, 0xFF, 0xF3, 0, 0);
    native_set_fg(block + 0x580, packet + 0x480, 0x199);
    return 0;
}
