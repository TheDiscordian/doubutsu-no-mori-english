#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/room.c"

static int disabled;
int af_v3_furniture_import_profile(u32 index) {
    return !disabled && (index == 1161 || index == 1198);
}

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
    puts("Selected rotations, disabled profiles, and original room arithmetic pass");
    return 0;
}
