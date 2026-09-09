/* Complete names owned by the catalogue overlay, without widening native pages. */
#define AF_CATALOG_SLOTS 63
#define AF_CATALOG_NAME_BYTES 16

typedef struct {
    const unsigned char *native;
    unsigned char text[AF_CATALOG_NAME_BYTES];
} AfCatalogName;

static AfCatalogName names[AF_CATALOG_SLOTS];
static const unsigned char unavailable[] = "Name unavailable";

extern void af_catalog_native_init(void *);
extern void af_catalog_native_name(unsigned char *, unsigned short);
extern int af_load_item_name(unsigned char *, unsigned int, unsigned int);
extern float af_catalog_native_draw(void *, const unsigned char *, int, float, float,
                                    int, int, int, int, int, int, float, float, int);

void af_catalog_init(void *submenu) {
    unsigned int i;
    /* The native constructor calls initialization on every entry, including
       entries which reuse an already allocated native catalogue state. */
    for (i = 0; i < AF_CATALOG_SLOTS; ++i) names[i].native = 0;
    af_catalog_native_init(submenu);
}

void af_catalog_load_name(unsigned char *destination, unsigned short item) {
    unsigned int i, empty = AF_CATALOG_SLOTS;
    AfCatalogName *slot = 0;
    if (!destination) return;
    /* Preserve the original ten-byte compatibility fields and their strides. */
    af_catalog_native_name(destination, item);
    for (i = 0; i < AF_CATALOG_SLOTS; ++i) {
        if (names[i].native == destination) { slot = names+i; break; }
        if (!names[i].native && empty == AF_CATALOG_SLOTS) empty = i;
    }
    if (!slot && empty < AF_CATALOG_SLOTS) slot = names+empty;
    if (!slot) return; /* Draw reports an unavailable name; never read past state. */
    slot->native = destination;
    for (i = 0; i < AF_CATALOG_NAME_BYTES; ++i) slot->text[i] = unavailable[i];
    if (!af_load_item_name(slot->text, AF_CATALOG_NAME_BYTES, item)) {
        /* A rejected resource must not leave a stale or partially loaded name. */
        for (i = 0; i < AF_CATALOG_NAME_BYTES; ++i) slot->text[i] = unavailable[i];
    }
}

const unsigned char *af_catalog_name(const unsigned char *native) {
    unsigned int i;
    if (native) {
        for (i = 0; i < AF_CATALOG_SLOTS; ++i)
            if (names[i].native == native) return names[i].text;
    }
    return unavailable;
}

float af_catalog_draw(void *game, const unsigned char *native, int length,
                      float x, float y, int r, int g, int b, int a,
                      int reverse, int cut, float scale_x, float scale_y, int mode) {
    (void)length;
    return af_catalog_native_draw(game, af_catalog_name(native), AF_CATALOG_NAME_BYTES,
                                  x, y, r, g, b, a, reverse, cut, scale_x, scale_y, mode);
}
