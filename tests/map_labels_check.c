#include <assert.h>
#include <string.h>

typedef struct { unsigned char first[8], second[8]; } AfMapLabel;
extern const AfMapLabel af_map_labels[6];
extern float af_map_label_draw(void *, const unsigned char *, int, float, float,
                              int, int, int, int, int, int, float, float, int);
static int game, calls;
static const unsigned char *expected[2];
static int lengths[2];
static float top;

float af_map_native_draw(void *p, const unsigned char *text, int length,
                         float x, float y, int r, int g, int b, int a,
                         int reverse, int cut, float sx, float sy, int mode) {
    assert(calls < 2 && p == &game);
    assert(length == lengths[calls] && !memcmp(text, expected[calls], length));
    assert(x == 77.0f && y == top+12.0f*calls);
    assert(r == 120 && g == 95 && b == 205 && a == 255);
    assert(reverse == 0 && cut == 0 && sx == 0.75f && sy == 0.75f && mode == 0);
    ++calls; return 10.0f*calls;
}

static float draw(const unsigned char *text, int length) {
    return af_map_label_draw(&game, text, length, 77.0f, top,
                             120, 95, 205, 255, 0, 0, 0.75f, 0.75f, 0);
}

int main(void) {
    static const char *first[] = {"Shop", "Police", "Post", "Wishing", "Train", "Dump"};
    static const char *second[] = {"", "Station", "Office", "Well", "Station", ""};
    unsigned char maximum[16];
    int i;
    assert(sizeof(AfMapLabel) == 16);
    memcpy(maximum, "ABCDEFGHabcdefgh", sizeof(maximum));
    for (i = 0; i < 6; ++i) {
        calls = 0; expected[0] = (const unsigned char *)first[i]; expected[1] = (const unsigned char *)second[i];
        lengths[0] = (int)strlen(first[i]); lengths[1] = (int)strlen(second[i]);
        top = lengths[1] ? 139.0f : 145.0f;
        assert(draw(af_map_labels[i].first, lengths[0]) == (lengths[1] ? 20.0f : 10.0f));
        assert(calls == (lengths[1] ? 2 : 1));
    }
    calls = 0; expected[0] = maximum; expected[1] = maximum+8;
    lengths[0] = lengths[1] = 8; top = 139.0f;
    assert(draw(maximum, 8) == 20.0f && calls == 2);
    calls = 0;
    assert(draw(0, 4) == 0.0f && draw(maximum, 0) == 0.0f && draw(maximum, 9) == 0.0f);
    assert(calls == 0);
    return 0;
}
