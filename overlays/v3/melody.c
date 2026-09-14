/* Full-ID melody loading; retain native audio command synchronization. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed char s8;
typedef signed short s16;
#ifndef AF_V3_MELODY_BEGIN
#define AF_V3_MELODY_BEGIN 0x80463000u
#define AF_V3_MELODY_END 0x80463FF0u
#endif
struct Melody { u32 source, size; };
struct AudioEntry { u32 source, size; u8 medium, cache; u16 params[3]; };
_Static_assert(sizeof(struct AudioEntry) == 16, "Native audio header entry");
#ifdef __mips__
#define extra ((const struct Melody *)0x80462900u)
#define current ((volatile u16 *)0x80462B00u)
#define sizes ((const u32 *)0x80119240u)
#define offsets ((const u32 *)0x80119640u)
#define sequence (*(u8 * volatile *)0x8014CBA8u)
#define seq_header (*(const u8 * volatile *)0x8014BD30u)
#define send8 ((void (*)(u32, int))0x800EEE44u)
#define send32 ((void (*)(u32, u32))0x800EEE20u)
#define flush ((void (*)(void))0x800EEEA4u)
#define wait_audio ((void (*)(void))0x800EF940u)
#define fastcopy ((void (*)(u32, void *, u32, int))0x800EB978u)
#define imported_data(address) ((const u8 *)(address))
#define port ((int (*)(int, int, int))0x800EF3C0u)
#else
extern struct Melody af_v3_melodies[43];
extern volatile u16 af_v3_melody_current[16];
extern u32 af_v3_melody_sizes[256], af_v3_melody_offsets[256];
extern u8 *af_v3_sequence;
extern const u8 *af_v3_seq_header;
extern void af_v3_send8(u32, int), af_v3_send32(u32, u32), af_v3_flush(void), af_v3_wait_audio(void);
extern void af_v3_fastcopy(u32, void *, u32, int);
extern const u8 *af_v3_imported_data(u32);
extern int af_v3_port(int, int, int);
#define extra af_v3_melodies
#define current af_v3_melody_current
#define sizes af_v3_melody_sizes
#define offsets af_v3_melody_offsets
#define sequence af_v3_sequence
#define seq_header af_v3_seq_header
#define send8 af_v3_send8
#define send32 af_v3_send32
#define flush af_v3_flush
#define wait_audio af_v3_wait_audio
#define fastcopy af_v3_fastcopy
#define imported_data af_v3_imported_data
#define port af_v3_port
#endif

static int source_for(u32 voice, struct Melody *result) {
    const struct AudioEntry *entry;
    const u8 *header;
    u32 offset;
    if (voice >= 299) return 0;
    if (voice >= 256) {
        *result = extra[voice - 256];
        if (!result->size || result->size > 0x600u || result->size % 16u
                || result->source < AF_V3_MELODY_BEGIN || result->source > AF_V3_MELODY_END - result->size) return 0;
    } else {
        header = seq_header;
        if (!header) return 0;
#ifdef __mips__
        if ((u32)header < 0x80000400u || (u32)header > 0x80400000u - 3312u || (u32)header % 4u) return 0;
#endif
        entry = (const struct AudioEntry *)(header + 16u + 205u * 16u);
        result->size = sizes[voice];
        offset = offsets[voice];
        if (!result->size || result->size > 0x600u || result->size % 16u
                || entry->medium != 2 || entry->size != 0x18D10u
                || offset > entry->size - result->size
                || entry->source > 0x04000000u - entry->size) return 0;
        result->source = entry->source + offset;
    }
    return 1;
}

static int valid_sequence(const u8 *data) {
    if (!data) return 0;
#ifdef __mips__
    if ((u32)data < 0x80000400u || (u32)data > 0x80400000u - 0x4C30u || (u32)data % 16u) return 0;
#endif
    /* Main control sequence 199 owns three 0x600-byte melody areas. */
    return data[0] == 0xFB && data[1] == 0 && data[2] == 6 && data[3] == 0
        && data[4] == 0x3A && data[5] == 0x10;
}

int af_v3_melody_start(u32 voice_argument, u32 track_argument, u32 notes) {
    u32 voice = (u16)voice_argument, track = (u16)track_argument;
    u32 command, relative;
    u8 *data, *destination;
    struct Melody source;
    if ((track != 6 && track != 7 && track != 15) || !notes || !source_for(voice, &source)
            || !valid_sequence(sequence)) return 0;
    command = 0x06000000u | (track << 8);
    send8(command, 1); /* Stop before replacing a sequence that audio may be reading. */
    send8(command | 4u, 0); /* Do not report a stale note count under an aliased low-byte ID. */
    flush();
    wait_audio();
    data = sequence;
    if (!valid_sequence(data)) return 0;
    relative = 0x3A10u + (track == 6 ? 0 : track == 7 ? 0x600u : 0xC00u);
    destination = data + relative;
    if (voice < 256) {
        fastcopy(source.source, destination, source.size, 2);
    } else {
        /* Native FastCopy only supports PI media; medium zero never queues a
         * completion and would hang its blocking receive. These checked assets
         * are already resident and the sequence interpreter reads them on CPU. */
        const u8 *input = imported_data(source.source);
        for (u32 i = 0; i < source.size; ++i) destination[i] = input[i];
    }
    for (u32 i = 0; i < 19; ++i) {
        u8 *pointer = destination + 4u + 2u * i;
        u32 relocated = (u32)pointer[0] * 256u + pointer[1] + relative;
        pointer[0] = (u8)(relocated >> 8);
        pointer[1] = (u8)relocated;
    }
    current[track] = voice;
    send32(0x10000000u | (track << 8), notes);
    send8(command | 2u, (s8)voice);
    send8(command, 0);
    return 1;
}

int af_v3_melody_count(u32 argument) {
    u32 voice = (u16)argument;
    u32 track = voice == 0 ? 6 : voice == 255 ? 7 : 15;
    if (voice >= 299 || current[track] != voice || ((u32)port(0, track, 2) & 255u) != (voice & 255u)) return -1;
    return (s8)(port(0, track, 4) - 1);
}
