#include <assert.h>
#include <stdint.h>
#include <string.h>

typedef unsigned char u8;
extern const u8 af_fishing_aliases[6368];
extern const u8 *af_fishing_resolve(const u8 *, const u8 *, int);
extern void af_fishing_name(void *, int, const u8 *, int);
static const u8 *got_name;
static int got_length, got_slot, calls;
static void *got_window;

void af_fishing_native_set(void *window, int slot, const u8 *name, int length) {
    got_window = window; got_slot = slot; got_name = name; got_length = length; ++calls;
}

static void check(u8 *id, int length, const u8 *expected, int expected_length) {
    u8 before[18];
    int old_calls = calls;
    void *window = (void *)(uintptr_t)0x12345678;
    if (id) memcpy(before, id - 1, 18);
    af_fishing_name(window, 0, id, length);
    assert(calls == old_calls + 1 && got_window == window && got_slot == 0);
    assert(got_name == expected && got_length == expected_length);
    if (id) assert(!memcmp(before, id - 1, 18));
}

int main(void) {
    const u8 marker[10] = {0x98, 0xA6, 0x8F, 0xA1, 0x20, 0x20, 0xFF, 0xFF, 0xFF, 0xFF};
    const u8 *rows = af_fishing_aliases + 64;
    u8 guarded[18], *id = guarded + 1;
    int n, i;
    memset(guarded, 0xA5, sizeof guarded);
    memcpy(id + 6, marker, 10);
    for (n = 0; n < 394; ++n) {
        const u8 *row = rows + n * 16;
        memcpy(id, row, 6);
        assert(af_fishing_resolve(id, rows, 394) == row + 8);
        check(id, 6, row + 8, 8);
        /* Every byte of the NPC-only shape participates in the type guard. */
        for (i = 6; i < 16; ++i) {
            id[i] ^= 1;
            check(id, 6, id, 6);
            id[i] ^= 1;
        }
        check(id, 5, id, 5);
        check(id, 8, id, 8);
    }
    memcpy(id, "Octavi", 6); /* A long English prefix is not an identity. */
    check(id, 6, id, 6);
    memset(id, 0xFF, 6); check(id, 6, id, 6);
    memset(id, 0, 6); check(id, 6, id, 6);
    check(0, 6, 0, 6);
    assert(!af_fishing_resolve(id, 0, 394));
    assert(!af_fishing_resolve(id, rows, 0));
    assert(!af_fishing_resolve(id, rows, 395));
    /* An ordinary player's name collision must never become an NPC name. */
    memcpy(id, rows, 6); memcpy(id + 6, "Town  ", 6);
    id[12] = 1; id[13] = 2; id[14] = 3; id[15] = 4;
    check(id, 6, id, 6);
    assert(guarded[0] == 0xA5 && guarded[17] == 0xA5);
    return 0;
}
