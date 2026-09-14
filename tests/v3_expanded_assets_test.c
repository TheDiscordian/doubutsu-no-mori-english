#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_OBJECT_CAPACITY 448
#include "../overlays/v3/asset.c"

struct Object af_v3_objects[AF_V3_OBJECT_CAPACITY];
volatile u32 af_v3_object_entry[2];
void af_v3_writeback(void *at, u32 size) { (void)at; (void)size; }
void af_v3_invalidate(void *at, u32 size) { (void)at; (void)size; }

int main(void) {
    struct Status status;
    struct Arena arena;
    for (int bank = 410; bank < AF_V3_OBJECT_CAPACITY; ++bank) {
        memset(&status, 0xA5, sizeof(status));
        memset(&arena, 0, sizeof(arena));
        arena.next = 0x80200000; arena.end = 0x80204000;
        af_v3_objects[bank].start = 0x02212000;
        af_v3_objects[bank].end = 0x02214780;
        assert(af_v3_object_status(&status, &arena, 0x12340000u+bank));
        assert(status.id == -bank && status.size == 10112 && status.vrom == 0x02212000);
        assert(status.vram == 0x80200000 && status.segment == 0 && status.pending == 1);
        assert(arena.next == 0x80202780 && status.keep == 0);
    }
    const u32 invalid[] = {448, 449, 65535, 0x1234FFFF, 0x123401C0};
    for (unsigned i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i) {
        struct Status saved = status;
        struct Arena previous = arena;
        assert(!af_v3_object_status(&status, &arena, invalid[i]));
        assert(!memcmp(&status, &saved, sizeof(status)));
        assert(!memcmp(&arena, &previous, sizeof(arena)));
    }
    arena.next = 0x80200000; arena.end = 0x80202780;
    assert(!af_v3_object_status(&status, &arena, 431));
    arena.end += 16;
    assert(af_v3_object_status(&status, &arena, 431));
    af_v3_objects[447].end = af_v3_objects[447].start;
    assert(!af_v3_object_status(&status, &arena, 447));
    af_v3_objects[447].end--;
    assert(!af_v3_object_status(&status, &arena, 447));
    puts("expanded object bounds, signed arguments, and status ownership pass");
    return 0;
}
