#ifndef AF_V3_PAK_CODEC_H
#define AF_V3_PAK_CODEC_H

/* Lossless note framing for the existing passport and village-backup paths.
 * No device I/O or live-state changes occur here. The caller must validate the
 * decoded native structure, selected imports, and individual record semantics
 * before committing any player data. CRCs detect damage, not malicious edits. */
enum {
    AF_PAK_HEADER=96, AF_PAK_PAGE=256, AF_PAK_MAX_NOTE=0x7B00,
    AF_PAK_PASSPORT=0, AF_PAK_BACKUP=1,
    AF_PAK_PRIVATE_NOTE=0x1200, AF_PAK_BACKUP_NOTE=0x6700,
    AF_PAK_MAX_RECORDS=0x4000,
    AF_PAK_HASH_WORDS=4096, AF_PAK_HASH_BYTES=AF_PAK_HASH_WORDS*4,
    AF_PAK_ARGUMENT=-1, AF_PAK_FORMAT=-2, AF_PAK_CRC=-3,
    AF_PAK_CAPACITY=-4, AF_PAK_STREAM=-5, AF_PAK_BINDING=-6
};
typedef unsigned char af_pak_u8;
typedef unsigned int af_pak_u32;
typedef struct {
    const af_pak_u8 *native,*records;
    af_pak_u32 kind,native_bytes,record_bytes;
    /* Binding identifies the runtime record interpretation/behaviour contract,
     * not a local filename. Selected-import requirements belong in records. */
    af_pak_u8 binding[32],identity[16];
} AFPakInput;
typedef struct {
    const af_pak_u8 *native,*records;
    af_pak_u32 kind,native_bytes,record_bytes;
    af_pak_u8 identity[16];
} AFPakView;

/* Returns page-aligned note bytes or a negative error. Encode measures first
 * and leaves the entire output untouched on failure. The caller-owned aligned
 * hash workspace may change. All mutable and source buffers must be disjoint;
 * sources must stay immutable through both passes. */
int af_v3_pak_measure(const AFPakInput *,af_pak_u32 capacity,
    af_pak_u32 *hash,af_pak_u32 hash_bytes);
int af_v3_pak_encode(af_pak_u8 *note,af_pak_u32 capacity,const AFPakInput *,
    af_pak_u32 *hash,af_pak_u32 hash_bytes);
/* View is published only after full framing/binding/CRC validation. Raw scratch
 * may change on an invalid token stream, but note and view are never changed on
 * error. identity may be null for a read-only note probe. No legacy note is
 * accepted as this format; the native adapter handles legacy notes explicitly. */
int af_v3_pak_decode(const af_pak_u8 *note,af_pak_u32 note_bytes,
    const af_pak_u8 binding[32],const af_pak_u8 identity[16],
    af_pak_u8 *raw,af_pak_u32 raw_bytes,AFPakView *view);
#endif
