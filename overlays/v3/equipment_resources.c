/* Shared held-resource readers. Item selection and actions are separate. */
typedef unsigned int u32;
typedef unsigned char u8;
typedef struct { u32 vrom, bytes, pointer, type; } Resource;
#ifdef __mips__
#define native_pointers ((const u32 *)0x8010BF30u)
#define native_types ((const u8 *)0x8010BF74u)
#define native_bounds ((const u32 *)0x8010BF88u)
#define header ((const u32 *)0x804A4000u)
#else
extern u32 af_equipment_native_pointers[17], af_equipment_native_bounds[18];
extern u8 af_equipment_native_types[17];
extern u32 af_equipment_header[2048];
#define native_pointers af_equipment_native_pointers
#define native_types af_equipment_native_types
#define native_bounds af_equipment_native_bounds
#define header af_equipment_header
#endif

static const Resource *imported(int index) {
    u32 slot = (u32)index-17u;
    if (slot >= 50u || header[0] != 0x41464852u || header[1] != 1u
            || header[2] != 50u || header[3] != 16u) return 0;
    const Resource *row = (const Resource *)(header+4)+slot;
    if (row->vrom < 0x02200000u || row->vrom >= 0x025F0000u
            || (row->vrom & 15u) || !row->bytes || (row->bytes & 15u)
            || row->bytes > 4376u || row->bytes > 0x025F0000u-row->vrom
            || row->type > 5u || row->type == 1u
            || row->bytes < (row->type ? 20u : 8u)
            || row->pointer < 0x06000000u || (row->pointer & 3u)
            || row->pointer-0x06000000u > row->bytes-(row->type ? 20u : 8u)) return 0;
    return row;
}

u32 af_v3_equipment_pointer(int index) {
    if ((u32)index < 17u) return native_pointers[index];
    const Resource *row = imported(index);
    return row ? row->pointer : 0;
}

u32 af_v3_equipment_type(int index) {
    if ((u32)index < 17u) return native_types[index];
    const Resource *row = imported(index);
    return row ? row->type : 0;
}

u32 af_v3_equipment_size(int index) {
    if ((u32)index < 17u) {
        u32 begin = native_bounds[index], end = native_bounds[index+1];
        return begin && end ? end-begin-8u : 0;
    }
    const Resource *row = imported(index);
    return row ? row->bytes : 0;
}

u32 af_v3_equipment_origin(int index) {
    return (u32)index < 17u ? native_bounds[index]-0x06000000u+8u : 0;
}

u32 af_v3_equipment_vrom(int index) {
    if ((u32)index < 17u) return 0x00B8B000u+af_v3_equipment_origin(index);
    const Resource *row = imported(index);
    /* Preserve the native invalid-index result; its transfer length is zero. */
    return row ? row->vrom : 0x00B8B000u;
}
