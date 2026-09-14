#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/room.c"

static int disabled;
int af_v3_furniture_import_profile(u32 index) {
    return !disabled && (index == 1161 || index == 1198);
}
#ifdef AF_V3_CLOTHING_PROFILE
int af_v3_item_type(u32 item) { return !disabled && item == 0x34BF ? 12 : 0; }
#endif

int main(void) {
    const u32 items[] = {0x3224, 0x32B8};
    const u32 indices[] = {1161, 1198};
    for (u32 i = 0; i < 2; ++i) {
        for (u32 rotation = 0; rotation < 4; ++rotation) {
            u32 item = items[i] | rotation;
            assert(af_v3_room_value(item, 0) == 1);
            assert(af_v3_room_value(item, 1) == indices[i] * 4 + rotation);
            assert(af_v3_room_value(item, 2) == 1);
            disabled = 1;
            assert(af_v3_room_value(item, 0) == 0);
            assert(af_v3_room_value(item, 1) == item - 0x1000);
            assert(af_v3_room_value(item, 2) == 3);
            disabled = 0;
        }
    }
    const u32 ordinary[] = {0, 0xFFF, 0x1000, 0x1ECC, 0x1ECD, 0x1F27,
                            0x2000, 0x3000, 0xFFFF, 0x13224, 0xFFFFFFFF};
    for (u32 i = 0; i < sizeof(ordinary) / sizeof(*ordinary); ++i) {
        u32 value = ordinary[i];
        assert(af_v3_room_value(value, 0) == ((int)value < 0x1ECD));
        assert(af_v3_room_value(value, 1) == value - 0x1000u);
        assert(af_v3_room_value(value, 2) == ((value >> 12) & 15));
    }
#ifdef AF_V3_CLOTHING_PROFILE
    assert(af_v3_room_value(0x34BF, 0) == 0);
    assert(af_v3_room_value(0x34BF, 1) == 0x24BF);
    assert(af_v3_room_value(0x34BF, 2) == 2);
    assert(af_v3_room_value(0x34BF, 3) == 0x10BF);
    assert(af_v3_room_value(0x2400, 3) == 0);
    assert(af_v3_room_value(0x24BF, 3) == 0xBF);
    assert(af_v3_room_value(0x24FF, 3) == 0xFF);
    assert(af_v3_room_value(0x23FF, 3) == 0);
    assert(af_v3_room_value(0x2500, 3) == 0);
    assert(af_v3_room_value(0x34BC, 3) == 0);
    assert(af_v3_room_value(0x134BF, 3) == 0);
    assert(af_v3_room_value(0xFFFFFFFF, 3) == 0);
    for (u32 item = 0x34BC; item < 0x34BF; ++item)
        assert(af_v3_room_value(item, 2) == 3);
    assert(af_v3_room_value(0x134BF, 2) == 3);
    disabled = 1;
    assert(af_v3_room_value(0x34BF, 2) == 3);
    assert(af_v3_room_value(0x34BF, 3) == 0);
#endif
    puts("Selected rotations, disabled profiles, and original room arithmetic pass");
    return 0;
}
