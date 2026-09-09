/* Full English inventory descriptions; native identities and actions stay native. */
typedef unsigned char u8;
static struct { const u8 *owner; u8 to[8], from[8], kind; } description;
extern int af_load_display_name(u8 *, unsigned int, unsigned int);
extern int af_tag_quest_names(u8 *, u8 *, int);
extern void af_tag_native_animal(u8 *, const u8 *);
extern void af_tag_native_special(u8 *, unsigned short);
extern float af_tag_native_draw(void *, const u8 *, int, float, float,
                               int, int, int, int, int, int, float, float, int);
#ifdef __mips__
static const u8 *cuts(void) { return (const u8 *)0x80106AF4u; }
#else
extern const u8 *af_tag_test_cuts(void);
#define cuts af_tag_test_cuts
#endif

static void copy(u8 *dst, const u8 *src, unsigned int n) {
    unsigned int i;
    for (i = 0; i < 8; ++i) dst[i] = i < n ? src[i] : ' ';
}

void af_tag_special(u8 *dst, unsigned short id) {
    if (!af_load_display_name(dst, 8, id)) {
        af_tag_native_special(dst, id);
        dst[6] = dst[7] = ' ';
    }
}

void af_tag_animal(u8 *dst, const u8 *identity) {
    unsigned int id = identity ? (identity[0] << 8) | identity[1] : 0;
    if (id < 0xE000 || id >= 0xE0D8 || !af_load_display_name(dst, 8, id)) {
        af_tag_native_animal(dst, identity);
        dst[6] = dst[7] = ' ';
    }
}

static void mail_name(u8 *dst, const u8 *name) {
    if (name[0x10] == 1 && name[0x0C] < 216 &&
        af_load_display_name(dst, 8, 0xE000u | name[0x0C])) return;
    /* Museum is a typed canonical identity, including in existing Japanese
       saves. Translate its display spelling without changing that identity. */
    copy(dst, name[0x10] == 2 ? (const u8 *)"Museum" : name, 6);
}

/* Explicit lengths retain the meaningful space after each prefix. */
static const u8 letter[] = "Letter to", delivery[] = "Delivery for";
static const u8 fortune[] = "fortune", from[] = "from ", the[] = "the ", possessive[] = "'s";
static const u8 home[] = "home", hra[] = "the HRA";
static const u8 colours[][3] = {{90,60,50}, {205,40,40}, {100,65,195},
    {60,150,65}, {165,30,255}, {60,50,155}};

static unsigned int length(const u8 *s, unsigned int n) {
    while (n && s[n-1] == ' ') --n;
    return n;
}

static unsigned int pixels(const u8 *s, unsigned int n) {
    unsigned int i, width = 0;
    const u8 *table = cuts();
    for (i = 0; i < n; ++i) width += table[s[i]] <= 12 ? 12-table[s[i]] : 12;
    return width;
}

/* The same segment walk computes the window width and draws each complete line.
   No DMA occurs during drawing, and no GC-only font control is transplanted. */
static __attribute__((section(".description_lines"), noinline))
unsigned int lines(void *game, float x, float y, float scale, float step) {
    unsigned int row, part, widest = 0, kind = description.kind;
    for (row = 0; row < 3; ++row) {
        const u8 *text[2]; unsigned int n[2], col[2], width = 0;
        text[0] = text[1] = from; n[0] = n[1] = col[0] = col[1] = 0;
        if (row == 2) {
            text[0] = from; n[0] = 5;
            text[1] = description.from; n[1] = length(text[1], 8);
            col[1] = kind == 3 || kind == 9 ? 3 : kind == 5 ? 4 :
                     kind == 6 || kind == 7 || kind == 8 ? 5 : 2;
        } else if (row == (kind == 8 ? 1u : 0u)) {
            text[0] = kind == 1 ? delivery : kind == 8 ? fortune : letter;
            n[0] = kind == 1 ? 12 : kind == 8 ? 7 : 9;
        } else if (kind == 4) {
            text[0] = the; n[0] = 4;
            text[1] = description.to; n[1] = length(text[1], 8); col[1] = 3;
        } else {
            text[0] = description.to; n[0] = length(text[0], 8); col[0] = 1;
            if (kind == 8) { text[1] = possessive; n[1] = 2; }
        }
        for (part = 0; part < 2; ++part) {
            if (game && n[part]) {
                const u8 *c = colours[col[part]];
                af_tag_native_draw(game, text[part], (int)n[part], x+width*scale, y+row*step,
                                   c[0], c[1], c[2], 255, 0, 1, scale, scale, 0);
            }
            width += pixels(text[part], n[part]);
        }
        if (width > widest) widest = width;
    }
    return widest;
}

int af_tag_description_prepare(const u8 *tag, const u8 *mail, int index) {
    unsigned int kind = tag[2];
    description.owner = 0;
    description.kind = (u8)kind;
    copy(description.to, tag+0x44, 6); copy(description.from, tag+0x4E, 6);
    if (kind == 1) {
        /* A private copy of the native quest resolver changes only its five
           name calls. Lookup, first-job substitution, and success stay native. */
        af_tag_quest_names(description.to, description.from, index);
    } else if (mail) {
        mail_name(description.to, mail);
        switch (mail[0x28]) {
            case 0: mail_name(description.from, mail+0x12); break;
            case 1: af_tag_special(description.from, 0xD00F); break;
            case 2: case 7: af_tag_special(description.from, 0xD008); break;
            case 3: af_tag_special(description.from, 0xD001); break;
            case 4: copy(description.from, home, 4); break;
            case 5: af_tag_special(description.from, 0xD03D); break;
            case 8: af_tag_special(description.from, 0x800D); break;
            default: copy(description.from, hra, 7); break;
        }
    }
    description.owner = tag;
    kind = (lines(0, 0, 0, 0, 0)+11)/12;
    return kind < 4 ? 4 : (int)kind;
}

void af_tag_description_draw(void *game, const u8 *tag, float x, float y,
                             float scale, float column, float step) {
    (void)column;
    if (description.owner == tag && description.kind == tag[2])
        lines(game, x, y, scale, step);
}
