#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/campsite_scene.c"
u8 af_campsite_packet[0x1000], af_campsite_scene_table[35 * 20];
static _Alignas(16) u8 block[0x614], field[0x168];
u8 *af_campsite_test_block = block;
static int originals, backgrounds, foregrounds;
int af_campsite_native_block_info(void *p, const void *c) {
    assert(p == field && c); ++originals; return 73;
}
void af_campsite_native_set_bg(void *p, const void *d, u16 height, u8 type, u16 id, int x, int z) {
    assert(p == block && d == packet + 0x40 && height == 0 && type == 255 && id == 0xF3 && !x && !z);
    ++backgrounds;
}
void af_campsite_native_set_fg(void *p, const void *d, u16 id) {
    assert(p == block + 0x580 && d == packet + 0x480 && id == 0x199 && backgrounds == foregrounds + 1);
    ++foregrounds;
}
int main(int argc, char **argv) {
    assert(argc == 2);
    FILE *input = fopen(argv[1], "rb"); assert(input);
    assert(fread(af_campsite_packet, 1, sizeof af_campsite_packet, input) == sizeof af_campsite_packet);
    assert(fgetc(input) == EOF); fclose(input);
    for (int i = 0; i < 35; ++i) assert(af_v3_campsite_scene_status(i) == af_campsite_scene_table + i * 20);
    assert(af_v3_campsite_scene_status(35) == af_campsite_packet + 0x20);
    assert(!af_v3_campsite_scene_status(-1) && !af_v3_campsite_scene_status(36));
    for (int i = -1; i <= 36; ++i) {
        int expected = i == 20 ? 1 : i == 6 || i == 9 || i == 12 || i == 14 || i == 18 || i == 21 || i == 31 || i == 35 ? 2
            : i == 17 || i == 22 || i == 23 || i == 24 || i == 25 || i == 29 ? 3 : 0;
        assert(af_v3_campsite_room_sound(i) == expected);
    }
    const u8 combination[2] = {5, 0xBC};
    assert(af_v3_campsite_block_info(field, combination) == 73 && originals == 1);
    field[0] = 0x30; field[1] = 0x12; field[0x166] = field[0x167] = 1;
    assert(!af_v3_campsite_block_info(field, combination) && backgrounds == 1 && foregrounds == 1);
    for (int i = 0; i < 16; ++i) {
        af_campsite_packet[i] ^= 1;
        assert(!af_v3_campsite_scene_status(35));
        assert(af_v3_campsite_block_info(field, combination) == -1);
        af_campsite_packet[i] ^= 1;
    }
    assert(af_v3_campsite_block_info(field, 0) == -1);
    field[0x166] = 2; assert(af_v3_campsite_block_info(field, combination) == -1); field[0x166] = 1;
    field[0x167] = 0; assert(af_v3_campsite_block_info(field, combination) == -1); field[0x167] = 1;
    af_campsite_test_block = 0; assert(af_v3_campsite_block_info(field, combination) == -1);
    assert(backgrounds == 1 && foregrounds == 1 && originals == 1);
    puts("campsite additive identities, full acoustics mapping, native adapters, and rejection pass");
}
