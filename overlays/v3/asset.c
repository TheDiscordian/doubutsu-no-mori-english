/* Additive object-bank loading. Native object arena ownership is retained. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed short s16;
#ifndef AF_V3_OBJECT_CAPACITY
#define AF_V3_OBJECT_CAPACITY 430
#endif
struct Object { u32 start, end; };
struct Status {
    s16 id; u16 pad;
    u32 segment, vram, vrom, size;
    u8 reserved[60];
    u16 keep;
    u8 unknown, pending;
};
struct Arena { u8 reserved[0x1800]; u32 next, end; };
_Static_assert(__builtin_offsetof(struct Status, keep) == 0x50, "Native status layout");
_Static_assert(__builtin_offsetof(struct Arena, next) == 0x1800, "Native arena layout");

#ifdef __mips__
#define objects ((const struct Object *)0x80461000u)
#define entry ((volatile u32 *)0x800C5AA0u)
#define writeback ((void (*)(void *, u32))0x8002FE00u)
#define invalidate ((void (*)(void *, u32))0x80034CE0u)
#else
extern struct Object af_v3_objects[AF_V3_OBJECT_CAPACITY];
extern volatile u32 af_v3_object_entry[2];
extern void af_v3_writeback(void *, u32), af_v3_invalidate(void *, u32);
#define objects af_v3_objects
#define entry af_v3_object_entry
#define writeback af_v3_writeback
#define invalidate af_v3_invalidate
#endif

int af_v3_object_status(struct Status *status, struct Arena *arena, u32 bank_argument) {
    int bank = (s16)bank_argument;
    u32 start, end, size, next;
    if (bank < 0 || bank >= AF_V3_OBJECT_CAPACITY) return 0;
    start = objects[bank].start;
    end = objects[bank].end;
    if (end < start || (bank >= 410 && (!start || end == start))) return 0;
    size = end - start;
    if (size > 0xFFFFFFFFu - arena->next - 15u || arena->next > 0xFFFFFFF0u) return 0;
    next = (arena->next + size + 15u) & ~15u;
    if (next >= arena->end) return 0;
    status->id = -bank;
    status->segment = 0;
    status->vram = arena->next;
    status->vrom = start;
    status->size = size;
    status->keep = 0;
    status->pending = 1;
    arena->next = next;
    return 1;
}

int af_v3_asset_init(void) {
    u32 jump;
#ifdef __mips__
    jump = 0x08000000u | (((u32)af_v3_object_status >> 2) & 0x03FFFFFFu);
#else
    jump = 0x08118050u; /* Host fixture; actual linked target is checked separately. */
#endif
    if (entry[0] == jump && entry[1] == 0) return 1;
    if (entry[0] != 0xAFA60008u || entry[1] != 0x00063400u) return 0;
    entry[0] = jump;
    entry[1] = 0;
    writeback((void *)entry, 8);
    invalidate((void *)entry, 8);
    return 1;
}
