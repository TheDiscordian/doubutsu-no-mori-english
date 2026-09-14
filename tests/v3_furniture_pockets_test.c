#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room.c"
#include "../overlays/v3/pockets.c"

static u32 missing, calls, expected_kind, expected_condition;
static const struct Pockets *expected_private;
int af_v3_furniture_import_profile(u32 index) {
    return index != missing && (index == 1161 || index == 1198);
}
int af_v3_original_pocket_index(const struct Pockets *private, u32 kind, u32 condition) {
    assert(private == expected_private && kind == expected_kind && condition == expected_condition);
    ++calls; return 71;
}
int af_v3_original_pocket_count(const struct Pockets *private, u32 kind, u32 condition) {
    assert(private == expected_private && kind == expected_kind && condition == expected_condition);
    ++calls; return 72;
}

int main(void) {
    struct { u32 before[4]; struct Pockets private; u32 after[4]; } record;
    memset(&record, 0xA5, sizeof(record));
    struct Pockets *p = &record.private;
    for (u32 slot = 0; slot < 15; ++slot) {
        for (u32 rotation = 0; rotation < 4; ++rotation) {
            for (u32 condition = 0; condition < 4; ++condition) {
                memset(p, 0, sizeof(*p));
                p->items[slot] = (slot & 1 ? 0x3224 : 0x32B8) + rotation;
                p->conditions = condition << (slot * 2);
                struct Pockets saved = *p;
                assert(af_v3_pocket_index(p, 1, condition) == (int)slot);
                assert(af_v3_pocket_count(p, 1, condition) == 1);
                assert(af_v3_pocket_index(p, 1, condition ^ 1) == -1);
                assert(af_v3_pocket_count(p, 1, condition ^ 1) == 0);
                assert(!memcmp(p, &saved, sizeof(*p)));
            }
        }
    }
    for (u32 i = 0; i < 15; ++i) p->items[i] = i & 1 ? 0x3224 : 0x1004;
    p->conditions = 0;
    assert(af_v3_pocket_index(p, 0x10001, 0) == 0);
    assert(af_v3_pocket_count(p, 0x10001, 0) == 15);
    missing = 1161;
    assert(af_v3_pocket_count(p, 1, 0) == 8);
    memset(p->items, 0, sizeof(p->items));
    p->items[14] = 0x3225;
    assert(af_v3_pocket_index(p, 1, 0) == -1);
    missing = 0;
    p->items[14] = 0x3000;
    assert(af_v3_pocket_count(p, 1, 0) == 0);
    assert(af_v3_pocket_index(p, 1, 4) == -1);
    assert(af_v3_pocket_count(p, 1, 0xFFFFFFFFu) == 0);
    assert(af_v3_pocket_index(0, 1, 0) == -1);
    assert(af_v3_pocket_count(0, 1, 0) == 0);
    for (u32 i = 0; i < 4; ++i) {
        assert(record.before[i] == 0xA5A5A5A5u && record.after[i] == 0xA5A5A5A5u);
        expected_private = i & 1 ? p : 0;
        expected_kind = i * 2;
        expected_condition = 0xFFFFFFFFu;
        assert(af_v3_pocket_index(expected_private, expected_kind, expected_condition) == 71);
        assert(af_v3_pocket_count(expected_private, expected_kind, expected_condition) == 72);
    }
    assert(calls == 8);
    puts("All pocket slots, rotations, conditions, guards, and original fallbacks pass");
}
