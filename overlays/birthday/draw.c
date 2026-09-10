/* Read-only English birthday drawing; native date selection/storage is retained. */
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned short u16;
typedef struct { u32 a, b; } Gfx;

extern void af_birthday_scale(float, float, float, int);
extern void af_birthday_translate(float, float, float, int);
extern void *af_birthday_matrix(void *);
extern void af_birthday_number(u8 *, unsigned int, int, int, int);
extern void af_birthday_font(void *, const u8 *, int, float, float,
                             int, int, int, int, int, int, float, float, int);

/* Immediate constants keep the replacement within the original relocation
 * allocation as well as the original function, without adding literal pointers. */
static inline float constant(u32 bits) {
#ifdef __mips__
    float result;
    __asm__("mtc1 %1,%0" : "=f"(result) : "r"(bits));
    return result;
#else
    union { u32 bits; float value; } result = {bits};
    return result.value;
#endif
}

static void *pointer(const void *data, unsigned offset) {
#ifdef __mips__
    return *(void *const *)((const u8 *)data + offset);
#else
    extern void *af_birthday_test_pointer(const void *, unsigned);
    return af_birthday_test_pointer(data, offset);
#endif
}

static void graph_end(void *graph, Gfx *end) {
#ifdef __mips__
    *(Gfx **)((u8 *)graph + 0x298) = end;
#else
    extern void af_birthday_test_graph_end(void *, Gfx *);
    af_birthday_test_graph_end(graph, end);
#endif
}

void af_birthday_draw(void *submenu, void *menu, void *game) {
    void *overlay = pointer(submenu, 0x2C);
    const u16 *birthday = pointer(overlay, 0x10710);
    const u8 *asset = pointer(menu, 0x28);
    void *graph = pointer(game, 0);
    float x = *(float *)((u8 *)menu + 0x18);
    float y = *(float *)((u8 *)menu + 0x1C);
    Gfx *gfx;
    unsigned s, t;
    int row;
    u8 day[2];

    af_birthday_scale(constant(0x41800000), constant(0x41800000), constant(0x3F800000), 0);
    af_birthday_translate(x, y, constant(0x430C0000), 1);
    gfx = pointer(graph, 0x298);
    gfx[0] = (Gfx){0xDB060030, (u32)(unsigned long)asset};
    gfx[1] = (Gfx){0xDA380003, (u32)(unsigned long)af_birthday_matrix(graph)};
    gfx[2] = (Gfx){0xDE000000, 0x0C000740};
    gfx[3] = (Gfx){0xE8000000, 0};
    s = (int)(-*(float *)((u8 *)overlay + 0x10698) * constant(0x40000000)) & 127;
    t = (int)(-*(float *)((u8 *)overlay + 0x1069C) * constant(0x40000000)) & 127;
    gfx[4] = (Gfx){0xF2000000 | s << 12 | t, (s + 124) << 12 | (t + 124)};
    gfx[5] = (Gfx){0xDE000000, 0x0C0012C8};
    graph_end(graph, gfx + 6);
    ((void (*)(void *))pointer(overlay, 0x106B4))(graph);
    af_birthday_number(day, birthday[1], 2, 0, 1);

    for (row = 0; row < 4; row++) {
        const u8 *text;
        int length, r, g, b;
        float tx, ty = constant(0x42F80000), scale = constant(0x3F800000);
        if (!row) {
            text = asset + 0x2DB8;
            length = 21; tx = constant(0x42EE0000); ty = constant(0x42B00000); scale = constant(0x3F600000);
            r = g = b = 255;
        } else {
            if (row == 1) {
                unsigned month = birthday[0];
                text = asset + 0x2DD0 + (month >= 1 && month <= 12 ? month - 1 : 12) * 10;
                length = 0;
                while (length < 9 && text[length]) length++;
                tx = constant(0x42C20000);
            } else if (row == 2) {
                text = day; length = 2; tx = constant(0x432B0000);
            } else {
                text = asset + 0x2E52; length = 2; tx = constant(0x43460000);
            }
            if (*(const int *)(birthday + 2) == row - 1) { r = 195; g = 0; b = 0; }
            else { r = 70; g = 145; b = 225; }
        }
        af_birthday_font(game, text, length, x + tx, -y + ty,
                         r, g, b, 255, 0, 0, scale, scale, 0);
    }
}
