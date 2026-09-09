/* Display-only map names. Packed native names, house data, and saves stay six-byte. */
#define AF_MAP_SLOTS 15

typedef struct {
    const unsigned char *native;
    unsigned char text[8];
} AfMapName;

static AfMapName names[AF_MAP_SLOTS];

extern void af_map_native_init(void *);
extern void af_map_native_name(unsigned char *, const unsigned short *);
extern int af_load_display_name(unsigned char *, unsigned int, unsigned int);
extern float af_map_native_draw(void *, const unsigned char *, int, float, float,
                               int, int, int, int, int, int, float, float, int);

void af_map_init(void *submenu) {
    unsigned int i;
    for (i = 0; i < AF_MAP_SLOTS; ++i) names[i].native = 0;
    af_map_native_init(submenu);
}

void af_map_load_name(unsigned char *destination, const unsigned short *identity) {
    unsigned int i, empty = AF_MAP_SLOTS;
    AfMapName *slot = 0;
    unsigned char complete[8];
    if (!destination) return;
    af_map_native_name(destination, identity);
    for (i = 0; i < AF_MAP_SLOTS; ++i) {
        if (names[i].native == destination) { slot = names+i; break; }
        if (!names[i].native && empty == AF_MAP_SLOTS) empty = i;
    }
    if (!slot && empty < AF_MAP_SLOTS) slot = names+empty;
    if (!slot) return;
    slot->native = destination;
    /* A rejected resource uses this newly generated native name, never a stale
       English name. Stage the load so partial failure cannot leak to drawing. */
    for (i = 0; i < 8; ++i) slot->text[i] = i < 6 ? destination[i] : ' ';
    if (identity && *identity >= 0xE000 && *identity < 0xE0D8
            && af_load_display_name(complete, 8, *identity))
        for (i = 0; i < 8; ++i) slot->text[i] = complete[i];
}

const unsigned char *af_map_name(const unsigned char *native, int *length) {
    unsigned int i;
    if (native) {
        for (i = 0; i < AF_MAP_SLOTS; ++i) {
            if (names[i].native == native) {
                *length = 8;
                return names[i].text;
            }
        }
    }
    /* Player names and empty-house labels were never passed to the NPC loader. */
    return native;
}

float af_map_draw(void *game, const unsigned char *native, int length,
                  float x, float y, int r, int g, int b, int a,
                  int reverse, int cut, float scale_x, float scale_y, int mode) {
    const unsigned char *text = af_map_name(native, &length);
    return af_map_native_draw(game, text, length, x, y, r, g, b, a,
                              reverse, cut, scale_x, scale_y, mode);
}
