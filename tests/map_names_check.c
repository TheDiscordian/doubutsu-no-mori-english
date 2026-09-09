#include <assert.h>
#include <string.h>

extern void af_map_init(void *);
extern void af_map_load_name(unsigned char *, const unsigned short *);
extern const unsigned char *af_map_name(const unsigned char *, int *);
extern float af_map_draw(void *, const unsigned char *, int, float, float,
                        int, int, int, int, int, int, float, float, int);

static unsigned char records[16][9];
static unsigned char player[9] = {'P', 'l', 'a', 'y', 'e', 'r', 0xF1, 0xF2, 0xF3};
static unsigned char expected[8];
static int expected_length;
static unsigned int full_calls, init_calls;
static int reject;
static int game, submenu;

void af_map_native_init(void *p) { assert(p == &submenu); ++init_calls; }
void af_map_native_name(unsigned char *out, const unsigned short *id) {
    memset(out, id ? 'A'+(*id & 15) : '?', 6);
}
int af_load_display_name(unsigned char *out, unsigned int capacity, unsigned int id) {
    unsigned int i;
    assert(capacity == 8); ++full_calls;
    for (i = 0; i < 8; ++i) out[i] = (unsigned char)('A'+(id+i)%26);
    return !reject; /* Deliberately writes even on failure to test staging. */
}
float af_map_native_draw(void *p, const unsigned char *text, int length,
                         float x, float y, int r, int g, int b, int a,
                         int reverse, int cut, float sx, float sy, int mode) {
    assert(p == &game && length == expected_length && !memcmp(text, expected, length));
    assert(x == 120.0f && y == 53.0f && sx == 0.75f && sy == 0.75f);
    assert(r == 255 && g == 75 && b == 40 && a == 255 && reverse == 0 && cut == 0 && mode == 0);
    return 13.5f;
}
static void draw(const unsigned char *name) {
    unsigned int before = full_calls;
    assert(af_map_draw(&game, name, 6, 120.0f, 53.0f,
                       255, 75, 40, 255, 0, 0, 0.75f, 0.75f, 0) == 13.5f);
    assert(full_calls == before);
}
int main(void) {
    unsigned int i, j;
    unsigned short id;
    int length;
    memset(records, 0xA5, sizeof(records));
    af_map_init(&submenu);
    for (i = 0; i < 15; ++i) {
        id = (unsigned short)(0xE000+i);
        af_map_load_name(records[i], &id);
        for (j = 6; j < 9; ++j) assert(records[i][j] == 0xA5);
        for (j = 0; j < 8; ++j) expected[j] = (unsigned char)('A'+(id+j)%26);
        expected_length = 8; draw(records[i]);
    }
    expected_length = 6; memcpy(expected, player, 6); draw(player);
    assert(player[6] == 0xF1 && player[7] == 0xF2 && player[8] == 0xF3);
    /* Replacement and load failure cannot keep an earlier resident's name. */
    id = 0xE020; reject = 1;
    af_map_load_name(records[3], &id);
    memset(expected, 'A', 6); expected[6] = expected[7] = ' ';
    expected_length = 8; draw(records[3]);
    af_map_load_name(records[3], 0);
    memset(expected, '?', 6); draw(records[3]);
    id = 0xD008; reject = 0; af_map_load_name(records[3], &id);
    memset(expected, 'I', 6); draw(records[3]);
    assert(full_calls == 16); /* A special-actor ID is not an animal identity. */
    /* The hypothetical sixteenth key and player names retain native lengths. */
    id = 0xE001; af_map_load_name(records[15], &id);
    assert(full_calls == 16);
    expected_length = 6; memset(expected, 'B', 6); draw(records[15]);
    af_map_load_name(0, &id); assert(full_calls == 16);
    af_map_init(&submenu);
    for (i = 0; i < 16; ++i) {
        length = 6; assert(af_map_name(records[i], &length) == records[i] && length == 6);
    }
    length = 6; assert(!af_map_name(0, &length) && length == 6);
    reject = 0; af_map_load_name(records[15], &id);
    for (j = 0; j < 8; ++j) expected[j] = (unsigned char)('A'+(id+j)%26);
    expected_length = 8; draw(records[15]);
    assert(init_calls == 2 && full_calls == 17);
    return 0;
}
