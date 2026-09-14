#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/melody.c"

struct Melody af_v3_melodies[43];
volatile u16 af_v3_melody_current[16];
u32 af_v3_melody_sizes[256], af_v3_melody_offsets[256];
static _Alignas(16) u8 buffer[0x4C50], headers[3312], sample[256];
u8 *af_v3_sequence = buffer + 16;
const u8 *af_v3_seq_header = headers;
static int ports[16][8], events, copies, ram_reads, invalidate_during_wait;
static u32 active_track, copied_source, copied_size;
static int copied_medium;

void af_v3_send8(u32 command, int value) {
    u32 track = (command >> 8) & 255u, index = command & 255u;
    assert((command >> 24) == 6 && track == active_track && index < 8);
    if (events == 0) assert(index == 0 && value == 1);
    else if (events == 1) assert(index == 4 && value == 0);
    else if (events == 6) assert(index == 2);
    else if (events == 7) assert(index == 0 && value == 0);
    else assert(0);
    ports[track][index] = value;
    ++events;
}
void af_v3_send32(u32 command, u32 value) {
    assert(events == 5 && command == (0x10000000u | active_track << 8) && value == 0x80123450);
    ++events;
}
void af_v3_flush(void) { assert(events++ == 2); }
void af_v3_wait_audio(void) {
    assert(events++ == 3);
    if (invalidate_during_wait) af_v3_sequence[0] = 0;
}
void af_v3_fastcopy(u32 source, void *dest, u32 size, int medium) {
    assert(events++ == 4 && size == sizeof(sample) && medium == 2);
    assert(dest == af_v3_sequence + 0x3A10 + (active_track == 6 ? 0 : active_track == 7 ? 0x600 : 0xC00));
    copied_source = source; copied_size = size; copied_medium = medium; ++copies;
    memcpy(dest, sample, size);
}
const u8 *af_v3_imported_data(u32 source) {
    assert(events++ == 4 && (source == 0x80463000 || source == 0x80463100));
    copied_source = source; copied_size = sizeof(sample); copied_medium = -1;
    ++ram_reads;
    return sample;
}
int af_v3_port(int group, int track, int index) {
    assert(group == 0 && track < 16 && index < 8);
    return ports[track][index];
}
static void reset(void) {
    memset(buffer, 0xA5, sizeof(buffer));
    memcpy(af_v3_sequence, "\xFB\x00\x06\x00\x3A\x10", 6);
    memset(headers, 0, sizeof(headers));
    struct AudioEntry *entry = (struct AudioEntry *)(headers + 16 + 205 * 16);
    entry->source = 0xCC000; entry->size = 0x18D10; entry->medium = 2;
    for (u32 i = 0; i < 256; ++i) {
        af_v3_melody_sizes[i] = 256; af_v3_melody_offsets[i] = i * 256;
    }
    memset(sample, 0xCC, sizeof(sample));
    for (u32 i = 0; i < 19; ++i) { sample[4 + 2 * i] = 0; sample[5 + 2 * i] = 42 + 10 * i; }
    memset(af_v3_melodies, 0, sizeof(af_v3_melodies));
    af_v3_melodies[29] = (struct Melody){0x80463000, 256};
    af_v3_melodies[30] = (struct Melody){0x80463100, 256};
    for (u32 i = 0; i < 16; ++i) af_v3_melody_current[i] = 65535;
    memset(ports, 0, sizeof(ports)); events = copies = ram_reads = invalidate_during_wait = 0;
}
static void check(u32 voice, u32 track) {
    u8 before[sizeof(buffer)]; memcpy(before, buffer, sizeof(buffer));
    events = 0; active_track = track;
    assert(af_v3_melody_start(voice | 0x12340000u, track, 0x80123450));
    assert(events == 8 && copied_size == 256 && copied_medium == (voice < 256 ? 2 : -1));
    assert(copied_source == (voice < 256 ? 0xCC000u + voice * 256 : af_v3_melodies[voice - 256].source));
    assert(af_v3_melody_current[track] == voice && ports[track][4] == 0);
    u32 relative = 0x3A10 + (track == 6 ? 0 : track == 7 ? 0x600 : 0xC00);
    memcpy(before + 16 + relative, sample, sizeof(sample));
    for (u32 i = 0; i < 19; ++i) {
        u32 value = relative + 42 + 10 * i;
        before[16 + relative + 4 + 2 * i] = value >> 8;
        before[16 + relative + 5 + 2 * i] = value;
    }
    assert(!memcmp(before, buffer, sizeof(buffer)));
}
int main(void) {
    reset(); check(0, 6); check(255, 7); check(29, 15); check(285, 15);
    ports[15][4] = 7;
    assert(af_v3_melody_count(285) == 6 && af_v3_melody_count(29) == -1);
    check(286, 6); check(286, 15); check(29, 15);
    ports[15][4] = 4;
    assert(af_v3_melody_count(29) == 3 && af_v3_melody_count(285) == -1);
    assert(copies == 4 && ram_reads == 3);
    const u32 invalid[] = {256, 284, 287, 299, 65535};
    reset(); active_track = 15;
    for (u32 i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i)
        assert(!af_v3_melody_start(invalid[i], 15, 0x80123450) && !events);
    assert(!af_v3_melody_start(285, 8, 0x80123450) && !events);
    assert(!af_v3_melody_start(285, 15, 0) && !events);
    af_v3_melodies[29].source = 0x80463FE0;
    assert(!af_v3_melody_start(285, 15, 0x80123450) && !events);
    reset(); active_track = 15; af_v3_melodies[29].size = 0x601;
    assert(!af_v3_melody_start(285, 15, 0x80123450) && !events);
    reset(); active_track = 15; af_v3_sequence[0] = 0;
    assert(!af_v3_melody_start(285, 15, 0x80123450) && !events);
    reset(); active_track = 15; invalidate_during_wait = 1;
    assert(!af_v3_melody_start(285, 15, 0x80123450) && !copies && !ram_reads && events == 4);
    puts("V3 melody synchronization, native/imported sources, relocation, full IDs, and guards pass");
    return 0;
}
