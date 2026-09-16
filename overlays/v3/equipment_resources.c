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

#ifdef AF_V3_EQUIPMENT_KINDS
typedef signed short s16;
#ifdef __mips__
#define kind_header ((const u32 *)0x804A3B00u)
#else
extern u32 af_equipment_kind_header[241];
#define kind_header af_equipment_kind_header
#endif

/* Native owner getters retain their original tables; only extended kinds
   reach this reader. No item selector or gameplay action is enabled here. */
int af_v3_equipment_kind_field(int kind,unsigned int field) {
    static const s16 missing[6]={-1,0,-1,-1,33,34};
    unsigned int slot=(unsigned int)kind-36u;
    if(field>=6u)return -1;
    if(slot>=79u || kind_header[0]!=0x41464B44u || kind_header[1]!=1u
            || kind_header[2]!=79u || kind_header[3]!=12u)return missing[field];
    const s16 *rows=(const s16 *)(kind_header+4);
    return rows[slot*6u+field];
}
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

#ifdef AF_V3_PLAYER_MOTION
#ifdef __mips__
#define player_bounds ((const u32 *)0x8010BD20u)
#define player_header ((const u32 *)0x804A4340u)
#define fan_mask ((const u8 *)0x804A4FD0u)
extern void af_v3_native_player_part(u8 *, int);
#else
extern u32 af_player_native_bounds[131], af_player_header[644];
extern u8 af_player_fan_mask[27];
extern void af_v3_native_player_part(u8 *, int);
#define player_bounds af_player_native_bounds
#define player_header af_player_header
#define fan_mask af_player_fan_mask
#endif

static const Resource *player_imported(int index) {
    u32 slot=(u32)index-130u;
    if (slot>=157u || player_header[0]!=0x4146504Du || player_header[1]!=1u
            || player_header[2]!=157u || player_header[3]!=16u) return 0;
    const Resource *row=(const Resource *)(player_header+4)+slot;
    if (row->vrom<0x02200000u || row->vrom>=0x025F0000u || (row->vrom&15u)
            || row->bytes<32u || row->bytes>3848u || (row->bytes&15u)
            || row->bytes>0x025F0000u-row->vrom || row->type>4u
            || row->pointer<0x06000000u || (row->pointer&3u)
            || row->pointer-0x06000000u>row->bytes-20u) return 0;
    return row;
}

u32 af_v3_player_animation_size(int index) {
    if ((u32)index<130u) {
        u32 begin=player_bounds[index],end=player_bounds[index+1];
        return begin && end ? end-begin-8u : 0;
    }
    const Resource *row=player_imported(index);
    return row ? row->bytes : 0;
}

u32 af_v3_player_animation_origin(int index) {
    return (u32)index<130u ? player_bounds[index]-0x06000000u+8u : 0;
}

u32 af_v3_player_animation_vrom(int index) {
    if ((u32)index<130u) return 0x00B36000u+af_v3_player_animation_origin(index);
    const Resource *row=player_imported(index);
    return row ? row->vrom : 0x00B36000u;
}

/* The relocated player owner retains its native pointer/part tables. Only
   its out-of-native-range path delegates to these two additional readers. */
u32 af_v3_player_animation_pointer(int index) {
    const Resource *row=player_imported(index);
    return row ? row->pointer : 0;
}

int af_v3_player_animation_part(int index) {
    const Resource *row=player_imported(index);
    return row ? (int)row->type : -1;
}

void af_v3_player_part_copy(u8 *destination,int index) {
    if ((u32)index<4u) af_v3_native_player_part(destination,index);
    else if (index==4 && player_header[0]==0x4146504Du && player_header[1]==1u)
        for (unsigned int i=0;i<27u;++i) destination[i]=fan_mask[i];
}
#endif
