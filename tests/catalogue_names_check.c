#include <assert.h>
#include <string.h>

extern void af_catalog_init(void *);
extern void af_catalog_load_name(unsigned char *, unsigned short);
extern const unsigned char *af_catalog_name(const unsigned char *);
extern float af_catalog_draw(void *, const unsigned char *, int, float, float,
                             int, int, int, int, int, int, float, float, int);

static unsigned char fields[64][12];
static unsigned int init_calls, old_calls, full_calls, draw_calls;
static unsigned int reject;
static int game, submenu;
static unsigned char expected[16];

static void make_name(unsigned char *out, unsigned int item) {
    unsigned int i;
    for (i = 0; i < 16; ++i) out[i] = (unsigned char)('A'+(i+item)%26);
}
void af_catalog_native_init(void *p) { assert(p == &submenu); ++init_calls; }
void af_catalog_native_name(unsigned char *out, unsigned short item) {
    assert(out); memset(out, item & 255, 10); ++old_calls;
}
int af_load_item_name(unsigned char *out, unsigned int size, unsigned int item) {
    assert(size == 16); ++full_calls; make_name(out, item);
    return item != reject;
}
float af_catalog_native_draw(void *p, const unsigned char *text, int length,
                            float x, float y, int r, int g, int b, int a,
                            int reverse, int cut, float sx, float sy, int mode) {
    assert(p == &game && length == 16 && !memcmp(text, expected, 16));
    assert(x == 120.0f && y == 53.0f && sx == 0.875f && sy == 0.875f);
    assert(r == 155 && g == 156 && b == 157 && a == 255 && reverse == 0 && cut == 0 && mode == 0);
    ++draw_calls; return 17.5f;
}
static void draw(unsigned int i) {
    unsigned int before = full_calls;
    assert(af_catalog_draw(&game, fields[i]+1, 10, 120.0f, 53.0f,
                           155, 156, 157, 255, 0, 0, 0.875f, 0.875f, 0) == 17.5f);
    assert(full_calls == before); /* No per-frame name DMA. */
}
int main(void) {
    unsigned int i, j, count;
    reject = 65535; memset(fields, 0xA5, sizeof(fields));
    af_catalog_init(&submenu);
    assert(!memcmp(af_catalog_name(0), "Name unavailable", 16));
    for (i = 0; i < 63; ++i) af_catalog_load_name(fields[i]+1, (unsigned short)(i+1));
    for (i = 0; i < 63; ++i) {
        assert(fields[i][0] == 0xA5 && fields[i][11] == 0xA5);
        for (j = 1; j <= 10; ++j) assert(fields[i][j] == i+1);
        make_name(expected, i+1); draw(i);
    }
    /* All native pages have keys; repeat loads update, never consume extra slots. */
    for (i = 0; i < 63; ++i) {
        af_catalog_load_name(fields[i]+1, (unsigned short)(i+201));
        make_name(expected, i+201); draw(i);
    }
    reject = 222;
    af_catalog_load_name(fields[4]+1, 222);
    memcpy(expected, "Name unavailable", 16); draw(4);
    af_catalog_load_name(fields[4]+1, 333);
    make_name(expected, 333); draw(4);
    count = full_calls;
    af_catalog_load_name(fields[63]+1, 400);
    assert(full_calls == count);
    memcpy(expected, "Name unavailable", 16); draw(63);
    assert(fields[63][0] == 0xA5 && fields[63][11] == 0xA5);
    af_catalog_load_name(0, 1);
    assert(full_calls == count);
    af_catalog_init(&submenu);
    for (i = 0; i < 64; ++i) assert(!memcmp(af_catalog_name(fields[i]+1), expected, 16));
    af_catalog_load_name(fields[63]+1, 400);
    make_name(expected, 400); draw(63);
    assert(init_calls == 2 && old_calls == 130 && full_calls == 129 && draw_calls == 130);
    return 0;
}
